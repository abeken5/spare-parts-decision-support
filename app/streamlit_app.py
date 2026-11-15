from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "data/processed/mro_inventory.db"

st.set_page_config(
    page_title="MRO Yedek Parça Envanter Karar Destek Sistemi",
    page_icon="✈️",
    layout="wide",
)


@st.cache_data
def load_core_tables(db_path: str = DB_PATH) -> dict[str, pd.DataFrame]:
    with sqlite3.connect(db_path) as conn:
        return {
            "bt_sum": pd.read_sql_query("SELECT * FROM backtest_summary;", conn),
            "bt_det": pd.read_sql_query("SELECT * FROM backtest_part_details;", conn),
            "boot": pd.read_sql_query("SELECT * FROM bootstrap_policies;", conn),
            "action": pd.read_sql_query("SELECT * FROM part_action_plan;", conn),
        }


def classify_dynamic_action(row: pd.Series) -> str:
    if row["annual_demand_qty"] <= 0.5 or row["forecast_monthly_part"] < 0.15:
        return "Düşük Hız / Eskime İzleme (Manuel Onay)"
    if row["rop_selected"] > row["min_stock"] and (row["ved_class"] == "V" or row["cur_stockout_days"] > 0):
        return "Kritik Stok Artışı (ROP Yükselt)"
    if row["rop_selected"] < row["min_stock"]:
        return "Aşırı Stoğu Erit (Sermaye Çöz)"
    return "Dengeli (s, Q Geçişi)"


st.title("✈️ Savunma / Havacılık MRO Yedek Parça Karar Destek Sistemi")
st.caption(
    "Syntetos-Boylan Segmentasyonu • Croston/SBA Tahmin • Ampirik Blok Bootstrap (10.000 Senaryo) • 365 Günlük CRN Backtest"
)

if not Path(DB_PATH).exists():
    st.error("Veritabanı bulunamadı. Lütfen önce veri üretim ve backtest boru hattını çalıştırın.")
    st.stop()

data = load_core_tables()
bt_sum = data["bt_sum"]
bt_det = data["bt_det"]
boot_df = data["boot"]
base_action = data["action"]

# Sidebar: Decision Parameters (R-10: Explicit CSL vs Fill Rate distinction)
st.sidebar.header("🎛️ Politika & Risk Parametreleri")
target_csl = st.sidebar.select_slider(
    "Hedef Döngü Hizmet Seviyesi (Target CSL)",
    options=[0.85, 0.90, 0.95, 0.98, 0.99],
    value=0.95,
    format_func=lambda x: f"%{int(round(x * 100))}",
    help="CSL tedarik süresinde stoksuzluk yaşamama olasılığıdır; gerçekleşen talep karşılama oranı (Fill Rate) ayrıca ölçülür.",
)

penalty_choice = st.sidebar.radio(
    "VED Stoksuzluk Ceza Senaryosu (R-01)",
    options=["Low_0.5x", "Base_1.0x", "High_2.0x"],
    index=1,
    format_func=lambda x: {
        "Low_0.5x": "Düşük Ceza (0.5x — İyimser)",
        "Base_1.0x": "Baz Senaryo (1.0x — Charter)",
        "High_2.0x": "Yüksek Ceza (2.0x — Kritik Filo)",
    }[x],
)
cost_col_map = {
    "Low_0.5x": ("total_cost_Low_M", 0.5),
    "Base_1.0x": ("total_cost_Base_M", 1.0),
    "High_2.0x": ("total_cost_High_M", 2.0),
}
tot_cost_col, pen_mult = cost_col_map[penalty_choice]

st.sidebar.divider()
st.sidebar.subheader("🔍 Portföy Filtreleri")
ved_filter = st.sidebar.multiselect("VED Kritiklik", ["V", "E", "D"], default=["V", "E", "D"])
abc_filter = st.sidebar.multiselect("ABC Sınıfı", ["A", "B", "C"], default=["A", "B", "C"])
sb_filter = st.sidebar.multiselect(
    "Talep Deseni (Syntetos-Boylan)",
    ["Smooth", "Erratic", "Intermittent", "Lumpy"],
    default=["Smooth", "Erratic", "Intermittent", "Lumpy"],
)

# Merge dynamic CSL selection
csl_tag = f"Bootstrap_CSL{int(round(target_csl * 100))}"
cur_row = bt_sum[bt_sum["policy"] == "MinMax_Current_1.5_3.0m"].iloc[0]
opt_row = bt_sum[bt_sum["policy"] == csl_tag].iloc[0]

