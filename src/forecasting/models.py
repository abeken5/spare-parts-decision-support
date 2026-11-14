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
