import numpy as np
from src.evaluation.backtest import simulate_single_part_policy


def test_pipeline_prevents_duplicate_orders():
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
        initial_stock=5,
    )
    assert res["order_count"] == 1
    assert res["fill_rate"] == 1.0


def test_higher_rop_improves_or_maintains_fill_rate():
    rng = np.random.default_rng(42)
    demand = rng.choice([0, 0, 0, 2, 5], size=365).astype(float)
    lts = np.array([10, 14, 18], dtype=int)

    low_rop = simulate_single_part_policy(demand, lts, 5000.0, "V", "sQ", trigger_level=2, order_param=6, initial_stock=5)
    high_rop = simulate_single_part_policy(demand, lts, 5000.0, "V", "sQ", trigger_level=15, order_param=6, initial_stock=5)

    assert high_rop["fill_rate"] >= low_rop["fill_rate"]
    assert high_rop["holding_cost"] >= low_rop["holding_cost"]


def test_backorder_tracks_debt_and_clears_on_arrival():
    demand = np.array([5, 0, 0, 0, 0], dtype=float)
    lts = np.array([2], dtype=int)

    res = simulate_single_part_policy(
        daily_demand=demand,
        lead_time_draws=lts,
        unit_cost=1000.0,
        ved_class="V",
        policy_type="sQ",
        trigger_level=2,
        order_param=4,
        initial_stock=2,
        fulfillment_mode="backorder",
    )
    # Day 0: demand 5, initial 2 -> 3 backordered; order of 4 arrives Day 2 and clears 3 backorder leaving 1 on hand
    assert res["ending_backorder"] == 0
    assert res["stockout_days"] == 2
