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
