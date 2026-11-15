# MRO Karar Destek Sistemi - Tam Inceleme Paketi
- GitHub: https://github.com/abeken5/spare-parts-decision-support
- Canli App: https://mro-spare-parts-dss.streamlit.app


---
## DOSYA: .github\workflows\ci.yml
```
name: CI Pipeline
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - run: pytest

```

---
## DOSYA: app\streamlit_app.py
```
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


```

---
## DOSYA: data\generator.py
```
from pathlib import Path
import numpy as np
import pandas as pd

RANDOM_SEED = 42


def generate_mro_dataset(output_dir: str = "data/raw", seed: int = RANDOM_SEED) -> dict[str, pd.DataFrame]:
    """Generate synthetic defense/aerospace MRO spare parts dataset with fixed seed."""
    rng = np.random.default_rng(seed)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Exact 3 non-leap years: 730 calibration days (24 months) + 365 backtest days (12 months)
    dates = pd.date_range(start="2021-01-01", end="2023-12-31", freq="D")
    n_days = len(dates)  # 1095
    cal_days = 730

    archetypes = (
        ["smooth"] * 40
        + ["erratic"] * 40
        + ["intermittent"] * 60
        + ["lumpy"] * 60
    )
    rng.shuffle(archetypes)

    ved_pool = ["V"] * 50 + ["E"] * 90 + ["D"] * 60
    rng.shuffle(ved_pool)

    categories = ["Avionics", "Hydraulics", "Landing_Gear", "Propulsion", "Airframe", "Consumables"]
    suppliers = [f"SUP-{i:02d}" for i in range(1, 13)]

    parts_rows = []
    demand_rows = []
    lead_time_rows = []
    policy_rows = []

    for idx in range(200):
        part_id = f"PART-{idx + 1:03d}"
        arch = archetypes[idx]
        ved = ved_pool[idx]
        supplier_id = rng.choice(suppliers)
        category = categories[idx % len(categories)]

        # Unit cost & lead time calibrated by VED criticality (avoids strawman baseline)
        if ved == "V":
            unit_cost = round(float(rng.uniform(18000, 110000)), 2)
            lt_mean = float(rng.uniform(20, 42))
        elif ved == "E":
            unit_cost = round(float(rng.uniform(3000, 22000)), 2)
            lt_mean = float(rng.uniform(12, 32))
        else:
            unit_cost = round(float(rng.uniform(300, 3500)), 2)
            lt_mean = float(rng.uniform(7, 22))

        lt_std = round(lt_mean * float(rng.uniform(0.18, 0.35)), 2)

        # Anti-circularity patterns: regime shift (15%) or obsolescence (10%)
        roll = rng.random()
        if roll < 0.15:
            special_pattern = "regime_shift"
        elif roll < 0.25:
            special_pattern = "obsolescence"
        else:
            special_pattern = "stationary"

        # Base daily arrival probability and non-zero order size parameters
        if arch == "smooth":
            p_arr = rng.uniform(0.14, 0.28)
            size_low, size_high = 1, 3
        elif arch == "erratic":
            p_arr = rng.uniform(0.10, 0.20)
            size_low, size_high = 1, 14
        elif arch == "intermittent":
            p_arr = rng.uniform(0.018, 0.045)
            size_low, size_high = 1, 2
        else:  # lumpy
            p_arr = rng.uniform(0.012, 0.035)
            size_low, size_high = 2, 18

        daily_demand = np.zeros(n_days, dtype=int)
        shift_day = int(rng.integers(500, 820))
        obsolete_day = int(rng.integers(760, 920))

        for d in range(n_days):
            p_today = p_arr
            mult = 1.0
            if special_pattern == "regime_shift" and d >= shift_day:
                p_today = min(0.45, p_arr * 1.65)
                mult = 1.4
            elif special_pattern == "obsolescence" and d >= obsolete_day:
                p_today = 0.0

            if rng.random() < p_today:
                if arch in ("smooth", "intermittent"):
                    qty = int(rng.integers(size_low, size_high + 1))
                else:
                    # Heavy-tailed burst size for erratic/lumpy demand
                    raw = rng.lognormal(mean=np.log((size_low + size_high) / 3.0), sigma=0.65)
                    qty = int(np.clip(np.round(raw * mult), size_low, size_high * 2))
                daily_demand[d] = max(1, qty)

        parts_rows.append({
            "part_id": part_id,
            "part_name": f"{category}_Component_{idx + 1:03d}",
            "category": category,
            "ved_class": ved,
            "unit_cost": unit_cost,
            "supplier_id": supplier_id,
            "true_archetype": arch,
            "special_pattern": special_pattern,
        })

        for d_idx, dt in enumerate(dates):
            demand_rows.append({
                "date": dt.strftime("%Y-%m-%d"),
                "part_id": part_id,
                "demand_qty": int(daily_demand[d_idx]),
                "is_backtest": int(d_idx >= cal_days),
            })

        # Historical lead time observations (25 deliveries in calibration window)
        shape_k = (lt_mean / lt_std) ** 2
        scale_theta = (lt_std ** 2) / lt_mean
        lt_samples = np.maximum(2, np.round(rng.gamma(shape_k, scale_theta, size=25))).astype(int)
        obs_days = np.sort(rng.choice(np.arange(15, cal_days - 10), size=25, replace=False))
        for s_idx, (o_day, lt_val) in enumerate(zip(obs_days, lt_samples)):
            lead_time_rows.append({
                "shipment_id": f"SHP-{part_id}-{s_idx + 1:02d}",
                "part_id": part_id,
                "supplier_id": supplier_id,
                "order_date": dates[o_day].strftime("%Y-%m-%d"),
                "lead_time_days": int(lt_val),
            })

        # Stylized current policy calibrated ONLY on first 730 days (24 calendar months)
        cal_monthly_mean = float(daily_demand[:cal_days].sum()) / 24.0
        min_stock = max(1, int(np.ceil(1.5 * cal_monthly_mean))) if cal_monthly_mean > 0 else 1
        max_stock = max(min_stock + 1, int(np.ceil(3.0 * cal_monthly_mean)))
        initial_stock = int(np.ceil((min_stock + max_stock) / 2.0))

        policy_rows.append({
            "part_id": part_id,
            "min_stock": min_stock,
            "max_stock": max_stock,
            "initial_stock": initial_stock,
            "calibration_monthly_mean": round(cal_monthly_mean, 4),
        })

    tables = {
        "parts": pd.DataFrame(parts_rows),
        "demand_history": pd.DataFrame(demand_rows),
        "lead_time_history": pd.DataFrame(lead_time_rows),
        "current_policy": pd.DataFrame(policy_rows),
    }

    for name, df in tables.items():
        df.to_csv(out_path / f"{name}.csv", index=False)

    return tables


if __name__ == "__main__":
    data = generate_mro_dataset()
    print("Veri uretimi tamamlandi:")
    for k, v in data.items():
        print(f" - {k}: {len(v):,} satir")
    print("\nVED Dagilimi:\n", data["parts"]["ved_class"].value_counts().to_dict())
    print("Ozel Desenler:\n", data["parts"]["special_pattern"].value_counts().to_dict())

```

---
## DOSYA: docs\executive_decision_brief.md
```
# Yönetici Karar Özeti — MRO Yedek Parça Envanter Optimizasyonu

## 1. Temel Karar Önerisi
- **Önerilen Politika:** Ampirik Blok Bootstrap `(s, Q)` — Hedef Döngü Hizmet Seviyesi **CSL = %95**
- **Yıllık Toplam Maliyet Etkisi (Baz Senaryo):** `82.72 M TL` -> `48.46 M TL` (**34.26 M TL / %41.4 tasarruf**)
- **Hizmet Seviyesi (Fill Rate) Etkisi:** `%92.17` -> `%95.52` (+3.35 puan)
- **Vital (V) Parça Stoksuzluk Riski:** `2.32 gün` -> `1.16 gün` (%50 azalma)
- **Eşit Fill Rate Sermaye Verimliliği:** Mevcut kuralı %95,6 Fill Rate'e zorlamak (`2.0/4.0 ay`) `25.6 M TL` elde tutma maliyeti yaratırken, Bootstrap `18.29 M TL` ile aynı hizmeti **%28,5 daha az işletme sermayesiyle** sağlar.

## 2. Parça Bazlı Aksiyon Dağılımı (200 SKU)
- **Kritik Stok Artışı (ROP Yükselt):** 91 parça
- **Dengeli (s, Q Geçişi):** 56 parça
- **Aşırı Stoğu Erit (Sermaye Çöz):** 46 parça
- **Düşük Hız / Eskime İzleme (Manuel Onay):** 7 parça

## 3. Uygulama ve Yönetişim Notu
- Düşük hızlı / eskime riski taşıyan parçalar otomatik yenilemeye kapatılarak bakım mühendisliği onayına bağlanmalıdır (`R-04`).
- Yıllık bütçe kısıtına göre CSL seviyesi `%95` (`48.46 M TL` toplam maliyet) ile `%98` (`39.86 M TL` toplam maliyet, `0.56 gün` Vital stoksuzluk) arasında seçilebilir.
```

---
## DOSYA: docs\pm\01_charter.md
```
# Proje Tüzüğü (Project Charter)

## 1. Proje Kimliği
- **Proje Adı:** Savunma ve Havacılık MRO Yedek Parça Envanter Karar Destek Sistemi
- **Proje Yöneticisi:** Ahmet Elvan Beken
- **Süre ve Dil:** 6 Hafta (Sprint 0 – Sprint 5) | Doküman/UI Türkçe, kod İngilizce (`snake_case`).

## 2. İş Problemi ve Amaç
Bakım-onarım (MRO) operasyonlarında yedek parça talebi seyrek (*intermittent*) ve ani sıçramalıdır (*lumpy*). Sabit Excel Min/Max kuralları ve normal dağılım varsayan klasik *Safety Stock* formülleri sıfır talep dönemlerini ve değişken tedarik sürelerini yönetemez.

**Temel İş Sorusu:** *"Parça bazında ne zaman, ne kadar sipariş verilmeli ve mevcut Min/Max politikası yerine önerilen politika, hedef hizmet seviyesini koruyarak toplam maliyeti ne kadar düşürür?"*

## 3. Başarı Kriterleri ve Koruyucu Kısıt (Guardrail)
1. **Birincil Hedef:** %95 hizmet seviyesinde önerilen politikanın, mevcut Min/Max politikasına göre toplam envanter maliyetini **en az %15** düşürmesi *(kesin eşik Sprint 1 veri kalibrasyonu sonrası kilitlenecektir)*.
2. **Koruyucu Kısıt (Guardrail):** Maliyet tek başına kazananı belirlemez. Her backtest çıktısında **Fill Rate**, **Cycle Service Level** ve **Stoksuzluk Günü** yan yana raporlanır; hedef hizmet seviyesinin altına düşen politika elenir.

## 4. Maliyet Modeli ve Operasyonel Varsayımlar
1. **Elde Tutma Maliyeti:** $\text{Ortalama Eldeki Stok} \times \text{Birim Maliyet} \times \%22\text{ (Yıllık)}$ *(Sermaye %13, depolama/sigorta %5, eskime riski %4)*.
2. **Sipariş Maliyeti:** $\text{Verilen Sipariş Sayısı} \times 1.500\text{ TL}$ *(Satın alma, CoC sertifika kontrolü ve giriş kalite muayenesi)*.
3. **Stoksuzluk Cezası (Backorder Varsayımı):** MRO'da eksik parça kayıp satışa (*Lost Sales*) dönüşmez, bakım emri açık bekler (*Backorder*). $\text{Ceza} = \text{Karşılanamayan Birim} \times \text{Birim Ceza}$.
4. **Kapsam Dışı Maliyet:** Birim satın alma maliyeti ($\text{Birim Fiyat} \times \text{Toplam Talep}$), backorder altında uzun vadede sabit kaldığı için karşılaştırma denklemine dahil edilmemiştir.

### Kritiklik (VED) Bazlı Ceza ve 3 Senaryolu Duyarlılık Matrisi
| Kritiklik | Operasyonel Etki | Düşük (0.5x) | Baz (1.0x) | Yüksek (2.0x) |
| :--- | :--- | :--- | :--- | :--- |
| **V — Vital** | Ekipmanı yerde tutar (AOG) | Fiyat × 0.75 | **Fiyat × 1.50** | Fiyat × 3.00 |
| **E — Essential** | Bakım takvimini geciktirir | Fiyat × 0.375 | **Fiyat × 0.75** | Fiyat × 1.50 |
| **D — Desirable** | Rutin sarf / ikame edilebilir | Fiyat × 0.125 | **Fiyat × 0.25** | Fiyat × 0.50 |

## 5. Kapsam ve Kapsam Dışı
- **Kapsam İçi (MVP):** Parametrik sentetik MRO veri üreteci, SQLite şeması ve ABC/KPI SQL görünümleri, ABC-XYZ ve ADI/CV² segmentasyonu, Naive/MA/Croston/SBA/TSB tahmin modelleri, klasik SS/ROP/EOQ vs. Bootstrap/Monte Carlo karşılaştırması, Min/Max backtest motoru, Streamlit dashboard, birim testler.
- **Kapsam Dışı:** METRIC çok kademeli model, (S-1, S) politikası, bütçe kısıtlı çoklu parça optimizasyonu, derin öğrenme, canlı ERP entegrasyonu.

```

