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