boot_sel = boot_df[boot_df["target_csl"].sub(target_csl).abs() < 1e-6][
    ["part_id", "rop_bootstrap", "ss_bootstrap", "p99_lt_demand_emp", "order_qty_q"]
].rename(columns={"rop_bootstrap": "rop_selected", "ss_bootstrap": "ss_selected"})

det_cur = bt_det[bt_det["policy"] == "MinMax_Current_1.5_3.0m"][
    ["part_id", "holding_cost", "ordering_cost", "base_shortage_cost", "fill_rate", "stockout_days"]
].rename(
    columns={
        "holding_cost": "c_hold",
        "ordering_cost": "c_ord",
        "base_shortage_cost": "c_short",
        "fill_rate": "c_fr",
        "stockout_days": "c_sd",
    }
)
det_opt = bt_det[bt_det["policy"] == csl_tag][
    ["part_id", "holding_cost", "ordering_cost", "base_shortage_cost", "fill_rate", "stockout_days"]
].rename(
    columns={
        "holding_cost": "o_hold",
        "ordering_cost": "o_ord",
        "base_shortage_cost": "o_short",
        "fill_rate": "o_fr",
        "stockout_days": "o_sd",
    }
)

merged = (
    base_action.drop(columns=["rop_bootstrap", "ss_bootstrap", "order_qty_q", "recommended_action"])
    .merge(boot_sel, on="part_id")
    .merge(det_cur, on="part_id")
    .merge(det_opt, on="part_id")
)
merged["cur_scen_cost_tl"] = merged["c_hold"] + merged["c_ord"] + pen_mult * merged["c_short"]
merged["opt_scen_cost_tl"] = merged["o_hold"] + merged["o_ord"] + pen_mult * merged["o_short"]
merged["scen_savings_tl"] = (merged["cur_scen_cost_tl"] - merged["opt_scen_cost_tl"]).round(2)
merged["recommended_action"] = merged.apply(classify_dynamic_action, axis=1)

filtered = merged[
    merged["ved_class"].isin(ved_filter)
    & merged["abc_class"].isin(abc_filter)
    & merged["sb_class"].isin(sb_filter)
].copy()

# Top Executive KPIs
savings_m = float(cur_row[tot_cost_col] - opt_row[tot_cost_col])
savings_pct = (savings_m / float(cur_row[tot_cost_col])) * 100.0

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    label=f"Yıllık Toplam Maliyet ({csl_tag})",
    value=f"{opt_row[tot_cost_col]:.2f} M TL",
    delta=f"{-savings_m:.2f} M TL (-%{savings_pct:.1f})",
    delta_color="inverse",
)
k2.metric(
    label="Elde Tutma Maliyeti (Sermaye)",
    value=f"{opt_row['holding_cost_M']:.2f} M TL",
    delta=f"{opt_row['holding_cost_M'] - cur_row['holding_cost_M']:+.2f} M TL vs. Mevcut",
    delta_color="inverse",
)
k3.metric(
    label="Gerçekleşen Fill Rate (Portföy)",
    value=f"%{opt_row['portfolio_fill_rate_pct']:.2f}",
    delta=f"{opt_row['portfolio_fill_rate_pct'] - cur_row['portfolio_fill_rate_pct']:+.2f} puan",
)
k4.metric(
    label="Vital (V) Ort. Stoksuzluk Günü",
    value=f"{opt_row['vital_avg_stockout_days']:.2f} gün",
    delta=f"{opt_row['vital_avg_stockout_days'] - cur_row['vital_avg_stockout_days']:+.2f} gün",
    delta_color="inverse",
)

tab1, tab2, tab3 = st.tabs([
    "📊 Yönetici Özeti & Pareto Eğrisi",
    "📋 Parça Bazlı Aksiyon Listesi",
    "🔬 Tekil Parça Röntgeni",
])