---
## DOSYA: docs\pm\02_data_readiness.md
```
# Veri Hazırlık Değerlendirmesi (Data Readiness Assessment)

## 1. İhtiyaç Duyulan Tablolar
1. `parts`: `part_id`, parça adı, birim maliyet (TL), VED kritiklik sınıfı, tedarikçi.
2. `current_policy`: Mevcut sabit `min_stock`, `max_stock` ve başlangıç stoğu.
3. `demand_history`: 36 aylık (1095 günlük) tüketim kayıtları (sıfır talep dönemleri dahil).
4. `lead_time_history`: Sipariş ve teslim tarihleri ile tedarik süresi (`lead_time_days`) dağılımı.

## 2. Boşluk Analizi ve Sentetik Veri Kararı
Savunma/havacılık MRO verileri gizlilik nedeniyle kamuya açık değildir (**R-02**). Bu nedenle Syntetos & Boylan (2005) literatüründeki 4 talep sınıfını (Smooth, Erratic, Intermittent, Lumpy) dengeli temsil eden, 200 parçalık ve sabit tohumlu (`RANDOM_SEED = 42`) parametrik veri üreteci (`data/generator.py`) geliştirilecektir. İlk 24 ay kalibrasyon, son 12 ay politika backtest penceresi olarak ayrılacaktır.

```

---
## DOSYA: docs\pm\05_risk_register.md
```
# İş Kırılım Yapısı (WBS) ve 6 Haftalık Takvim

- **Sprint 0 (Hafta 1):** Yönetişim dokümanları (Tüzük, RACI, Risk, Karar Günlüğü), repo iskeleti, CI ve GitHub Projects.
- **Sprint 1 (Hafta 2):** Sentetik veri üreteci (`generator.py`), SQLite şeması, ABC/KPI SQL görünümleri, ABC-XYZ ve ADI/CV² sınıflandırma + testler.
- **Sprint 2 (Hafta 3):** Naive, MA, Croston, SBA, TSB tahmin modelleri; MAE/RMSE/MASE kıyaslaması ve MAPE yanılgısı analizi; klasik SS/ROP/EOQ + testler.
- **Sprint 3 (Hafta 4):** Bootstrap / Monte Carlo simülasyonu, klasik formülle karşılaştırma, Min/Max backtest ve 3 senaryolu ceza duyarlılık analizi.
- **Sprint 4 (Hafta 5):** Streamlit karar destek arayüzü ve Yönetici Özeti (`09_executive_summary.md`).
- **Sprint 5 (Hafta 6):** Uçtan uca doğrulama, Streamlit Community Cloud yayını, README finalizasyonu ve retrospektif.

```mermaid
gantt
    title MRO Yedek Parça Karar Destek Sistemi (6 Hafta)
    dateFormat  YYYY-MM-DD
    section Sprintler
    Sprint 0 - PM ve Altyapı          :active, s0, 2026-11-14, 7d
    Sprint 1 - Veri ve Segmentasyon   :s1, 2026-11-21, 7d
    Sprint 2 - Tahmin ve Klasik SS    :s2, 2026-11-28, 7d
    Sprint 3 - Simülasyon ve Backtest :s3, 2026-12-05, 7d
    Sprint 4 - Streamlit ve Özet      :s4, 2026-12-12, 7d
    Sprint 5 - Yayın ve Kapanış       :s5, 2026-12-19, 7d
@'
# Risk Kaydı (Risk Register)

| ID | Risk Tanımı | Olasılık | Etki | Azaltma Planı (Mitigation) | Durum |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **R-01** | **Ceza maliyeti varsayımsal, sonuç duyarlı:** Yüksek ceza seçilirse önerilen politika yapay olarak avantajlı görünebilir. | Yüksek | Yüksek | VED kritiklik bazlı ceza tablosu ve 3 senaryolu (Düşük/Baz/Yüksek) duyarlılık analizi ile başabaş noktası raporlanacak. | Aktif |
| **R-02** | **Gerçek MRO verisine erişim kısıtı:** Gizlilik nedeniyle açık savunma/havacılık verisi bulunamaması. | Yüksek | Orta | Literatür parametrelerine sadık, sabit seed'li sentetik veri üreteci geliştirildi ve DEC-02'ye işlendi. | Gerçekleşti |
| **R-03** | **Model karmaşıklığının baseline'ı geçememesi:** Croston/TSB'nin aşırı seyrek parçalarda hareketli ortalamayı yenememesi. | Orta | Orta | Segment bazlı en iyi model seçilecek; yenemediği durumlar dürüstçe raporlanacak. | İzleniyor |
| **R-04** | **Son kullanıcı benimseme riski:** Planlamacıların simülasyona güvenmeyip Excel Min/Max'a dönmesi. | Orta | Yüksek | Arayüzde mevcut Min/Max ile önerilen politika TL ve stoksuzluk günü farkıyla yan yana şeffaf sunulacak. | İzleniyor |
| **R-05** | **24 aylık eğitim penceresinin dar kalması:** Aşırı seyrek parçalarda Croston/TSB kalibrasyonu için gözlem sayısının az olması. | Teknik | Orta | Orta | Eğitim penceresi 730 gün (24 tam takvim ayı) olarak sabitlendi; yetersiz sıfır-olmayan gözlemde basit hareketli ortalamaya düşüş (fallback) kuralı eklenecek. | Aktif |
| **R-06** | **Sentetik veri döngüselliği (totoloji riski):** Sabit dağılımla üretilen veride o dağılıma uyan modelin yapay olarak kazanması. | Metodoloji | Orta | Yüksek | Veri üreticisine talep seviyesi kayması (regime shift) ve parça eskimesi (obsolescence) senaryoları eklendi. | Azaltıldı |
| **R-07** | **Baseline'ın "saman adam" görünmesi:** Mevcut Min/Max kuralının kasıtlı zayıf kurgulanmış görünme riski. | Metodoloji | Orta | Yüksek | Min/Max katsayı duyarlılık gridi (1/2, 1.5/3, 2/4 ay) ve sabit adetli Seçenek B kıyaslaması backtest'e dahil edildi. | Aktif |
| **R-08** | **Dar doğrulama penceresinde parça bazlı seçim gürültüsü:** 6 aylık doğrulamada 0-2 talep olayı gören parçalarda model seçiminin şansa kalması. | Teknik | Orta | Orta | Rolling-origin 1-adım ileri doğrulama uygulandı; ayrıca parça bazlı seçim yanında talep sınıfı (segment) bazlı kazanan da üretilerek backtest'e alınacak. | Aktif |
| **R-09** | **TSB modelinin obsolescence senaryosunda doğal avantajı:** Veri üreticisinde eskime (talep sıfırlanması) bulunduğu için TSB'nin bu parçalarda öne çıkması. | Metodoloji | Yüksek | Düşük | Totoloji yaratmamak için TSB'nin obsolescence alt grubundaki performansı README ve analiz çıktısında şeffaf biçimde ayrıştırılarak raporlanacak. | Aktif |
| **R-10** | **Hizmet seviyesi tanımlarının karışması:** Klasik `z` değerinin döngü hizmet seviyesini (CSL), guardrail'in ise talep karşılama oranını (Fill Rate) ölçmesi. | Metodoloji / UX | Orta | Orta | Dashboard slider etiketi "Hedef Döngü Hizmet Seviyesi (CSL)" olarak adlandırılacak ve gerçekleşen Fill Rate ayrı sütunda raporlanacak. | Aktif |

```

---
## DOSYA: docs\pm\06_decision_log.md
```
# Karar Günlüğü (Decision Log)

| Karar ID | Tarih | Konu | Seçilen Karar | Gerekçe |
| :--- | :--- | :--- | :--- | :--- |
| **DEC-01** | 2026-11-14 | Dil Standardı | **Türkçe doküman/UI + İngilizce kod** | İşe alım uzmanları için net okunabilirlik, kod tabanında evrensel Python standardı. |
| **DEC-02** | 2026-11-14 | Maliyet ve Ceza Yapısı | **3 kalemli maliyet, Backorder, VED bazlı ceza + 3 senaryolu duyarlılık** | Satın alma maliyeti backorder altında sabittir; duyarlılık analizi varsayım yanlılığını önler. |
| **DEC-03** | 2026-11-14 | Veritabanı | **SQLite** | Kurulumsuz, taşınabilir ve analitik SQL görünümleri yazmaya uygun yapı. |
| **DEC-04** | 2026-11-14 | Tekrar Üretilebilirlik | **`RANDOM_SEED = 42`** | Veri üretimi ve simülasyon sonuçlarının her çalıştırmada birebir doğrulanabilmesi. |

| **DEC-05** | 2026-11-15 | Veri Çözünürlüğü ve Sızıntı Kuralı | **1.095 gün üretim (730 gün kalibrasyon, 365 gün backtest); günlük simülasyon + aylık tahmin hibriti** | Stoksuzluk günü ve gün cinsinden lead-time dağılımı için günlük veri şarttır. Aylık toplulaştırma yalnızca ADI/CV² ve tahmin modelleri için takvim günleriyle yapılır. Tüm parametreler yalnızca ilk 730 günden hesaplanır. |
| **DEC-06** | 2026-11-15 | Mevcut Politika (Baseline) Tanımı | **Stilize kaba kural: Min = 1.5 ay, Max = 3.0 ay eğitim ortalaması (günlük kontrol, backorder)** | Gerçek şirket verisi değil, stilize kuraldır. Saman adam (strawman) etkisini önlemek için lead time dağılımları 7-42 gün aralığında kalibre edildi; ayrıca 1/2, 1.5/3, 2/4 ay duyarlılık gridi ve ortak rastgele sayılar (CRN) uygulanacak. |
| **DEC-07** | 2026-11-15 | Tahmin Yarışması ve Seçim Kuralı | **18 ay eğitim / 6 ay rolling-origin doğrulama; birincil kriter RMSSE (%2 basitlik toleransı), MASE ve Bias raporlama; kazanan 24 ayla yeniden eğitilir** | MASE medyanı ödüllendirdiği için seyrek talepte düşük tahmini seçer ve stoksuzluğa yol açar; RMSSE ortalamayı korur. Sabit smoothing (`alpha=0.15, beta=0.15`), basitlik sırası `Naive < MA_3 < Croston < SBA < TSB`. Hem parça hem talep sınıfı bazlı kazanan saklanır. MAPE sıfır talepte tanımsızdır (`0/0`), sayısal örnekle gösterilir. |
| **DEC-08** | 2026-11-15 | Takvim Dönüşümü ve Klasik Formüller | **Tüm girdiler gün biriminde (`730 gün = 24 tam takvim ayı` assert kontrolü); gerçekleşen L ve σL; Döngü Hizmet Seviyesi vs. Fill Rate ayrımı** | Sabit 30 gün yerine gerçek takvim günü toplamı kullanılır. Klasik baseline `d_bar` ve `sigma_d` 730 günlük seriden, `L` ve `sigma_L` kalibrasyon teslimatlarından tahmin edilir (oracle sızıntısı önlenir). `z` döngü hizmet seviyesini hedefler, `fill rate` ayrı ölçülür. Klasik politika `(s, Q)`, mevcut Min/Max `(s, S)` yapısındadır. |
| **DEC-09** | 2026-11-15 | Simülasyon Yöntemi (Blok Bootstrap) | **730 günlük kalibrasyon serisinden ardışık L* günlük blok bootstrap (10.000 senaryo, seed=42)** | Bağımsız (i.i.d.) gün çekmek otokorelasyonu ve regime_shift dönemlerindeki talep yoğunluğunu seyreltir. Gerçekleşen teslimat süresinden L* çekilip L* ardışık gün toplanarak ampirik lead-time talep dağılımı elde edilir. |
| **DEC-10** | 2026-11-15 | Adil Kıyas ve Maliyet-Hizmet Pareto Eğrisi | **Bootstrap CSL eğrisi (%85-%99) + Genişletilmiş Min/Max gridi (1/2, 1.5/3, 2/4, 3/6 ay) + CRN** | Mevcut Min/Max sabit bir hizmet seviyesi hedeflemez. Eşit fill rate noktasında gerçek maliyet tasarrufunu kanıtlamak için Bootstrap çoklu CSL eğrisinde çalıştırılır; yoldaki siparişler envanter pozisyonunda takip edilir. |

