from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

HOLDING_RATE = 0.22
ORDERING_COST = 1500.0
# Charter Sec. 4 ile birebir uyumlu VED birim ceza katsayilari
BASE_VED_PENALTY = {"V": 1.50, "E": 0.75, "D": 0.25}
PENALTY_SCENARIOS = {"Low_0.5x": 0.5, "Base_1.0x": 1.0, "High_2.0x": 2.0}


def simulate_single_part_policy(
    daily_demand: np.ndarray,
    lead_time_draws: np.ndarray,
    unit_cost: float,
    ved_class: str,
    policy_type: str,
    trigger_level: int,
    order_param: int,
    initial_stock: int | None = None,
    fulfillment_mode: str = "backorder",
    penalty_divisor: float = 30.0,
) -> dict:
    """Simulate 365-day daily inventory under backorder (primary) or lost_sales sensitivity mode."""
    assert fulfillment_mode in ("backorder", "lost_sales"), "Invalid fulfillment_mode"
    n_days = len(daily_demand)

    if initial_stock is not None:
        on_hand = max(0, int(initial_stock))
    elif policy_type == "sS":
        on_hand = max(1, int(np.ceil((trigger_level + order_param) / 2.0)))
    else:
        on_hand = max(1, int(np.ceil(trigger_level + order_param / 2.0)))

    backorder_qty = 0
    pipeline: list[tuple[int, int]] = []
    order_idx = 0
    order_count = 0
    holding_cost = 0.0
    base_shortage_cost = 0.0
    total_demand = 0.0
    immediate_fulfilled = 0.0
    stockout_days = 0
    ending_stock_sum = 0.0

    daily_hold_unit = unit_cost * (HOLDING_RATE / 365.0)
    base_pen_unit = unit_cost * BASE_VED_PENALTY[ved_class]

    for t in range(n_days):
        if pipeline:
            arrived = sum(qty for arr_day, qty in pipeline if arr_day == t)
            if arrived > 0:
                on_hand += arrived
                pipeline = [(arr_day, qty) for arr_day, qty in pipeline if arr_day > t]

        if fulfillment_mode == "backorder" and backorder_qty > 0 and on_hand > 0:
            cleared = min(on_hand, backorder_qty)
            on_hand -= cleared
            backorder_qty -= cleared

        d_t = int(round(float(daily_demand[t])))
        total_demand += d_t
        fulfilled_now = min(on_hand, d_t)
        unmet_today = d_t - fulfilled_now
        immediate_fulfilled += fulfilled_now
        on_hand -= fulfilled_now

        if fulfillment_mode == "backorder":
            backorder_qty += unmet_today
            if backorder_qty > 0:
                stockout_days += 1
                # Gunluk acik siparis (backorder-day) cezasi
                base_shortage_cost += (backorder_qty / penalty_divisor) * base_pen_unit
        else:
            if unmet_today > 0:
                stockout_days += 1
                base_shortage_cost += unmet_today * base_pen_unit

        holding_cost += on_hand * daily_hold_unit
        ending_stock_sum += on_hand

        on_order = sum(qty for _, qty in pipeline)
        inv_pos = on_hand - backorder_qty + on_order

        if inv_pos <= trigger_level:
            qty = max(1, order_param - inv_pos) if policy_type == "sS" else max(1, order_param)
            lt_days = int(lead_time_draws[order_idx % len(lead_time_draws)])
            pipeline.append((t + max(1, lt_days), qty))
            order_count += 1
            order_idx += 1

    ordering_cost = order_count * ORDERING_COST
    fill_rate = (immediate_fulfilled / total_demand) if total_demand > 0 else 1.0

    return {
        "holding_cost": holding_cost,
        "ordering_cost": ordering_cost,
        "base_shortage_cost": base_shortage_cost,
        "total_demand": total_demand,
        "fulfilled_demand": immediate_fulfilled,
        "fill_rate": fill_rate,
        "stockout_days": stockout_days,
        "ending_backorder": backorder_qty,
        "order_count": order_count,
        "avg_on_hand": ending_stock_sum / n_days,
    }