with tab1:
    st.subheader("Politika Karşılaştırması: Mevcut Min/Max vs. Klasik (s, Q) vs. Ampirik Blok Bootstrap")
    disp_cols = [
        "policy",
        "holding_cost_M",
        "ordering_cost_M",
        "shortage_base_M",
        tot_cost_col,
        "portfolio_fill_rate_pct",
        "vital_avg_stockout_days",
    ]
    st.dataframe(
        bt_sum[disp_cols].rename(
            columns={
                "policy": "Politika",
                "holding_cost_M": "Elde Tutma (M TL)",
                "ordering_cost_M": "Sipariş (M TL)",
                "shortage_base_M": "Baz Stoksuzluk (M TL)",
                tot_cost_col: f"Toplam Maliyet [{penalty_choice}] (M TL)",
                "portfolio_fill_rate_pct": "Gerçekleşen Fill Rate (%)",
                "vital_avg_stockout_days": "Vital Stoksuzluk (Gün)",
            }
        ),
        width='stretch',
        hide_index=True,
    )

    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("**Toplam Maliyet Karşılaştırması (Milyon TL)**")
        chart_cost = bt_sum.set_index("policy")[[tot_cost_col]].rename(
            columns={tot_cost_col: "Toplam Maliyet (M TL)"}
        )
        st.bar_chart(chart_cost)
    with c_right:
        st.markdown("**Gerçekleşen Fill Rate (%) Karşılaştırması**")
        chart_fr = bt_sum.set_index("policy")[["portfolio_fill_rate_pct"]].rename(
            columns={"portfolio_fill_rate_pct": "Fill Rate (%)"}
        )
        st.bar_chart(chart_fr)

with tab2:
    st.subheader(f"Filtrelenmiş Karar Tablosu ({len(filtered)} / 200 Parça)")
    act_summary = filtered["recommended_action"].value_counts().reset_index()
    act_summary.columns = ["Önerilen Aksiyon", "Parça Sayısı"]
    st.dataframe(act_summary, width='stretch', hide_index=True)

    show_cols = [
        "part_id",
        "category",
        "ved_class",
        "abc_xyz",
        "sb_class",
        "winner_part_level",
        "unit_cost",
        "min_stock",
        "rop_selected",
        "order_qty_q",
        "c_fr",
        "o_fr",
        "scen_savings_tl",
        "recommended_action",
    ]
    table_df = filtered[show_cols].sort_values("scen_savings_tl", ascending=False)
    st.dataframe(
        table_df.rename(
            columns={
                "part_id": "Parça Kodu",
                "category": "Sistem",
                "ved_class": "VED",
                "abc_xyz": "ABC-XYZ",
                "sb_class": "Talep Deseni",
                "winner_part_level": "Kazanan Model",
                "unit_cost": "Birim Fiyat (TL)",
                "min_stock": "Mevcut Min",
                "rop_selected": "Önerilen ROP (s)",
                "order_qty_q": "Sipariş Miktarı (Q)",
                "c_fr": "Mevcut Fill Rate",
                "o_fr": "Yeni Fill Rate",
                "scen_savings_tl": "Net Tasarruf (TL)",
                "recommended_action": "Aksiyon",
            }
        ),
        width='stretch',
        hide_index=True,
    )

    csv_bytes = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Aksiyon Listesini CSV Olarak İndir (ERP Aktarımı)",
        data=csv_bytes,
        file_name=f"mro_action_plan_csl{int(round(target_csl * 100))}.csv",
        mime="text/csv",
    )

with tab3:
    st.subheader("Tekil Parça Talep ve Politika Röntgeni")
    sel_pid = st.selectbox("İncelenecek Parçayı Seçin", options=merged["part_id"].tolist())
    p_info = merged[merged["part_id"] == sel_pid].iloc[0]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sınıf (VED / ABC-XYZ)", f"{p_info['ved_class']} / {p_info['abc_xyz']}")
    m2.metric("Syntetos-Boylan / Model", f"{p_info['sb_class']} / {p_info['winner_part_level']}")
    m3.metric("Mevcut Min / Max", f"{int(p_info['min_stock'])} / {int(p_info['max_stock'])}")
    m4.metric("Önerilen ROP (s) / EOQ (Q)", f"{int(p_info['rop_selected'])} / {int(p_info['order_qty_q'])}")

    with sqlite3.connect(DB_PATH) as conn:
        hist_ts = pd.read_sql_query(
            "SELECT date, demand_qty, is_backtest FROM demand_history WHERE part_id = ? ORDER BY date;",
            conn,
            params=(sel_pid,),
        )
    hist_ts["date"] = pd.to_datetime(hist_ts["date"])
    hist_ts["Ay"] = hist_ts["date"].dt.to_period("M").astype(str)
    monthly_ts = hist_ts.groupby("Ay")["demand_qty"].sum().reset_index().set_index("Ay")
    st.markdown("**36 Aylık Tüketim Seyri (İlk 24 Ay Kalibrasyon + Son 12 Ay Backtest)**")
    st.line_chart(monthly_ts)