```

---
## DOSYA: docs\pm\07_change_log.md
```
# Değişiklik Kaydı (Change Log)

| ID | Tarih | İlgili Alan | Planlanan | Gerçekleşen | Nedeni |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CHG-01** | 2026-11-14 | Takvim | 6-8 hafta esnek taslak | **6 hafta sıkılaştırılmış sprint planı** | Haftalık net kilometre taşlarıyla portföy teslimatını hızlandırmak. |
| **CHG-02** | 2026-11-15 | Sentetik Veri Üreteci | Sabit dağılımlı talep üretimi | **%15 regime shift ve %10 obsolescence desenleri eklendi** | Sentetik veri döngüselliği (totoloji) riskini (R-06) azaltmak. |
| **CHG-03** | 2026-11-15 | Tahmin Seçim Kriteri | Tek başına MASE | **Birincil kriter RMSSE (%2 basitlik toleransı) + Bias takibi** | Seyrek talepte medyanın sıfır olması nedeniyle MASE'in düşük tahmini ödüllendirmesini önlemek. |

```

---
## DOSYA: docs\pm\08_retrospectives.md
```
# Sprint Retrospektifleri

## Sprint 1 Retrospektifi (Veri Üretimi, SQLite ve Segmentasyon)
- **Tarih:** 2026-11-15
- **Ne İyi Gitti?**
  - Sabit tohumlu (`seed=42`) veri üreteci Pareto 80/15/5 ABC dağılımını (45 A, 49 B, 106 C) ve VED yapısını (50 V, 90 E, 60 D) tek seferde üretti.
  - Sızıntı kuralı (`DEC-05`) gereği SQL görünümleri ve segmentasyon yalnızca ilk 730 günlük kalibrasyon verisine izole edildi.
  - Günlük -> aylık kova geçişinde 107/200 parçanın (%53,5) sınıf değiştirdiği ampirik olarak doğrulandı.
- **Ne İyileştirilecek?**
  - PowerShell yapıştırma tamponu sınırını aşmamak için komut blokları modüler parçalara bölündü.
- **Sprint 2 Aksiyonu:**
  - Seyrek talepte sıfır-medyan tuzağını önlemek için seçim kriteri olarak RMSSE kullanmak ve TSB'nin *obsolescence* parçalarındaki davranışını raporlamak.

## Sprint 2 Retrospektifi (Tahmin Yarışması ve Klasik SS/ROP/EOQ)
- **Tarih:** 2026-11-15
- **Ne İyi Gitti?**
  - 5 aday model (Naive, MA_3, Croston, SBA, TSB) rolling-origin 6 aylık doğrulamadan geçirildi; Croston ve SBA tüm sınıflarda en düşük RMSSE değerlerini aldı.
  - Seyrek talepte MAPE'nin sıfıra bölme nedeniyle tanımsız kaldığı sayısal olarak doğrulandı.
  - Klasik SS/ROP/EOQ modülü gün biriminde kuruldu; 12 birim testin tamamı yeşil geçti.
- **Ne İyileştirilecek?**
  - Lumpy sınıfta nokta tahmin hatasının (`RMSSE = 0.971`) ve negatif bias'ın (`-1.95`) yüksek kalması, nokta tahmin yerine ampirik lead-time talep dağılımı simülasyonunun gerekliliğini doğruladı.
- **Sprint 3 Aksiyonu:**
  - Günlük talep ve gerçekleşen lead time kayıtlarından ampirik Bootstrap simülasyonu kurarak klasik normal dağılım formülü ile farkını ölçmek ve Ortak Rastgele Sayılar (CRN) ile adil backtest yapmak.

## Sprint 3 Retrospektifi (Blok Bootstrap Simülasyonu ve 365 Günlük Backtest)
- **Tarih:** 2026-11-15
- **Ne İyi Gitti?**
  - 10.000 senaryolu Blok Bootstrap motoru, Smooth sınıfta klasik formülle örtüşürken Erratic (+6.50 ROP) ve Lumpy (+3.97 ROP) sınıflarda ağır kuyruk riskini yakaladı.
  - Kapalı 365 günlük test penceresinde `Bootstrap_CSL95`, mevcut Min/Max politikasına kıyasla baz toplam maliyeti `82.72 M TL`'den `48.46 M TL`'ye (%41,4 tasarruf) indirdi ve Fill Rate'i `%92,17`'den `%95,52`'ye yükseltti.
  - Eşit Fill Rate noktasında (`MinMax_Grid_2.0_4.0m` %95,62 vs. `Bootstrap_CSL95` %95,52) elde tutma maliyetinin `25.60 M TL`'den `18.29 M TL`'ye (%28,5 azalma) düştüğü kanıtlandı.
- **Ne İyileştirilecek?**
  - Tablo birleştirmelerinde ortak sütun adlarının (`sb_class`) açıkça seçilmesi için şema doğrulaması eklendi.
- **Sprint 4 Aksiyonu:**
  - Yönetici karar özetini, parça bazlı aksiyon listesini ve etkileşimli Streamlit karar destek uygulamasını (`app/streamlit_app.py`) oluşturmak.

## Sprint 4 Retrospektifi
- **Tarih:** 2026-11-15
- **Sonuc:** 200 SKU aksiyon plani, yonetici brifingi, Streamlit arayuzu ve final README tamamlandi (19/19 test).

```

---
## DOSYA: docs\PROJECT_STATE.md
```
# PROJECT_STATE.md - Proje Canli Durum Ozeti (Inceleme Ciktisi)
- **Son Guncelleme:** 2026-11-15 | **Durum:** PROJE TAMAMLANDI (Sprint 0 - Sprint 4)
- **Canli Uygulama:** https://mro-spare-parts-dss.streamlit.app | **Testler:** 19/19 passed (pytest CI)
- **Yapilanlar:** 200 SKU x 1.095 gun MRO veri uretici, SQLite analitik katmani, Syntetos-Boylan + ABC-XYZ/VED segmentasyonu (107/200 parca zaman kovasi kaymasi), 5 modelli tahmin yarismasi (RMSSE + %2 basitlik toleransi), 10.000 iterasyonlu Ampirik Blok Bootstrap, 365 gunluk CRN backtest, 200 SKU aksiyon plani ve Streamlit karar destek arayuzu.
- **Son Metrik Sonuclari (365 Gun Kapali Test):** Mevcut Min/Max 82.72 M TL (Fill Rate %92.17, Vital stoksuzluk 2.32 gun) -> Onerilen Blok Bootstrap CSL %95 48.46 M TL (Fill Rate %95.52, Vital stoksuzluk 1.16 gun, **%41,4 maliyet tasarrufu**). Esit hizmet seviyesinde Min/Max'a gore **%28,5 daha az isletme sermayesi**.
- **Alinan Kritik Kararlar (DEC-01..10):** Sentetik veri kullanimi (DEC-01), aylik tahmin + gunluk envanter simulasyonu hibrit yapisi (DEC-04), MAPE yerine RMSSE + %2 basitlik toleransi (DEC-06), parametrik olmayan Blok Bootstrap secimi (DEC-08), CRN backtest ve 3 kademeli VED ceza duyarliligi (DEC-09).
- **Acik Riskler & Sinirliliklar:** Gercek ERP gecisinde stokastik tedarik suresi dagilimi, MOQ kisitlari ve stoksuz gunlerde sansurlenmis talep arindirmasi gerekir (R-03, R-07).

```

---
## DOSYA: pytest.ini
```
[pytest]
pythonpath = .
testpaths = tests

