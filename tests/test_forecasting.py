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
