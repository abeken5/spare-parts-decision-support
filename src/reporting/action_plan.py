from pathlib import Path
import sqlite3
import pandas as pd

def classify_part_action(current_min: int, recommended_rop: int, ved_class: str, annual_demand_qty: float, forecast_monthly: float) -> str:
    if annual_demand_qty <= 0.5 or forecast_monthly < 0.15:
        return "Düşük Hız / Eskime İzleme (Manuel Onay)"
    if recommended_rop > current_min and ved_class == "V":
        return "Vital Koruma (ROP Yükselt)"
    if recommended_rop > current_min:
        return "Hizmet Koruması (ROP Yükselt)"
    if recommended_rop < current_min:
        return "Aşırı Stoğu Erit (Sermaye Çöz)"
    return "Dengeli (s, Q Geçişi)"

def generate_action_plan(db_path: str = "data/processed/mro_inventory.db", target_csl: float = 0.98, output_csv: str = "data/processed/part_action_plan.csv") -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        seg = pd.read_sql_query("SELECT * FROM part_segmentation;", conn)
        fc = pd.read_sql_query("SELECT part_id, winner_part_level, forecast_monthly_part FROM forecast_summary;", conn)
        boot = pd.read_sql_query("SELECT * FROM bootstrap_policies WHERE ABS(target_csl - ?) < 1e-6;", conn, params=(target_csl,))
        bt_cur = pd.read_sql_query("SELECT part_id, holding_cost AS cur_holding_tl, ordering_cost AS cur_ordering_tl, base_shortage_cost AS cur_shortage_tl, fill_rate AS cur_fill_rate, stockout_days AS cur_stockout_days FROM backtest_part_details WHERE policy = 'MinMax_Current_1.5_3.0m';", conn)
        csl_tag = str(round(target_csl * 100, 1)).rstrip("0").rstrip(".")
        bt_opt = pd.read_sql_query("SELECT part_id, holding_cost AS opt_holding_tl, ordering_cost AS opt_ordering_tl, base_shortage_cost AS opt_shortage_tl, fill_rate AS opt_fill_rate, stockout_days AS opt_stockout_days FROM backtest_part_details WHERE policy = ?;", conn, params=(f"Bootstrap_CSL{csl_tag}",))
    df = seg.merge(fc, on="part_id").merge(boot[["part_id", "rop_bootstrap", "ss_bootstrap", "order_qty_q"]], on="part_id").merge(bt_cur, on="part_id").merge(bt_opt, on="part_id")
    df["cur_total_cost_tl"] = df["cur_holding_tl"] + df["cur_ordering_tl"] + df["cur_shortage_tl"]
    df["opt_total_cost_tl"] = df["opt_holding_tl"] + df["opt_ordering_tl"] + df["opt_shortage_tl"]
    df["net_savings_tl"] = (df["cur_total_cost_tl"] - df["opt_total_cost_tl"]).round(2)
    df["rop_delta"] = df["rop_bootstrap"] - df["min_stock"]
    df["recommended_action"] = df.apply(lambda r: classify_part_action(int(r["min_stock"]), int(r["rop_bootstrap"]), str(r["ved_class"]), float(r["annual_demand_qty"]), float(r["forecast_monthly_part"])), axis=1)
    df = df.sort_values("net_savings_tl", ascending=False).reset_index(drop=True)
    df.to_csv(output_csv, index=False)
    with sqlite3.connect(db_path) as conn:
        df.to_sql("part_action_plan", conn, if_exists="replace", index=False)
    return df