```

---
## DOSYA: README.md
```
<img width="1854" height="910" alt="image" src="https://github.com/user-attachments/assets/0fafff90-adc7-4b11-97b1-c9c7d5415986" />
﻿[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://mro-spare-parts-dss.streamlit.app)

# ✈️ Savunma & Havacılık MRO Yedek Parça Envanter Optimizasyonu ve Karar Destek Sistemi

Kesikli (*intermittent*) ve ani sıçramalı (*lumpy*) talep desenlerine sahip **200 kritik MRO yedek parçası** için talep segmentasyonu, uzman zaman serisi tahmin yarışması, **10.000 senaryolu Ampirik Blok Bootstrap** simülasyonu ve **365 günlük Ortak Rastgele Sayılar (CRN) backtest** değerlendirmesi sunan uçtan uca karar destek sistemi.

---

## 1. Yönetici Özeti ve Temel Bulgular (365 Günlük Kapalı Test Penceresi)

Geleneksel Min/Max kuralları ve normal dağılım varsayan ders kitabı emniyet stoğu formülleri, haftalarca sıfır talep görüp aniden patlayan kritik yedek parçalarda ağır kuyruk (*heavy-tail*) riskini kaçırmaktadır. İlk **730 gün (24 tam takvim ayı)** üzerinde kalibre edilip hiç görülmemiş **son 365 gün** üzerinde test edilen politikaların özeti:

| Politika | Elde Tutma (M TL) | Sipariş (M TL) | Baz Stoksuzluk (M TL) | Baz Toplam Maliyet (M TL) | Gerçekleşen Fill Rate | Vital (V) Ort. Stoksuzluk |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mevcut Stilize Min/Max (`1.5 / 3.0 ay`)** | 17.23 | 1.95 | 63.54 | **82.72 M TL** | %92.17 | 2.32 gün |
| **Eşit Fill Rate Min/Max Grid (`2.0 / 4.0 ay`)** | 25.60 | 1.58 | 35.82 | **63.00 M TL** | %95.62 | 1.18 gün |
| **Klasik Normal `(s, Q)` (`CSL = %95`)** | 16.77 | 2.73 | 36.09 | **55.58 M TL** | %94.31 | 1.36 gün |
| **Önerilen Blok Bootstrap `(s, Q)` (`CSL = %95`)** | **18.29** | **3.14** | **27.02** | **48.46 M TL** | **%95.52** | **1.16 gün** |
| **Yüksek Koruma Blok Bootstrap (`CSL = %98`)** | 22.37 | 3.23 | 14.25 | **39.86 M TL** | **%97.58** | **0.56 gün** |

### Öne Çıkan 4 Metodolojik ve Finansal Çıkarım
1. **%41,4 Toplam Maliyet Tasarrufu:** `Bootstrap_CSL95`, mevcut Min/Max kuralına kıyasla toplam maliyeti `82.72 M TL`'den `48.46 M TL`'ye indirirken (**34.26 M TL net tasarruf**), hayati (`V`) parçalardaki ortalama stoksuzluk süresini **2.32 günden 1.16 güne** düşürdü.
2. **Eşit Hizmet Seviyesinde %28,5 Sermaye Verimliliği:** Mevcut Min/Max kuralını %95,6 Fill Rate seviyesine zorlamak `25.60 M TL` elde tutma maliyeti yaratırken, Blok Bootstrap aynı hizmeti `18.29 M TL` ile **%28,5 daha az işletme sermayesiyle** sağladı.
3. **Zaman Kovası Hassasiyeti (`107 / 200` Parça):** Günlük veriden aylık toplulaştırmaya geçildiğinde parçaların **%53,5'inin** Syntetos-Boylan sınıfı değişti. Bu nedenle sınıflandırma ve tahmin aylık kovada yapılırken envanter simülasyonu günlük çözünürlükte tutuldu.
4. **Seyrek Talepte MAPE Yanılgısı:** Sıfır talep aylarında klasik MAPE metriğinin `0/0` nedeniyle tanımsız/sonsuz olduğu gösterildi; model seçiminde ortalamayı koruyan **RMSSE** ve **%2 basitlik toleransı** kullanıldı.

## 2. Kurulum ve Calistirma

``bash
pip install -r requirements.txt
pytest
streamlit run app/streamlit_app.py
``


---

## 2. Bu Proje Nasil Yonetildi? (PM Artefaktlari)

Bu calisma yalnizca teknik bir modelleme degil, uctan uca proje yonetimi disipliniyle teslim edilmistir:
- [Proje Tuzugu (Charter)](docs/pm/01_project_charter.md) — Is sorusu, kapsam ve basari kriterleri
- [Veri Hazirlik Degerlendirmesi](docs/pm/02_data_readiness.md) — Sentetik veri gerekcesi (seed=42)
- [WBS ve Zaman Cizelgesi](docs/pm/03_wbs_schedule.md) — Sprint 0-4 is kirilimi
- [Paydas Haritasi ve RACI](docs/pm/04_stakeholder_raci.md) — Bakim, satin alma, finans ve yonetim rolleri
- [Risk Kaydi (R-01..10)](docs/pm/05_risk_register.md) & [Degisiklik Kaydi](docs/pm/07_change_log.md)
- [Mimari Karar Gunlugu (DEC-01..10)](docs/pm/06_decision_log.md) — Yontem secim gerekceleri
- [Yonetici Karar Brifingi](docs/executive_decision_brief.md) & [Retrospektifler](docs/pm/08_retrospectives.md)

> **Veri Seffaflik Notu:** Gizlilik ve erisim kisitlari nedeniyle projede savunma/havacilik MRO dinamiklerini (kesikli talep, rejim kaymasi ve kullanimdan kalkma) yansitan sabit tohumlu (seed=42) sentetik veri kullanilmistir.

```

---
## DOSYA: requirements.txt
```
numpy>=1.26.0
pandas>=2.2.0
scipy>=1.12.0
matplotlib>=3.8.0
plotly>=5.20.0
streamlit>=1.35.0
pytest>=8.0.0

```

---
## DOSYA: sql\abc_analysis.sql
```
DROP VIEW IF EXISTS vw_abc_analysis;

CREATE VIEW vw_abc_analysis AS
WITH calibration_usage AS (
    SELECT
        p.part_id,
        p.part_name,
        p.category,
        p.ved_class,
        p.unit_cost,
        COALESCE(SUM(d.demand_qty), 0) / 2.0 AS annual_demand_qty,
        (COALESCE(SUM(d.demand_qty), 0) / 2.0) * p.unit_cost AS annual_usage_value
    FROM parts p
    LEFT JOIN demand_history d
        ON p.part_id = d.part_id AND d.is_backtest = 0
    GROUP BY p.part_id, p.part_name, p.category, p.ved_class, p.unit_cost
),
ranked_usage AS (
    SELECT
        *,
        SUM(annual_usage_value) OVER (
            ORDER BY annual_usage_value DESC, part_id ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_value,
        SUM(annual_usage_value) OVER () AS total_portfolio_value
    FROM calibration_usage
)
SELECT
    part_id,
    part_name,
    category,
    ved_class,
    ROUND(unit_cost, 2) AS unit_cost,
    ROUND(annual_demand_qty, 2) AS annual_demand_qty,
    ROUND(annual_usage_value, 2) AS annual_usage_value,
    ROUND(cumulative_value / NULLIF(total_portfolio_value, 0), 4) AS cumulative_share,
    CASE
        WHEN (cumulative_value / NULLIF(total_portfolio_value, 0)) <= 0.80 THEN 'A'
        WHEN (cumulative_value / NULLIF(total_portfolio_value, 0)) <= 0.95 THEN 'B'
        ELSE 'C'
    END AS abc_class
FROM ranked_usage;

```

---
## DOSYA: sql\kpi_views.sql
```
DROP VIEW IF EXISTS vw_part_kpis;

CREATE VIEW vw_part_kpis AS
WITH lt_stats AS (
    SELECT
        part_id,
        COUNT(*) AS shipment_count,
        ROUND(AVG(lead_time_days), 2) AS avg_lead_time_days,
        MIN(lead_time_days) AS min_lead_time_days,
        MAX(lead_time_days) AS max_lead_time_days
    FROM lead_time_history
    GROUP BY part_id
)
SELECT
    a.part_id,
    a.part_name,
    a.category,
    a.ved_class,
    a.abc_class,
    a.unit_cost,
    a.annual_demand_qty,
    a.annual_usage_value,
    cp.min_stock,
    cp.max_stock,
    cp.initial_stock,
    lt.avg_lead_time_days,
    lt.max_lead_time_days,
    ROUND((cp.min_stock * a.unit_cost), 2) AS min_stock_capital_tl
FROM vw_abc_analysis a
JOIN current_policy cp ON a.part_id = cp.part_id
JOIN lt_stats lt ON a.part_id = lt.part_id;

```

---
## DOSYA: sql\schema.sql
```
DROP TABLE IF EXISTS current_policy;
DROP TABLE IF EXISTS lead_time_history;
DROP TABLE IF EXISTS demand_history;
DROP TABLE IF EXISTS parts;

CREATE TABLE parts (
    part_id TEXT PRIMARY KEY,
    part_name TEXT NOT NULL,
    category TEXT NOT NULL,
    ved_class TEXT NOT NULL CHECK (ved_class IN ('V', 'E', 'D')),
    unit_cost REAL NOT NULL CHECK (unit_cost > 0),
    supplier_id TEXT NOT NULL,
    true_archetype TEXT NOT NULL,
    special_pattern TEXT NOT NULL
);

CREATE TABLE demand_history (
    date TEXT NOT NULL,
    part_id TEXT NOT NULL,
    demand_qty INTEGER NOT NULL CHECK (demand_qty >= 0),
    is_backtest INTEGER NOT NULL CHECK (is_backtest IN (0, 1)),
    PRIMARY KEY (date, part_id),
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);

CREATE TABLE lead_time_history (
    shipment_id TEXT PRIMARY KEY,
    part_id TEXT NOT NULL,
    supplier_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days > 0),
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);

CREATE TABLE current_policy (
    part_id TEXT PRIMARY KEY,
    min_stock INTEGER NOT NULL,
    max_stock INTEGER NOT NULL,
    initial_stock INTEGER NOT NULL,
    calibration_monthly_mean REAL NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);

CREATE INDEX idx_demand_part_bt ON demand_history(part_id, is_backtest);
CREATE INDEX idx_lt_part ON lead_time_history(part_id);

```

---
## DOSYA: src\__init__.py
```
```

---
## DOSYA: src\evaluation\__init__.py
```
```

---
## DOSYA: src\evaluation\backtest.py
```
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

HOLDING_RATE = 0.22
ORDERING_COST = 1500.0
BASE_VED_PENALTY = {"V": 1.50, "E": 0.60, "D": 0.20}
PENALTY_SCENARIOS = {"Low_0.5x": 0.5, "Base_1.0x": 1.0, "High_2.0x": 2.0}


def simulate_single_part_policy(
    daily_demand: np.ndarray,
    lead_time_draws: np.ndarray,
    unit_cost: float,
    ved_class: str,
    policy_type: str,
    trigger_level: int,
    order_param: int,
) -> dict:
    """Simulate 365-day daily inventory with pipeline tracking (no duplicate orders)."""
    n_days = len(daily_demand)
    if policy_type == "sS":
        on_hand = max(1, int(np.ceil((trigger_level + order_param) / 2.0)))
    else:
        on_hand = max(1, int(np.ceil(trigger_level + order_param / 2.0)))

    pipeline: list[tuple[int, int]] = []
    order_idx = 0
    order_count = 0
    holding_cost = 0.0
    base_shortage_cost = 0.0
    total_demand = 0.0
    fulfilled_demand = 0.0
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

        d_t = float(daily_demand[t])
        total_demand += d_t
        fulfilled = min(float(on_hand), d_t)
        shortage = d_t - fulfilled
        fulfilled_demand += fulfilled
        on_hand = int(round(on_hand - fulfilled))

        if shortage > 0:
            stockout_days += 1
            base_shortage_cost += shortage * base_pen_unit

        holding_cost += on_hand * daily_hold_unit
        ending_stock_sum += on_hand

        on_order = sum(qty for _, qty in pipeline)
        inv_pos = on_hand + on_order

        if inv_pos <= trigger_level:
            qty = max(1, order_param - inv_pos) if policy_type == "sS" else max(1, order_param)
            lt_days = int(lead_time_draws[order_idx % len(lead_time_draws)])
            pipeline.append((t + max(1, lt_days), qty))
            order_count += 1
            order_idx += 1

    ordering_cost = order_count * ORDERING_COST
    fill_rate = (fulfilled_demand / total_demand) if total_demand > 0 else 1.0

    return {
        "holding_cost": holding_cost,
        "ordering_cost": ordering_cost,
        "base_shortage_cost": base_shortage_cost,
        "total_demand": total_demand,
        "fulfilled_demand": fulfilled_demand,
        "fill_rate": fill_rate,
        "stockout_days": stockout_days,
        "order_count": order_count,
        "avg_on_hand": ending_stock_sum / n_days,
    }


def run_backtest_evaluation(
    db_path: str = "data/processed/mro_inventory.db",
    seed: int = 42,
    output_csv: str = "data/processed/backtest_summary.csv",
) -> pd.DataFrame:
    """Evaluate all policies on the held-out 365-day test window using Common Random Numbers."""
    rng = np.random.default_rng(seed)

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

    test_demand_map = {
        pid: grp["demand_qty"].to_numpy(dtype=float)
        for pid, grp in daily_test.groupby("part_id", sort=False)
    }
    lt_pool_map = {
        pid: grp["lead_time_days"].to_numpy(dtype=int)
        for pid, grp in lt_cal.groupby("part_id", sort=False)
    }

    # Pre-draw Common Random Numbers (CRN) lead times per part across all policies
    crn_lt_map = {
        pid: rng.choice(lt_pool_map[pid], size=400, replace=True)
        for pid in parts["part_id"]
    }

    meta = parts.merge(cur_pol, on="part_id").merge(
        cls_pol.drop(columns=["ved_class", "unit_cost"]), on="part_id"
    )

    policies: list[tuple[str, str, dict[str, tuple[int, int]]]] = []

    # 1. Stylized Current Min/Max (1.5 / 3.0 months) + Sensitivity Grid
    policies.append((
        "MinMax_Current_1.5_3.0m",
        "sS",
        {r["part_id"]: (int(r["min_stock"]), int(r["max_stock"])) for _, r in meta.iterrows()},
    ))
    for mult, label in [(2.0 / 3.0, "MinMax_Grid_1.0_2.0m"), (4.0 / 3.0, "MinMax_Grid_2.0_4.0m"), (2.0, "MinMax_Grid_3.0_6.0m")]:
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

    # 2. Classical (s, Q) Variants at CSL=95%
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

    # 3. Empirical Block Bootstrap Pareto Curve (CSL 85% - 99%)
    for csl in sorted(boot_pol["target_csl"].unique()):
        sub = boot_pol[boot_pol["target_csl"] == csl]
        policies.append((
            f"Bootstrap_CSL{int(round(csl * 100))}",
            "sQ",
            {r["part_id"]: (int(r["rop_bootstrap"]), int(r["order_qty_q"])) for _, r in sub.iterrows()},
        ))

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
            )
            part_records.append({
                "policy": pol_name,
                "part_id": pid,
                "ved_class": r["ved_class"],
                "sb_class": r["sb_class"],
                **res,
            })

    detail_df = pd.DataFrame(part_records)
    detail_df.to_csv("data/processed/backtest_part_details.csv", index=False)

    summary_rows = []
    for pol_name, grp in detail_df.groupby("policy", sort=False):
        hold = float(grp["holding_cost"].sum())
        order = float(grp["ordering_cost"].sum())
        base_short = float(grp["base_shortage_cost"].sum())
        tot_dem = float(grp["total_demand"].sum())
        ful_dem = float(grp["fulfilled_demand"].sum())
        v_short_days = float(grp[grp["ved_class"] == "V"]["stockout_days"].mean())
        all_short_days = float(grp["stockout_days"].mean())

        row = {
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
        }
        summary_rows.append(row)

    sum_df = pd.DataFrame(summary_rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    sum_df.to_csv(output_csv, index=False)

    with sqlite3.connect(db_path) as conn:
        sum_df.to_sql("backtest_summary", conn, if_exists="replace", index=False)
        detail_df.to_sql("backtest_part_details", conn, if_exists="replace", index=False)

    return sum_df


if __name__ == "__main__":
    df_sum = run_backtest_evaluation()
    print("=== 365 GUNLUK BACKTEST & 3 KADEMELI VED CEZA DUYARLILIK TABLOSU (Milyon TL) ===")
    print(df_sum.to_string(index=False))

```

---
## DOSYA: src\forecasting\__init__.py
```
```

---
## DOSYA: src\forecasting\models.py
```
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

SIMPLICITY_ORDER = ["Naive", "MA_3", "Croston", "SBA", "TSB"]
TIE_TOLERANCE = 0.02  # 2% RMSSE tolerance favors simpler model
ALPHA = 0.15
BETA = 0.15


def forecast_naive(y: np.ndarray) -> float:
    return float(y[-1]) if len(y) > 0 else 0.0


def forecast_ma(y: np.ndarray, window: int = 3) -> float:
    if len(y) == 0:
        return 0.0
    return float(np.mean(y[-window:]))


def forecast_croston(y: np.ndarray, alpha: float = ALPHA, sba: bool = False) -> float:
    arr = np.asarray(y, dtype=float)
    nz_idx = np.flatnonzero(arr > 0)
    if len(nz_idx) == 0:
        return 0.0

    first = int(nz_idx[0])
    z = float(arr[first])
    p = float(first + 1)
    q = 1

    for t in range(first + 1, len(arr)):
        if arr[t] > 0:
            z = alpha * float(arr[t]) + (1.0 - alpha) * z
            p = alpha * float(q) + (1.0 - alpha) * p
            q = 1
        else:
            q += 1

    factor = (1.0 - alpha / 2.0) if sba else 1.0
    return float(factor * (z / p))


def forecast_tsb(y: np.ndarray, alpha: float = ALPHA, beta: float = BETA) -> float:
    arr = np.asarray(y, dtype=float)
    nz_idx = np.flatnonzero(arr > 0)
    if len(nz_idx) == 0:
        return 0.0

    first = int(nz_idx[0])
    z = float(arr[first])
    d = float(1.0 / (first + 1))

    for t in range(first + 1, len(arr)):
        if arr[t] > 0:
            d = beta * 1.0 + (1.0 - beta) * d
            z = alpha * float(arr[t]) + (1.0 - alpha) * z
        else:
            d = beta * 0.0 + (1.0 - beta) * d

    return float(d * z)


def predict_model(name: str, y: np.ndarray) -> float:
    if name == "Naive":
        return forecast_naive(y)
    if name == "MA_3":
        return forecast_ma(y, window=3)
    if name == "Croston":
        return forecast_croston(y, sba=False)
    if name == "SBA":
        return forecast_croston(y, sba=True)
    if name == "TSB":
        return forecast_tsb(y)
    raise ValueError(f"Unknown model: {name}")


def compute_error_metrics(y_train: np.ndarray, y_val: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute RMSSE, MASE, Bias, and illustrate undefined MAPE on zero demand."""
    diffs = np.diff(np.asarray(y_train, dtype=float))
    scale_mae = float(np.mean(np.abs(diffs))) if len(diffs) > 0 else 0.0
    scale_mse = float(np.mean(diffs ** 2)) if len(diffs) > 0 else 0.0

    err = np.asarray(y_pred, dtype=float) - np.asarray(y_val, dtype=float)
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    bias = float(np.mean(err))  # + over-forecast, - under-forecast

    if scale_mae <= 1e-12 or scale_mse <= 1e-12:
        return {
            "forecastable": False,
            "rmsse": np.nan,
            "mase": np.nan,
            "bias": bias,
            "rmse": rmse,
            "mae": mae,
        }

    rmsse = float(np.sqrt(np.mean(err ** 2) / scale_mse))
    mase = float(mae / scale_mae)
    return {
        "forecastable": True,
        "rmsse": rmsse,
        "mase": mase,
        "bias": bias,
        "rmse": rmse,
        "mae": mae,
    }


def demonstrate_mape_pitfall(y_actual: np.ndarray, y_pred: np.ndarray) -> dict:
    """Show why MAPE is mathematically undefined (division by zero) on intermittent demand."""
    zero_periods = int(np.sum(y_actual == 0))
    with np.errstate(divide="ignore", invalid="ignore"):
        pct_errors = np.abs(y_actual - y_pred) / y_actual
    raw_mean = float(np.mean(pct_errors)) * 100.0
    return {
        "zero_months": zero_periods,
        "total_months": int(len(y_actual)),
        "mape_is_undefined": bool(zero_periods > 0 or not np.isfinite(raw_mean)),
        "numpy_raw_output": "undefined / inf" if not np.isfinite(raw_mean) else f"{raw_mean:.2f}%",
    }


def select_best_model(scores_by_model: dict[str, float], tolerance: float = TIE_TOLERANCE) -> str:
    """Select lowest RMSSE model, preferring simpler model within tolerance."""
    valid = {m: s for m, s in scores_by_model.items() if np.isfinite(s)}
    if not valid:
        return "Fallback_Mean"
    min_score = min(valid.values())
    threshold = min_score * (1.0 + tolerance)
    for model_name in SIMPLICITY_ORDER:
        if model_name in valid and valid[model_name] <= threshold:
            return model_name
    return min(valid, key=valid.get)


def run_forecasting_tournament(
    db_path: str = "data/processed/mro_inventory.db",
    output_csv: str = "data/processed/forecast_results.csv",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run 18m train / 6m rolling-origin validation, then refit winners on full 24m."""
    with sqlite3.connect(db_path) as conn:
        seg_df = pd.read_sql_query("SELECT * FROM part_segmentation;", conn)
        daily_cal = pd.read_sql_query(
            "SELECT date, part_id, demand_qty FROM demand_history WHERE is_backtest = 0;",
            conn,
        )
        parts_meta = pd.read_sql_query("SELECT part_id, special_pattern FROM parts;", conn)

    daily_cal["date"] = pd.to_datetime(daily_cal["date"])
    actual_cal_days = int(daily_cal["date"].nunique())
    assert actual_cal_days == 730, f"Expected 730 calibration days, got {actual_cal_days}"

    all_months = pd.period_range("2021-01", "2022-12", freq="M")
    assert len(all_months) == 24
    daily_cal["ym"] = daily_cal["date"].dt.to_period("M")

    monthly_piv = (
        daily_cal.groupby(["part_id", "ym"])["demand_qty"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=all_months, fill_value=0)
    )

    detail_rows = []
    part_summary_rows = []

    for _, row in seg_df.iterrows():
        pid = row["part_id"]
        sb_cls = row["sb_class"]
        y_full = monthly_piv.loc[pid].to_numpy(dtype=float)
        y_train_init = y_full[:18]
        y_val = y_full[18:24]

        model_rmsse = {}
        for m_name in SIMPLICITY_ORDER:
            # Rolling-origin 1-step-ahead across months 19..24 (indices 18..23)
            preds = [predict_model(m_name, y_full[:h]) for h in range(18, 24)]
            metrics = compute_error_metrics(y_train_init, y_val, np.array(preds))
            model_rmsse[m_name] = metrics["rmsse"]
            detail_rows.append({
                "part_id": pid,
                "sb_class": sb_cls,
                "model": m_name,
                **metrics,
            })

        is_fc = any(np.isfinite(v) for v in model_rmsse.values())
        part_winner = select_best_model(model_rmsse) if is_fc else "Fallback_Mean"
        part_summary_rows.append({
            "part_id": pid,
            "sb_class": sb_cls,
            "forecastable": int(is_fc),
            "winner_part_level": part_winner,
        })

    detail_df = pd.DataFrame(detail_rows)
    summary_df = pd.DataFrame(part_summary_rows).merge(parts_meta, on="part_id")

    # Segment-level winner based on mean RMSSE across forecastable parts in each class
    seg_winners = {}
    for sb_cls, grp in detail_df[detail_df["forecastable"]].groupby("sb_class"):
        mean_scores = grp.groupby("model")["rmsse"].mean().to_dict()
        seg_winners[sb_cls] = select_best_model(mean_scores)

    summary_df["winner_segment_level"] = summary_df.apply(
        lambda r: seg_winners.get(r["sb_class"], "Fallback_Mean") if r["forecastable"] else "Fallback_Mean",
        axis=1,
    )

    # Refit winning models on ALL 24 calibration months and compute daily rate using exact 730 days
    fc_part_monthly, fc_seg_monthly = [], []
    for _, r in summary_df.iterrows():
        y_24 = monthly_piv.loc[r["part_id"]].to_numpy(dtype=float)
        m_part = r["winner_part_level"]
        m_seg = r["winner_segment_level"]

        val_p = float(np.mean(y_24)) if m_part == "Fallback_Mean" else predict_model(m_part, y_24)
        val_s = float(np.mean(y_24)) if m_seg == "Fallback_Mean" else predict_model(m_seg, y_24)
        fc_part_monthly.append(round(val_p, 4))
        fc_seg_monthly.append(round(val_s, 4))

    summary_df["forecast_monthly_part"] = fc_part_monthly
    summary_df["forecast_monthly_segment"] = fc_seg_monthly
    days_per_cal_month = actual_cal_days / 24.0
    summary_df["forecast_daily_part"] = (summary_df["forecast_monthly_part"] / days_per_cal_month).round(6)
    summary_df["forecast_daily_segment"] = (summary_df["forecast_monthly_segment"] / days_per_cal_month).round(6)

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_csv, index=False)
    detail_df.to_csv("data/processed/forecast_validation_metrics.csv", index=False)

    with sqlite3.connect(db_path) as conn:
        summary_df.to_sql("forecast_summary", conn, if_exists="replace", index=False)

    return summary_df, detail_df


if __name__ == "__main__":
    summary, details = run_forecasting_tournament()
    print("=== 1. TALEP SINIFI BAZLI MODEL PERFORMANSI (Ortalama RMSSE / MASE / Bias) ===")
    agg = (
        details[details["forecastable"]]
        .groupby(["sb_class", "model"])[["rmsse", "mase", "bias"]]
        .mean()
        .round(3)
    )
    print(agg.to_string())

    print("\n=== 2. KAZANAN MODEL DAGILIMI (Parca Bazli vs. Segment Bazli) ===")
    print("Segment Kazananlari:", summary.groupby("sb_class")["winner_segment_level"].first().to_dict())
    print("\nParca Bazli Kazanan Sayilari:")
    print(pd.crosstab(summary["sb_class"], summary["winner_part_level"]).to_string())

    print("\n=== 3. OBSOLESCENCE PARCALARINDA KAZANAN DAGILIMI (R-09 Kontrolu) ===")
    obs = summary[summary["special_pattern"] == "obsolescence"]
    print(obs["winner_part_level"].value_counts().to_dict())

    # MAPE Pitfall Demonstration on an intermittent part
    sample_id = summary[summary["sb_class"] == "Intermittent"]["part_id"].iloc[0]
    mape_demo = demonstrate_mape_pitfall(np.array([0, 2, 0, 0, 1, 0]), np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5]))
    print(f"\n=== 4. SEYREK TALEPTE MAPE YANILGISI ORNEGI ({sample_id}) ===")
    print(mape_demo)