def _build_policy_list(meta: pd.DataFrame, boot_pol: pd.DataFrame) -> list[tuple[str, str, dict[str, tuple[int, int]]]]:
    policies: list[tuple[str, str, dict[str, tuple[int, int]]]] = []
    policies.append((
        "MinMax_Current_1.5_3.0m",
        "sS",
        {r["part_id"]: (int(r["min_stock"]), int(r["max_stock"])) for _, r in meta.iterrows()},
    ))
    for mult, label in [
        (2.0 / 3.0, "MinMax_Grid_1.0_2.0m"),
        (4.0 / 3.0, "MinMax_Grid_2.0_4.0m"),
        (2.0, "MinMax_Grid_3.0_6.0m"),
    ]:
        policies.append((
            label,
            "sS",
            {
                r["part_id"]: (
                    max(1, int(np.ceil(r["min_stock"] * mult))),
                    max(2, int(np.ceil(r["max_stock"] * mult))),
                )
                for _, r in meta.iterrows()
            },
        ))

    policies.append((
        "Classical_Hist_CSL95",
        "sQ",
        {r["part_id"]: (int(r["rop_classical_hist"]), int(r["eoq_classical_hist"])) for _, r in meta.iterrows()},
    ))
    policies.append((
        "Classical_Forecast_CSL95",
        "sQ",
        {r["part_id"]: (int(r["rop_classical_fc"]), int(r["eoq_classical_fc"])) for _, r in meta.iterrows()},
    ))

    for csl in sorted(boot_pol["target_csl"].unique()):
        sub = boot_pol[boot_pol["target_csl"] == csl]
        csl_tag = str(round(csl * 100, 1)).rstrip("0").rstrip(".")
        policies.append((
            f"Bootstrap_CSL{csl_tag}",
            "sQ",
            {r["part_id"]: (int(r["rop_bootstrap"]), int(r["order_qty_q"])) for _, r in sub.iterrows()},
        ))
    return policies


