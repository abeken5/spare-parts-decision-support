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

        # Variant B: Forecast-Informed Classical (winning forecast daily rate)
        d_fc = float(r["forecast_daily_part"])
        d_std_fc = d_std * (d_fc / d_hist) if d_hist > 0 else d_std`r`n
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