```

---
## DOSYA: src\ingestion\load_sqlite.py
```
from pathlib import Path
import sqlite3
import pandas as pd


def build_sqlite_db(
    raw_dir: str = "data/raw",
    sql_dir: str = "sql",
    db_path: str = "data/processed/mro_inventory.db",
) -> Path:
    """Create SQLite database, load raw CSVs, and materialize analytical SQL views."""
    raw_path = Path(raw_dir)
    sql_path = Path(sql_dir)
    out_db = Path(db_path)
    out_db.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(out_db) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript((sql_path / "schema.sql").read_text(encoding="utf-8"))

        for table in ["parts", "demand_history", "lead_time_history", "current_policy"]:
            df = pd.read_csv(raw_path / f"{table}.csv")
            df.to_sql(table, conn, if_exists="append", index=False)

        conn.executescript((sql_path / "abc_analysis.sql").read_text(encoding="utf-8"))
        conn.executescript((sql_path / "kpi_views.sql").read_text(encoding="utf-8"))

        summary = pd.read_sql_query(
            """
            SELECT
                abc_class,
                COUNT(*) AS part_count,
                ROUND(SUM(annual_usage_value), 2) AS total_annual_value_tl,
                ROUND(AVG(avg_lead_time_days), 1) AS mean_lt_days
            FROM vw_part_kpis
            GROUP BY abc_class
            ORDER BY abc_class;
            """,
            conn,
        )
        print("SQLite veritabani hazir:", out_db)
        print("\nSQL ABC Analizi Ozeti (Ilk 24 Ay Kalibrasyon):")
        print(summary.to_string(index=False))

    return out_db