def _evaluate_mode(
    meta: pd.DataFrame,
    policies: list[tuple[str, str, dict[str, tuple[int, int]]]],
    test_demand_map: dict[str, np.ndarray],
    crn_lt_map: dict[str, np.ndarray],
    init_stock_map: dict[str, int],
    fulfillment_mode: str,
    penalty_divisor: float = 30.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    part_records = []
    for pol_name, pol_type, param_map in policies:
        for _, r in meta.iterrows():
            pid = r["part_id"]
            trig, ord_p = param_map[pid]
            res = simulate_single_part_policy(
                daily_demand=test_demand_map[pid],
                lead_time_draws=crn_lt_map[pid],
                unit_cost=float(r["unit_cost"]),
                ved_class=r["ved_class"],
                policy_type=pol_type,
                trigger_level=trig,
                order_param=ord_p,
                initial_stock=init_stock_map[pid],
                fulfillment_mode=fulfillment_mode,
                penalty_divisor=penalty_divisor,
            )
            part_records.append({
                "policy": pol_name,
                "part_id": pid,
                "ved_class": r["ved_class"],
                "sb_class": r["sb_class"],
                **res,
            })

    detail_df = pd.DataFrame(part_records)
    summary_rows = []
    for pol_name, grp in detail_df.groupby("policy", sort=False):
        hold = float(grp["holding_cost"].sum())
        order = float(grp["ordering_cost"].sum())
        base_short = float(grp["base_shortage_cost"].sum())
        tot_dem = float(grp["total_demand"].sum())
        ful_dem = float(grp["fulfilled_demand"].sum())
        v_short_days = float(grp[grp["ved_class"] == "V"]["stockout_days"].mean())
        all_short_days = float(grp["stockout_days"].mean())

        summary_rows.append({
            "policy": pol_name,
            "holding_cost_M": round(hold / 1e6, 2),
            "ordering_cost_M": round(order / 1e6, 2),
            "shortage_base_M": round(base_short / 1e6, 2),
            "total_cost_Low_M": round((hold + order + 0.5 * base_short) / 1e6, 2),
            "total_cost_Base_M": round((hold + order + 1.0 * base_short) / 1e6, 2),
            "total_cost_High_M": round((hold + order + 2.0 * base_short) / 1e6, 2),
            "portfolio_fill_rate_pct": round((ful_dem / tot_dem) * 100.0, 2),
            "vital_avg_stockout_days": round(v_short_days, 2),
            "all_avg_stockout_days": round(all_short_days, 2),
        })

    return pd.DataFrame(summary_rows), detail_df


def run_backtest_evaluation(
    db_path: str = "data/processed/mro_inventory.db",
    seed: int = 42,
    output_csv: str = "data/processed/backtest_summary.csv",
) -> pd.DataFrame:
    """Evaluate policies under Backorder (primary) and Lost Sales (sensitivity), plus concentration & multi-seed checks."""
    with sqlite3.connect(db_path) as conn:
        parts = pd.read_sql_query("SELECT * FROM parts;", conn)
        cur_pol = pd.read_sql_query("SELECT * FROM current_policy;", conn)
        cls_pol = pd.read_sql_query("SELECT * FROM classical_policies;", conn)
        boot_pol = pd.read_sql_query("SELECT * FROM bootstrap_policies;", conn)
        daily_test = pd.read_sql_query(
            "SELECT date, part_id, demand_qty FROM demand_history WHERE is_backtest = 1 ORDER BY date;",
            conn,
        )
        lt_cal = pd.read_sql_query("SELECT part_id, lead_time_days FROM lead_time_history;", conn)

    assert int(daily_test["date"].nunique()) == 365, "Test window must be exactly 365 days."

    test_demand_map = {pid: grp["demand_qty"].to_numpy(dtype=float) for pid, grp in daily_test.groupby("part_id", sort=False)}
    lt_pool_map = {pid: grp["lead_time_days"].to_numpy(dtype=int) for pid, grp in lt_cal.groupby("part_id", sort=False)}

    meta = parts.merge(cur_pol, on="part_id").merge(cls_pol.drop(columns=["ved_class", "unit_cost"]), on="part_id")
    # Tum politikalarda esit baslangic stogu (initial_stock)
    init_stock_map = {r["part_id"]: max(1, int(r["min_stock"])) for _, r in meta.iterrows()}
    policies = _build_policy_list(meta, boot_pol)

    rng = np.random.default_rng(seed)
    crn_lt_map = {pid: rng.choice(lt_pool_map[pid], size=400, replace=True) for pid in parts["part_id"]}

    # 1. Birincil Model: Backorder (T?z?k Sec. 4 & DEC-02 ile birebir uyumlu)
    sum_bo, det_bo = _evaluate_mode(meta, policies, test_demand_map, crn_lt_map, init_stock_map, "backorder", 30.0)
    sum_bo7, _ = _evaluate_mode(meta, policies, test_demand_map, crn_lt_map, init_stock_map, "backorder", 7.0)
    # 2. Duyarlilik Modeli: Lost Sales (Kayip Satis)
    sum_ls, _ = _evaluate_mode(meta, policies, test_demand_map, crn_lt_map, init_stock_map, "lost_sales")

    mode_comp = sum_bo[["policy", "total_cost_Base_M", "portfolio_fill_rate_pct", "vital_avg_stockout_days"]].rename(
        columns={
            "total_cost_Base_M": "backorder_div30_M",
            "portfolio_fill_rate_pct": "backorder_fill_rate_pct",
            "vital_avg_stockout_days": "backorder_vital_so_days",
        }
    ).merge(sum_bo7[["policy", "total_cost_Base_M"]].rename(columns={"total_cost_Base_M": "backorder_div7_M"}), on="policy").merge(
        sum_ls[["policy", "total_cost_Base_M", "portfolio_fill_rate_pct", "vital_avg_stockout_days"]].rename(
            columns={
                "total_cost_Base_M": "lost_sales_M",
                "portfolio_fill_rate_pct": "lost_sales_fill_rate_pct",
                "vital_avg_stockout_days": "lost_sales_vital_so_days",
            }
        ),
        on="policy",
    )

    # 3. Tasarruf Yogunlasmasi ve 20-Tohum Dayaniklilik Analizi (Backorder)
    cur_p = det_bo[det_bo["policy"] == "MinMax_Current_1.5_3.0m"].copy()
    opt_p = det_bo[det_bo["policy"] == "Bootstrap_CSL98"].copy()
    cur_p["cur_tot"] = cur_p["holding_cost"] + cur_p["ordering_cost"] + cur_p["base_shortage_cost"]
    opt_p["opt_tot"] = opt_p["holding_cost"] + opt_p["ordering_cost"] + opt_p["base_shortage_cost"]
    m_sav = cur_p[["part_id", "cur_tot"]].merge(opt_p[["part_id", "opt_tot"]], on="part_id")
    m_sav["sav"] = m_sav["cur_tot"] - m_sav["opt_tot"]
    m_sav = m_sav.sort_values("sav", ascending=False).reset_index(drop=True)

    tot_cur = float(m_sav["cur_tot"].sum())
    tot_sav = float(m_sav["sav"].sum())
    ex5_sav = float(m_sav.iloc[5:]["sav"].sum())
    ex5_cur = float(m_sav.iloc[5:]["cur_tot"].sum())
    ex10_sav = float(m_sav.iloc[10:]["sav"].sum())
    ex10_cur = float(m_sav.iloc[10:]["cur_tot"].sum())

    seed_sav_vs_mm = []
    seed_sav_vs_cls = []
    core_pols = [p for p in policies if p[0] in ("MinMax_Current_1.5_3.0m", "Classical_Hist_CSL95", "Bootstrap_CSL98")]
    for s in range(100, 120):
        r_s = np.random.default_rng(s)
        lt_s = {pid: r_s.choice(lt_pool_map[pid], size=400, replace=True) for pid in parts["part_id"]}
        s_df, _ = _evaluate_mode(meta, core_pols, test_demand_map, lt_s, init_stock_map, "backorder")
        c_mm = float(s_df[s_df["policy"] == "MinMax_Current_1.5_3.0m"]["total_cost_Base_M"].iloc[0])
        c_cl = float(s_df[s_df["policy"] == "Classical_Hist_CSL95"]["total_cost_Base_M"].iloc[0])
        c_bt = float(s_df[s_df["policy"] == "Bootstrap_CSL98"]["total_cost_Base_M"].iloc[0])
        seed_sav_vs_mm.append((c_mm - c_bt) / c_mm * 100.0)
        seed_sav_vs_cls.append((c_cl - c_bt) / c_cl * 100.0)

    robust_df = pd.DataFrame([
        {"metric": "Tum Portfoy Tasarruf (200 SKU, Backorder)", "value_pct": round(tot_sav / tot_cur * 100, 1), "note": f"{round(tot_sav/1e6, 2)} M TL net tasarruf"},
        {"metric": "Ilk 5 Parca Haric Tasarruf (195 SKU)", "value_pct": round(ex5_sav / ex5_cur * 100, 1), "note": "En yuksek 5 tasarruf parcasi cikarildiginda"},
        {"metric": "Ilk 10 Parca Haric Tasarruf (190 SKU)", "value_pct": round(ex10_sav / ex10_cur * 100, 1), "note": "En yuksek 10 tasarruf parcasi cikarildiginda"},
        {"metric": "20-Seed MinMax'e Karsi Tasarruf Araligi", "value_pct": round(float(np.median(seed_sav_vs_mm)), 1), "note": f"Min %{round(min(seed_sav_vs_mm),1)} - Max %{round(max(seed_sav_vs_mm),1)}"},
        {"metric": "20-Seed Klasik Formule Karsi Tasarruf Araligi", "value_pct": round(float(np.median(seed_sav_vs_cls)), 1), "note": f"Min %{round(min(seed_sav_vs_cls),1)} - Max %{round(max(seed_sav_vs_cls),1)}"},
    ])

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    sum_bo.to_csv(output_csv, index=False)
    det_bo.to_csv("data/processed/backtest_part_details.csv", index=False)
    mode_comp.to_csv("data/processed/backtest_mode_comparison.csv", index=False)
    robust_df.to_csv("data/processed/backtest_concentration_and_seeds.csv", index=False)

    with sqlite3.connect(db_path) as conn:
        sum_bo.to_sql("backtest_summary", conn, if_exists="replace", index=False)
        det_bo.to_sql("backtest_part_details", conn, if_exists="replace", index=False)
        mode_comp.to_sql("backtest_mode_comparison", conn, if_exists="replace", index=False)
        robust_df.to_sql("backtest_robustness", conn, if_exists="replace", index=False)

    return sum_bo


if __name__ == "__main__":
    run_backtest_evaluation()
