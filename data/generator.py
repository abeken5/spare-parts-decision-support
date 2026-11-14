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