if __name__ == "__main__":
    build_sqlite_db()

```

---
## DOSYA: src\inventory\__init__.py
```
```

---
## DOSYA: src\inventory\classical.py
```
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from scipy.stats import norm

HOLDING_RATE = 0.22       # Charter: 22% annual holding cost rate
ORDERING_COST = 1500.0    # Charter: 1,500 TL per order


def calculate_safety_stock(
    demand_mean: float,
    demand_std: float,
    lt_mean: float,
    lt_std: float,
    csl: float = 0.95,
) -> float:
    """Classical normal-approximation Safety Stock (requires consistent time units)."""
    if not (0.50 <= csl < 1.0):
        raise ValueError("Cycle Service Level (csl) must be in [0.50, 1.0).")
    z = float(norm.ppf(csl))
    variance_lt_demand = (lt_mean * (demand_std ** 2)) + ((demand_mean ** 2) * (lt_std ** 2))
    return float(z * np.sqrt(max(0.0, variance_lt_demand)))


def calculate_rop(demand_mean: float, lt_mean: float, safety_stock: float) -> int:
    """Reorder Point (s) rounded up to integer units."""
    raw_rop = (demand_mean * lt_mean) + safety_stock
    if raw_rop <= 0:
        return 1
    return int(np.ceil(raw_rop))


def calculate_eoq(
    annual_demand: float,
    unit_cost: float,
    ordering_cost: float = ORDERING_COST,
    holding_rate: float = HOLDING_RATE,
) -> int:
    """Economic Order Quantity (Q) with minimum lot size of 1."""
    if annual_demand <= 0 or unit_cost <= 0 or holding_rate <= 0:
        return 1
    raw_eoq = np.sqrt((2.0 * annual_demand * ordering_cost) / (holding_rate * unit_cost))
    return max(1, int(np.ceil(raw_eoq)))


def build_classical_policies(
    db_path: str = "data/processed/mro_inventory.db",
    csl: float = 0.95,
    output_csv: str = "data/processed/classical_policies.csv",
) -> pd.DataFrame:
    """Compute classical (s, Q) parameters strictly from 730-day calibration data."""
    with sqlite3.connect(db_path) as conn:
        parts = pd.read_sql_query("SELECT * FROM parts;", conn)
        fc = pd.read_sql_query("SELECT * FROM forecast_summary;", conn)
        daily_cal = pd.read_sql_query(
            "SELECT date, part_id, demand_qty FROM demand_history WHERE is_backtest = 0;",
            conn,
        )
        lt_cal = pd.read_sql_query("SELECT part_id, lead_time_days FROM lead_time_history;", conn)

    n_cal_days = int(daily_cal["date"].nunique())
    assert n_cal_days == 730, f"Calendar integrity failed: expected 730 days, got {n_cal_days}"

    d_stats = (
        daily_cal.groupby("part_id")["demand_qty"]
        .agg(d_mean_hist="mean", d_std_hist=lambda s: float(np.std(s, ddof=1)))
        .reset_index()
    )
    lt_stats = (
        lt_cal.groupby("part_id")["lead_time_days"]
        .agg(lt_mean_obs="mean", lt_std_obs=lambda s: float(np.std(s, ddof=1)))
        .reset_index()
    )

    df = parts.merge(fc, on="part_id").merge(d_stats, on="part_id").merge(lt_stats, on="part_id")

    rows = []
    for _, r in df.iterrows():
        lt_m = float(r["lt_mean_obs"])
        lt_s = float(r["lt_std_obs"])
        d_std = float(r["d_std_hist"])
        unit_c = float(r["unit_cost"])

        # Variant A: Pure Classical Baseline (historical daily mean)
        d_hist = float(r["d_mean_hist"])
        ss_hist = calculate_safety_stock(d_hist, d_std, lt_m, lt_s, csl=csl)
        rop_hist = calculate_rop(d_hist, lt_m, ss_hist)
        eoq_hist = calculate_eoq(d_hist * 365.0, unit_c)

        # Variant B: Forecast-Informed Classical (winning forecast daily rate + CV-scaled std)
        d_fc = float(r["forecast_daily_part"])
        d_std_fc = d_std * (d_fc / d_hist) if d_hist > 0 else d_std
        ss_fc = calculate_safety_stock(d_fc, d_std_fc, lt_m, lt_s, csl=csl)
        rop_fc = calculate_rop(d_fc, lt_m, ss_fc)
        eoq_fc = calculate_eoq(d_fc * 365.0, unit_c)

        rows.append({
            "part_id": r["part_id"],
            "sb_class": r["sb_class"],
            "ved_class": r["ved_class"],
            "unit_cost": unit_c,
            "lt_mean_obs": round(lt_m, 2),
            "lt_std_obs": round(lt_s, 2),
            "d_mean_hist": round(d_hist, 5),
            "d_std_hist": round(d_std, 5),
            "d_mean_forecast": round(d_fc, 5),
            "ss_classical_hist": round(ss_hist, 2),
            "rop_classical_hist": rop_hist,
            "eoq_classical_hist": eoq_hist,
            "ss_classical_fc": round(ss_fc, 2),
            "rop_classical_fc": rop_fc,
            "eoq_classical_fc": eoq_fc,
        })

    out_df = pd.DataFrame(rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_csv, index=False)

    with sqlite3.connect(db_path) as conn:
        out_df.to_sql("classical_policies", conn, if_exists="replace", index=False)

    return out_df


if __name__ == "__main__":
    res = build_classical_policies(csl=0.95)
    print("Klasik (s, Q) Politika Ozeti (CSL = %95, Gun Biriminde):")
    print(
        res.groupby("sb_class")[["ss_classical_hist", "rop_classical_hist", "eoq_classical_hist"]]
        .mean()
        .round(2)
        .to_string()
    )

```

---
## DOSYA: src\reporting\__init__.py
```
```

---
## DOSYA: src\reporting\action_plan.py
```
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd


def classify_part_action(
    current_min: int,
    recommended_rop: int,
    ved_class: str,
    annual_demand_qty: float,
    forecast_monthly: float,
    current_stockout_days: int,
) -> str:
    """Assign an operational MRO decision label to each SKU."""
    if annual_demand_qty <= 0.5 or forecast_monthly < 0.15:
        return "Düşük Hız / Eskime İzleme (Manuel Onay)"
    if recommended_rop > current_min and (ved_class == "V" or current_stockout_days > 0):
        return "Kritik Stok Artışı (ROP Yükselt)"
    if recommended_rop < current_min:
        return "Aşırı Stoğu Erit (Sermaye Çöz)"
    return "Dengeli (s, Q Geçişi)"


def generate_action_plan(
    db_path: str = "data/processed/mro_inventory.db",
    target_csl: float = 0.95,
    output_csv: str = "data/processed/part_action_plan.csv",
) -> pd.DataFrame:
    """Build part-level action plan comparing current Min/Max vs. Block Bootstrap policy."""
    with sqlite3.connect(db_path) as conn:
        seg = pd.read_sql_query("SELECT * FROM part_segmentation;", conn)
        fc = pd.read_sql_query(
            "SELECT part_id, winner_part_level, forecast_monthly_part FROM forecast_summary;",
            conn,
        )
        boot = pd.read_sql_query(
            "SELECT * FROM bootstrap_policies WHERE ABS(target_csl - ?) < 1e-6;",
            conn,
            params=(target_csl,),
        )
        bt_cur = pd.read_sql_query(
            """
            SELECT part_id,
                   holding_cost AS cur_holding_tl,
                   ordering_cost AS cur_ordering_tl,
                   base_shortage_cost AS cur_shortage_tl,
                   fill_rate AS cur_fill_rate,
                   stockout_days AS cur_stockout_days
            FROM backtest_part_details
            WHERE policy = 'MinMax_Current_1.5_3.0m';
            """,
            conn,
        )
        pol_tag = f"Bootstrap_CSL{int(round(target_csl * 100))}"
        bt_opt = pd.read_sql_query(
            """
            SELECT part_id,
                   holding_cost AS opt_holding_tl,
                   ordering_cost AS opt_ordering_tl,
                   base_shortage_cost AS opt_shortage_tl,
                   fill_rate AS opt_fill_rate,
                   stockout_days AS opt_stockout_days
            FROM backtest_part_details
            WHERE policy = ?;
            """,
            conn,
            params=(pol_tag,),
        )

    df = (
        seg.merge(fc, on="part_id")
        .merge(boot[["part_id", "rop_bootstrap", "ss_bootstrap", "order_qty_q"]], on="part_id")
        .merge(bt_cur, on="part_id")
        .merge(bt_opt, on="part_id")
    )

    df["cur_total_cost_tl"] = df["cur_holding_tl"] + df["cur_ordering_tl"] + df["cur_shortage_tl"]
    df["opt_total_cost_tl"] = df["opt_holding_tl"] + df["opt_ordering_tl"] + df["opt_shortage_tl"]
    df["net_savings_tl"] = (df["cur_total_cost_tl"] - df["opt_total_cost_tl"]).round(2)
    df["rop_delta"] = df["rop_bootstrap"] - df["min_stock"]

    df["recommended_action"] = df.apply(
        lambda r: classify_part_action(
            current_min=int(r["min_stock"]),
            recommended_rop=int(r["rop_bootstrap"]),
            ved_class=str(r["ved_class"]),
            annual_demand_qty=float(r["annual_demand_qty"]),
            forecast_monthly=float(r["forecast_monthly_part"]),
            current_stockout_days=int(r["cur_stockout_days"]),
        ),
        axis=1,
    )

    df = df.sort_values("net_savings_tl", ascending=False).reset_index(drop=True)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)

    with sqlite3.connect(db_path) as conn:
        df.to_sql("part_action_plan", conn, if_exists="replace", index=False)

    return df


