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
