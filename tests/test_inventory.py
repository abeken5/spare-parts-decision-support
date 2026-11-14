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