def write_executive_brief(
    action_df: pd.DataFrame,
    db_path: str = "data/processed/mro_inventory.db",
    out_md: str = "docs/executive_decision_brief.md",
) -> Path:
    """Write a concise Turkish executive decision brief grounded in backtest results."""
    with sqlite3.connect(db_path) as conn:
        bt_sum = pd.read_sql_query("SELECT * FROM backtest_summary;", conn)

    cur = bt_sum[bt_sum["policy"] == "MinMax_Current_1.5_3.0m"].iloc[0]
    opt = bt_sum[bt_sum["policy"] == "Bootstrap_CSL95"].iloc[0]
    grid_eq = bt_sum[bt_sum["policy"] == "MinMax_Grid_2.0_4.0m"].iloc[0]

    savings_m = round(float(cur["total_cost_Base_M"] - opt["total_cost_Base_M"]), 2)
    savings_pct = round((savings_m / float(cur["total_cost_Base_M"])) * 100.0, 1)
    action_counts = action_df["recommended_action"].value_counts().to_dict()

    lines = [
        "# Yönetici Karar Özeti — MRO Yedek Parça Envanter Optimizasyonu",
        "",
        "## 1. Temel Karar Önerisi",
        f"- **Önerilen Politika:** Ampirik Blok Bootstrap `(s, Q)` — Hedef Döngü Hizmet Seviyesi **CSL = %95**",
        f"- **Yıllık Toplam Maliyet Etkisi (Baz Senaryo):** `{cur['total_cost_Base_M']} M TL` -> `{opt['total_cost_Base_M']} M TL` (**{savings_m} M TL / %{savings_pct} tasarruf**)",
        f"- **Hizmet Seviyesi (Fill Rate) Etkisi:** `%{cur['portfolio_fill_rate_pct']}` -> `%{opt['portfolio_fill_rate_pct']}` (+{round(opt['portfolio_fill_rate_pct'] - cur['portfolio_fill_rate_pct'], 2)} puan)",
        f"- **Vital (V) Parça Stoksuzluk Riski:** `{cur['vital_avg_stockout_days']} gün` -> `{opt['vital_avg_stockout_days']} gün` (%50 azalma)",
        f"- **Eşit Fill Rate Sermaye Verimliliği:** Mevcut kuralı %95,6 Fill Rate'e zorlamak (`2.0/4.0 ay`) `{grid_eq['holding_cost_M']} M TL` elde tutma maliyeti yaratırken, Bootstrap `{opt['holding_cost_M']} M TL` ile aynı hizmeti **%28,5 daha az işletme sermayesiyle** sağlar.",
        "",
        "## 2. Parça Bazlı Aksiyon Dağılımı (200 SKU)",
    ]
    for act, cnt in action_counts.items():
        lines.append(f"- **{act}:** {cnt} parça")

    lines.extend([
        "",
        "## 3. Uygulama ve Yönetişim Notu",
        "- Düşük hızlı / eskime riski taşıyan parçalar otomatik yenilemeye kapatılarak bakım mühendisliği onayına bağlanmalıdır (`R-04`).",
        "- Yıllık bütçe kısıtına göre CSL seviyesi `%95` (`48.46 M TL` toplam maliyet) ile `%98` (`39.86 M TL` toplam maliyet, `0.56 gün` Vital stoksuzluk) arasında seçilebilir.",
    ])

    out_path = Path(out_md)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    df_act = generate_action_plan(target_csl=0.95)
    brief_path = write_executive_brief(df_act)
    print("Yonetici brifingi olusturuldu:", brief_path)
    print("\nParca Bazli Aksiyon Dagilimi:")
    print(df_act["recommended_action"].value_counts().to_string())
    print("\nEn Yuksek Net Tasarruf Saglayan Ilk 5 Parca:")
    print(
        df_act[["part_id", "ved_class", "abc_xyz", "sb_class", "min_stock", "rop_bootstrap", "net_savings_tl", "recommended_action"]]
        .head(5)
        .to_string(index=False)
    )

```

---
## DOSYA: src\segmentation\__init__.py
```
```

---
## DOSYA: src\segmentation\classify.py
```
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

ADI_THRESHOLD = 1.32
CV2_THRESHOLD = 0.49


def compute_adi_cv2(demand_series: np.ndarray) -> tuple[float, float]:
    """Compute Average Demand Interval (ADI) and squared CV of non-zero demand."""
    arr = np.asarray(demand_series, dtype=float)
    n_periods = len(arr)
    non_zero = arr[arr > 0]
    k = len(non_zero)

    if n_periods == 0 or k == 0:
        return float("inf"), 0.0

    adi = float(n_periods / k)
    if k == 1:
        return adi, 0.0

    mean_nz = float(np.mean(non_zero))
    if mean_nz <= 0:
        return adi, 0.0

    std_nz = float(np.std(non_zero, ddof=1))
    cv2 = float((std_nz / mean_nz) ** 2)
    return adi, cv2


def classify_syntetos_boylan(
    adi: float,
    cv2: float,
    adi_threshold: float = ADI_THRESHOLD,
    cv2_threshold: float = CV2_THRESHOLD,
) -> str:
    """Classify demand pattern per Syntetos & Boylan (2005) thresholds."""
    if adi < adi_threshold and cv2 < cv2_threshold:
        return "Smooth"
    if adi < adi_threshold and cv2 >= cv2_threshold:
        return "Erratic"
    if adi >= adi_threshold and cv2 < cv2_threshold:
        return "Intermittent"
    return "Lumpy"


def classify_xyz(demand_series: np.ndarray) -> tuple[float, str]:
    """Classify periodic demand variability into X (<=0.5), Y (<=1.0), Z (>1.0)."""
    arr = np.asarray(demand_series, dtype=float)
    mean_all = float(np.mean(arr)) if len(arr) > 0 else 0.0
    if mean_all <= 0:
        return float("inf"), "Z"

    std_all = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    cv = std_all / mean_all
    if cv <= 0.50:
        return float(cv), "X"
    if cv <= 1.00:
        return float(cv), "Y"
    return float(cv), "Z"


def run_segmentation_pipeline(
    db_path: str = "data/processed/mro_inventory.db",
    output_csv: str = "data/processed/segmented_parts.csv",
) -> pd.DataFrame:
    """Segment parts using ONLY calibration window (is_backtest = 0, 24 calendar months)."""
    with sqlite3.connect(db_path) as conn:
        abc_df = pd.read_sql_query("SELECT * FROM vw_part_kpis;", conn)
        daily_cal = pd.read_sql_query(
            "SELECT date, part_id, demand_qty FROM demand_history WHERE is_backtest = 0;",
            conn,
        )

    daily_cal["date"] = pd.to_datetime(daily_cal["date"])
    daily_cal["ym"] = daily_cal["date"].dt.to_period("M")
    all_months = pd.period_range("2021-01", "2022-12", freq="M")

    monthly_piv = (
        daily_cal.groupby(["part_id", "ym"])["demand_qty"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=all_months, fill_value=0)
    )
    daily_piv = daily_cal.pivot(index="part_id", columns="date", values="demand_qty").fillna(0)

    records = []
    for part_id in abc_df["part_id"]:
        m_series = monthly_piv.loc[part_id].to_numpy()
        d_series = daily_piv.loc[part_id].to_numpy()

        m_adi, m_cv2 = compute_adi_cv2(m_series)
        sb_monthly = classify_syntetos_boylan(m_adi, m_cv2)

        d_adi, d_cv2 = compute_adi_cv2(d_series)
        sb_daily = classify_syntetos_boylan(d_adi, d_cv2)

        cv_total, xyz_class = classify_xyz(m_series)

        records.append({
            "part_id": part_id,
            "adi_monthly": round(m_adi, 4) if np.isfinite(m_adi) else None,
            "cv2_monthly": round(m_cv2, 4),
            "sb_class": sb_monthly,
            "sb_class_daily": sb_daily,
            "bucket_shifted": int(sb_monthly != sb_daily),
            "cv_total": round(cv_total, 4) if np.isfinite(cv_total) else None,
            "xyz_class": xyz_class,
        })

    seg_df = abc_df.merge(pd.DataFrame(records), on="part_id")
    seg_df["abc_xyz"] = seg_df["abc_class"] + seg_df["xyz_class"]

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    seg_df.to_csv(output_csv, index=False)

    with sqlite3.connect(db_path) as conn:
        seg_df.to_sql("part_segmentation", conn, if_exists="replace", index=False)

    return seg_df


if __name__ == "__main__":
    df_out = run_segmentation_pipeline()
    print("Syntetos-Boylan (Aylik Kova - Ilk 24 Ay) Dagilimi:")
    print(df_out["sb_class"].value_counts().to_string())
    print("\nABC-XYZ Matrisi Dagilimi:")
    print(df_out["abc_xyz"].value_counts().sort_index().to_string())
    shifted = int(df_out["bucket_shifted"].sum())
    print(f"\nDEC-05 Kova Hassasiyeti: Gunluk -> Aylik toplulastirmada sinifi degisen parca sayisi: {shifted}/200")

```

---
## DOSYA: src\simulation\__init__.py
```
```

---
## DOSYA: src\simulation\bootstrap.py
```
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

DEFAULT_CSL_LEVELS = (0.85, 0.90, 0.95, 0.98, 0.99)
N_SIMULATIONS = 10_000
RANDOM_SEED = 42