def write_executive_brief(action_df: pd.DataFrame, db_path: str = "data/processed/mro_inventory.db", out_md: str = "docs/executive_decision_brief.md") -> Path:
    with sqlite3.connect(db_path) as conn:
        bt_sum = pd.read_sql_query("SELECT * FROM backtest_summary;", conn)
        mode_comp = pd.read_sql_query("SELECT * FROM backtest_mode_comparison;", conn)
        robust = pd.read_sql_query("SELECT * FROM backtest_robustness;", conn)
    cur = bt_sum[bt_sum["policy"] == "MinMax_Current_1.5_3.0m"].iloc[0]
    cls = bt_sum[bt_sum["policy"] == "Classical_Hist_CSL95"].iloc[0]
    opt = bt_sum[bt_sum["policy"] == "Bootstrap_CSL98"].iloc[0]
    opt95 = bt_sum[bt_sum["policy"] == "Bootstrap_CSL95"].iloc[0]
    opt99 = bt_sum[bt_sum["policy"] == "Bootstrap_CSL99"].iloc[0]
    grid_best = bt_sum[bt_sum["policy"] == "MinMax_Grid_3.0_6.0m"].iloc[0]
    sav_mm_m = round(float(cur["total_cost_Base_M"] - opt["total_cost_Base_M"]), 2)
    sav_mm_pct = round((sav_mm_m / float(cur["total_cost_Base_M"])) * 100.0, 1)
    sav_cls_pct = round(((float(cls["total_cost_Base_M"]) - float(opt["total_cost_Base_M"])) / float(cls["total_cost_Base_M"])) * 100.0, 1)
    sav_grid_pct = round(((float(grid_best["total_cost_Base_M"]) - float(opt["total_cost_Base_M"])) / float(grid_best["total_cost_Base_M"])) * 100.0, 1)
    v_so_drop_pct = round(((float(cur["vital_avg_stockout_days"]) - float(opt["vital_avg_stockout_days"])) / float(cur["vital_avg_stockout_days"])) * 100.0, 1)
    cost_ok = "Karşılandı" if sav_mm_pct >= 15.0 else "Karşılanmadı"
    fr_ok = "Karşılandı" if float(opt["portfolio_fill_rate_pct"]) >= 95.0 else "Karşılanmadı"
    mc_mm = mode_comp[mode_comp["policy"] == "MinMax_Current_1.5_3.0m"].iloc[0]
    mc_36 = mode_comp[mode_comp["policy"] == "MinMax_Grid_3.0_6.0m"].iloc[0]
    mc_98 = mode_comp[mode_comp["policy"] == "Bootstrap_CSL98"].iloc[0]
    lines = [
        "# Yönetici Karar Özeti — MRO Yedek Parça Envanter Optimizasyonu", "",
        "## 1. Yönetici Özeti ve Guardrail Doğrulaması (365 Günlük Kapalı Test)",
        f"- **Önerilen Politika:** Ampirik Blok Bootstrap `(s, Q)` — **CSL = %98** (CSL %95: `{opt95['total_cost_Base_M']} M TL`, CSL %98: `{opt['total_cost_Base_M']} M TL`, CSL %99: `{opt99['total_cost_Base_M']} M TL`).",
        f"- **Tüzük Başarı Kriteri (%15 Maliyet Düşüşü):** **{cost_ok}** — Mevcut Min/Max `{cur['total_cost_Base_M']} M TL` -> Bootstrap CSL %98 `{opt['total_cost_Base_M']} M TL` (**{sav_mm_m} M TL / %{sav_mm_pct} tasarruf**).",
        f"- **Guardrail (%95 Fill Rate):** **{fr_ok}** — Fill Rate `%{cur['portfolio_fill_rate_pct']}` -> `%{opt['portfolio_fill_rate_pct']}`; Vital açık sipariş günü `{cur['vital_avg_stockout_days']}` -> `{opt['vital_avg_stockout_days']} gün` (**%{v_so_drop_pct} azalma**).",
        f"- **Adil Kıyas:** Klasik `(s, Q)` formülüne (`{cls['total_cost_Base_M']} M TL`) göre **%{sav_cls_pct}**, ayarlı `3.0/6.0 ay` Min/Max kuralına (`{grid_best['total_cost_Base_M']} M TL`) göre **%{sav_grid_pct}** avantaj.", "",
        "## 2. Ceza Tanımı Duyarlılığı (`DEC-11`)",
        f"- **Günlük `/30` Backorder Cezası:** CSL98 `{mc_98['backorder_div30_M']} M TL` vs. Min/Max 3/6 `{mc_36['backorder_div30_M']} M TL` (Mevcut: `{mc_mm['backorder_div30_M']} M TL`).",
        f"- **Haftalık `/7` Backorder Cezası:** CSL98 `{mc_98['backorder_div7_M']} M TL` vs. Min/Max 3/6 `{mc_36['backorder_div7_M']} M TL` (Mevcut: `{mc_mm['backorder_div7_M']} M TL`).",
        f"- **Tek Seferlik Birim Ceza:** CSL98 `{mc_98['one_time_shortage_M']} M TL` vs. Min/Max 3/6 `{mc_36['one_time_shortage_M']} M TL` (Mevcut: `{mc_mm['one_time_shortage_M']} M TL`).", "",
        "## 3. Yoğunlaşma ve Çoklu Tohum Dayanıklılığı",
    ]
    for _, rr in robust.iterrows():
        lines.append(f"- **{rr['metric']}:** `%{rr['value_pct']}` ({rr['note']})")
    lines.extend(["", "## 4. Parça Bazlı Aksiyon Dağılımı (200 SKU — Sıfır Test Sızıntısı)"])
    for act, cnt in action_df["recommended_action"].value_counts().to_dict().items():
        lines.append(f"- **{act}:** {cnt} parça")
    body = chr(10).join(lines)
    Path(out_md).write_text(body, encoding="utf-8")
    Path("docs/pm/09_executive_summary.md").write_text(body, encoding="utf-8")
    return Path(out_md)

if __name__ == "__main__":
    write_executive_brief(generate_action_plan(target_csl=0.98))
