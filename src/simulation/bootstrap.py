from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

DEFAULT_CSL_LEVELS = (0.85, 0.90, 0.95, 0.98, 0.99, 0.995)
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
    run_bootstrap_simulation()