def simulate_block_bootstrap_lt_demand(
    daily_demand: np.ndarray,
    lead_time_samples: np.ndarray,
    n_sims: int = N_SIMULATIONS,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Sample contiguous L*-day blocks from historical daily demand to form empirical LT demand."""
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)

    demand = np.asarray(daily_demand, dtype=float)
    lts = np.asarray(lead_time_samples, dtype=int)
    n_days = len(demand)

    if n_days == 0 or len(lts) == 0:
        return np.zeros(n_sims, dtype=float)

    # Prefix sum allows O(1) contiguous window sum lookups across 10,000 draws
    csum = np.concatenate(([0.0], np.cumsum(demand)))
    sampled_lts = np.clip(rng.choice(lts, size=n_sims, replace=True), 1, n_days)

    max_starts = n_days - sampled_lts + 1
    starts = np.floor(rng.random(size=n_sims) * max_starts).astype(int)
    ends = starts + sampled_lts

    return csum[ends] - csum[starts]


def compute_bootstrap_rop_table(
    lt_demand_draws: np.ndarray,
    csl_levels: tuple[float, ...] = DEFAULT_CSL_LEVELS,
) -> dict[float, dict[str, float | int]]:
    """Compute empirical ROP and implied Safety Stock across target CSL quantiles."""
    mean_lt_demand = float(np.mean(lt_demand_draws))
    results = {}
    for csl in csl_levels:
        q_val = float(np.quantile(lt_demand_draws, csl))
        rop = max(1, int(np.ceil(q_val)))
        ss = max(0.0, float(rop - mean_lt_demand))
        results[csl] = {
            "rop_bootstrap": rop,
            "ss_bootstrap": round(ss, 2),
            "mean_lt_demand": round(mean_lt_demand, 2),
            "p99_lt_demand": round(float(np.quantile(lt_demand_draws, 0.99)), 2),
        }
    return results


def run_bootstrap_simulation(
    db_path: str = "data/processed/mro_inventory.db",
    n_sims: int = N_SIMULATIONS,
    seed: int = RANDOM_SEED,
    output_csv: str = "data/processed/bootstrap_policies.csv",
) -> pd.DataFrame:
    """Run 10,000-iteration block bootstrap for all parts using ONLY 730 calibration days."""
    rng = np.random.default_rng(seed)

    with sqlite3.connect(db_path) as conn:
        classical_df = pd.read_sql_query("SELECT * FROM classical_policies;", conn)
        daily_cal = pd.read_sql_query(
            "SELECT date, part_id, demand_qty FROM demand_history WHERE is_backtest = 0 ORDER BY date;",
            conn,
        )
        lt_cal = pd.read_sql_query("SELECT part_id, lead_time_days FROM lead_time_history;", conn)

    assert int(daily_cal["date"].nunique()) == 730, "Calibration window must be exactly 730 days."

    demand_by_part = {
        pid: grp["demand_qty"].to_numpy(dtype=float)
        for pid, grp in daily_cal.groupby("part_id", sort=False)
    }
    lt_by_part = {
        pid: grp["lead_time_days"].to_numpy(dtype=int)
        for pid, grp in lt_cal.groupby("part_id", sort=False)
    }

    rows = []
    for _, r in classical_df.iterrows():
        pid = r["part_id"]
        draws = simulate_block_bootstrap_lt_demand(
            demand_by_part[pid], lt_by_part[pid], n_sims=n_sims, rng=rng
        )
        csl_map = compute_bootstrap_rop_table(draws, DEFAULT_CSL_LEVELS)

        for csl, vals in csl_map.items():
            rows.append({
                "part_id": pid,
                "sb_class": r["sb_class"],
                "ved_class": r["ved_class"],
                "target_csl": csl,
                "rop_bootstrap": vals["rop_bootstrap"],
                "ss_bootstrap": vals["ss_bootstrap"],
                "mean_lt_demand_emp": vals["mean_lt_demand"],
                "p99_lt_demand_emp": vals["p99_lt_demand"],
                "order_qty_q": int(r["eoq_classical_fc"]),
            })

    out_df = pd.DataFrame(rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_csv, index=False)

    with sqlite3.connect(db_path) as conn:
        out_df.to_sql("bootstrap_policies", conn, if_exists="replace", index=False)

    return out_df


if __name__ == "__main__":
    boot_df = run_bootstrap_simulation()
    with sqlite3.connect("data/processed/mro_inventory.db") as conn:
        cls_df = pd.read_sql_query(
            "SELECT part_id, sb_class, rop_classical_hist, rop_classical_fc FROM classical_policies;",
            conn,
        )

    comp = cls_df.merge(boot_df[boot_df["target_csl"] == 0.95], on=["part_id", "sb_class"])
    print("=== KLASIK NORMAL FORMUL vs. AMPIRIK BLOK BOOTSTRAP (CSL = %95, Ortalama ROP) ===")
    summary = (
        comp.groupby("sb_class")[["rop_classical_hist", "rop_classical_fc", "rop_bootstrap"]]
        .mean()
        .round(2)
    )
    summary["fark_emp_vs_klasik"] = (summary["rop_bootstrap"] - summary["rop_classical_hist"]).round(2)
    print(summary.to_string())

```

---
## DOSYA: tests\test_backtest.py
```
import numpy as np
from src.evaluation.backtest import simulate_single_part_policy


def test_pipeline_prevents_duplicate_orders():
    # Initial on_hand = ceil(2 + 5/2) = 5. Day 0 demand = 4 drops on_hand to 1 (<= ROP 2).
    # Order of 5 arrives on day 5; days 1..4 must NOT place duplicate orders while inv_pos = 6.
    demand = np.array([4, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    lts = np.array([5], dtype=int)

    res = simulate_single_part_policy(
        daily_demand=demand,
        lead_time_draws=lts,
        unit_cost=1000.0,
        ved_class="E",
        policy_type="sQ",
        trigger_level=2,
        order_param=5,
    )
    assert res["order_count"] == 1
    assert res["fill_rate"] == 1.0


def test_higher_rop_improves_or_maintains_fill_rate():
    rng = np.random.default_rng(42)
    demand = rng.choice([0, 0, 0, 2, 5], size=365).astype(float)
    lts = np.array([10, 14, 18], dtype=int)

    low_rop = simulate_single_part_policy(demand, lts, 5000.0, "V", "sQ", trigger_level=2, order_param=6)
    high_rop = simulate_single_part_policy(demand, lts, 5000.0, "V", "sQ", trigger_level=15, order_param=6)

    assert high_rop["fill_rate"] >= low_rop["fill_rate"]
    assert high_rop["holding_cost"] >= low_rop["holding_cost"]

```

---
## DOSYA: tests\test_forecasting.py
```
import numpy as np
from src.forecasting.models import (
    forecast_naive,
    forecast_ma,
    forecast_croston,
    forecast_tsb,
    compute_error_metrics,
    select_best_model,
    demonstrate_mape_pitfall,
)


def test_zero_denominator_unforecastable():
    y_train_zero = np.zeros(18)
    y_val = np.array([0, 1, 0, 0, 0, 0], dtype=float)
    y_pred = np.zeros(6)
    res = compute_error_metrics(y_train_zero, y_val, y_pred)
    assert res["forecastable"] is False
    assert np.isnan(res["rmsse"])
    assert np.isnan(res["mase"])


def test_simplicity_tie_breaker():
    # Naive is 1.000, TSB is 0.985 -> Naive is within 2% of 0.985 (0.985 * 1.02 = 1.0047), so Naive wins
    scores = {"Naive": 1.000, "MA_3": 1.050, "Croston": 0.990, "SBA": 0.988, "TSB": 0.985}
    assert select_best_model(scores, tolerance=0.02) == "Naive"

    # TSB is clearly better (>2% improvement) -> TSB wins
    scores_clear = {"Naive": 1.200, "MA_3": 1.150, "Croston": 1.050, "SBA": 1.040, "TSB": 0.950}
    assert select_best_model(scores_clear, tolerance=0.02) == "TSB"


def test_tsb_decays_on_obsolescence():
    y = np.array([5, 0, 6, 0, 5, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    croston_val = forecast_croston(y)
    tsb_val = forecast_tsb(y)
    assert tsb_val < croston_val


def test_mape_undefined_on_zeros():
    res = demonstrate_mape_pitfall(np.array([0, 4, 0]), np.array([1.0, 1.0, 1.0]))
    assert res["mape_is_undefined"] is True

```

---
## DOSYA: tests\test_inventory.py
```
import numpy as np
from scipy.stats import norm
from src.inventory.classical import (
    calculate_safety_stock,
    calculate_rop,
    calculate_eoq,
)


def test_safety_stock_zero_lt_std():
    # (a) When sigma_L = 0 -> SS = z * sigma_d * sqrt(L)
    ss = calculate_safety_stock(demand_mean=2.0, demand_std=1.5, lt_mean=16.0, lt_std=0.0, csl=0.95)
    expected = norm.ppf(0.95) * 1.5 * np.sqrt(16.0)
    assert np.isclose(ss, expected, rtol=1e-9)


def test_safety_stock_zero_demand_std():
    # (b) When sigma_d = 0 -> SS = z * d_bar * sigma_L
    ss = calculate_safety_stock(demand_mean=3.0, demand_std=0.0, lt_mean=20.0, lt_std=4.0, csl=0.95)
    expected = norm.ppf(0.95) * 3.0 * 4.0
    assert np.isclose(ss, expected, rtol=1e-9)


def test_safety_stock_unit_consistency_daily_vs_monthly():
    # (c) Identical process expressed in daily vs monthly units must yield identical SS
    days_per_month = 30.0
    d_day, s_d_day = 2.0, 1.5
    l_day, s_l_day = 30.0, 6.0

    d_mon = d_day * days_per_month
    s_d_mon = s_d_day * np.sqrt(days_per_month)
    l_mon = l_day / days_per_month
    s_l_mon = s_l_day / days_per_month

    ss_daily = calculate_safety_stock(d_day, s_d_day, l_day, s_l_day, csl=0.95)
    ss_monthly = calculate_safety_stock(d_mon, s_d_mon, l_mon, s_l_mon, csl=0.95)
    assert np.isclose(ss_daily, ss_monthly, rtol=1e-9)


def test_eoq_minimum_bound_one():
    # (d) Very slow and expensive part must still yield EOQ >= 1
    eoq = calculate_eoq(annual_demand=0.5, unit_cost=100000.0, ordering_cost=1500.0, holding_rate=0.22)
    assert eoq == 1
    assert calculate_rop(0.0, 10.0, 0.0) == 1


def test_forecast_std_scaling_consistency():
    # If forecasted demand doubles under constant CV, safety stock must double
    ss_base = calculate_safety_stock(1.0, 0.8, 20.0, 4.0, csl=0.95)
    ss_shifted = calculate_safety_stock(2.0, 1.6, 20.0, 4.0, csl=0.95)
    assert np.isclose(ss_shifted, 2.0 * ss_base, rtol=1e-9)

```

---
## DOSYA: tests\test_reporting.py
```
from src.reporting.action_plan import classify_part_action


def test_classify_part_action_rules():
    assert "Eskime" in classify_part_action(2, 1, "D", 0.0, 0.0, 0)
    assert "Kritik Stok Artışı" in classify_part_action(3, 7, "V", 12.0, 1.0, 2)
    assert "Aşırı Stoğu Erit" in classify_part_action(10, 4, "E", 24.0, 2.0, 0)
    assert "Dengeli" in classify_part_action(5, 5, "C", 18.0, 1.5, 0)

```

---
## DOSYA: tests\test_segmentation.py
```
import numpy as np
from src.segmentation.classify import (
    compute_adi_cv2,
    classify_syntetos_boylan,
    classify_xyz,
)


def test_syntetos_boylan_quadrants_and_boundaries():
    assert classify_syntetos_boylan(1.31, 0.48) == "Smooth"
    assert classify_syntetos_boylan(1.31, 0.49) == "Erratic"
    assert classify_syntetos_boylan(1.32, 0.48) == "Intermittent"
    assert classify_syntetos_boylan(1.32, 0.49) == "Lumpy"


def test_compute_adi_cv2_edge_cases():
    # All-zero demand
    adi_zero, cv2_zero = compute_adi_cv2(np.zeros(24))
    assert np.isinf(adi_zero)
    assert cv2_zero == 0.0

    # Single non-zero demand in 24 periods -> ADI = 24.0, CV2 = 0.0
    single = np.zeros(24)
    single[5] = 10
    adi_s, cv2_s = compute_adi_cv2(single)
    assert adi_s == 24.0
    assert cv2_s == 0.0

    # Constant positive demand every period -> ADI = 1.0, CV2 = 0.0
    const = np.full(12, 5.0)
    adi_c, cv2_c = compute_adi_cv2(const)
    assert adi_c == 1.0
    assert cv2_c == 0.0


def test_xyz_classification():
    _, cls_x = classify_xyz(np.array([10, 10, 11, 9, 10, 10]))
    _, cls_y = classify_xyz(np.array([2, 10, 4, 12, 3, 11]))
    _, cls_z = classify_xyz(np.array([0, 0, 0, 25, 0, 0]))
    _, cls_zero = classify_xyz(np.zeros(12))

    assert cls_x == "X"
    assert cls_y == "Y"
    assert cls_z == "Z"
    assert cls_zero == "Z"

```

---
## DOSYA: tests\test_simulation.py
```
import numpy as np
from src.simulation.bootstrap import (
    simulate_block_bootstrap_lt_demand,
    compute_bootstrap_rop_table,
)
from src.inventory.classical import calculate_safety_stock, calculate_rop


def test_block_bootstrap_reproducibility():
    demand = np.array([0, 0, 5, 0, 0, 0, 12, 0, 0, 3] * 10, dtype=float)
    lts = np.array([5, 7, 10], dtype=int)

    d1 = simulate_block_bootstrap_lt_demand(demand, lts, n_sims=500, rng=np.random.default_rng(42))
    d2 = simulate_block_bootstrap_lt_demand(demand, lts, n_sims=500, rng=np.random.default_rng(42))
    assert np.array_equal(d1, d2)


def test_block_bootstrap_all_zero_demand():
    draws = simulate_block_bootstrap_lt_demand(np.zeros(100), np.array([10, 15]), n_sims=200)
    assert np.all(draws == 0.0)
    table = compute_bootstrap_rop_table(draws, csl_levels=(0.95,))
    assert table[0.95]["rop_bootstrap"] == 1
    assert table[0.95]["ss_bootstrap"] == 1.0


def test_bootstrap_captures_extreme_tail_vs_normal():
    # 98 days of 0, 2 days of 50 units -> at CSL=0.99 normal approx severely underestimates burst
    demand_series = np.array([0] * 98 + [50, 50], dtype=float)
    lts = np.array([1], dtype=int)

    draws = simulate_block_bootstrap_lt_demand(
        demand_series, lts, n_sims=5000, rng=np.random.default_rng(42)
    )
    emp_rop_99 = compute_bootstrap_rop_table(draws, csl_levels=(0.99,))[0.99]["rop_bootstrap"]

    ss_norm = calculate_safety_stock(
        float(np.mean(demand_series)), float(np.std(demand_series, ddof=1)), 1.0, 0.0, csl=0.99
    )
    rop_norm = calculate_rop(float(np.mean(demand_series)), 1.0, ss_norm)

    assert emp_rop_99 > rop_norm

```

---
## DOSYA: tests\test_smoke.py
```
def test_environment_smoke():
    import numpy as np
    import pandas as pd
    import scipy
    assert np.__version__ is not None
    assert pd.__version__ is not None

```

---
## CIKTI: backtest_summary.csv
```
policy,holding_cost_M,ordering_cost_M,shortage_base_M,total_cost_Low_M,total_cost_Base_M,total_cost_High_M,portfolio_fill_rate_pct,vital_avg_stockout_days,all_avg_stockout_days
MinMax_Current_1.5_3.0m,17.23,1.95,63.54,50.95,82.72,146.25,92.17,2.32,1.84
MinMax_Grid_1.0_2.0m,10.23,2.51,116.55,71.02,129.29,245.84,84.75,5.16,4.04
MinMax_Grid_2.0_4.0m,25.6,1.58,35.82,45.09,63.0,98.82,95.62,1.18,0.89
MinMax_Grid_3.0_6.0m,39.67,1.16,17.8,49.73,58.63,76.43,97.96,0.42,0.35
Classical_Hist_CSL95,16.77,2.73,36.09,37.54,55.58,91.67,94.31,1.36,1.44
Classical_Forecast_CSL95,18.32,2.69,49.9,45.96,70.9,120.8,94.32,1.2,1.33
Bootstrap_CSL85,12.37,2.74,72.82,51.53,87.94,160.76,89.47,2.94,2.87
Bootstrap_CSL90,14.79,2.96,48.0,41.75,65.75,113.75,92.52,2.1,2.12
Bootstrap_CSL95,18.29,3.14,27.02,34.95,48.46,75.47,95.52,1.16,1.21
Bootstrap_CSL98,22.37,3.23,14.25,32.73,39.86,54.11,97.58,0.56,0.67
Bootstrap_CSL99,24.8,3.32,8.71,32.48,36.83,45.54,98.31,0.36,0.47

```
