import numpy as np
from src.evaluation.backtest import simulate_single_part_policy


def test_pipeline_prevents_duplicate_orders():
    # Initial on_hand = ceil(2 + 5/2) = 5. Day 0 demand = 4 drops on_hand to 1 (<= ROP 2).
    # Order of 5 arrives on day 5; days 1..4 must NOT place duplicate orders while inv_pos = 6.
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
    )
    assert res["order_count"] == 1
    assert res["fill_rate"] == 1.0


def test_higher_rop_improves_or_maintains_fill_rate():
    rng = np.random.default_rng(42)
    demand = rng.choice([0, 0, 0, 2, 5], size=365).astype(float)
    lts = np.array([10, 14, 18], dtype=int)

    low_rop = simulate_single_part_policy(demand, lts, 5000.0, "V", "sQ", trigger_level=2, order_param=6)
    high_rop = simulate_single_part_policy(demand, lts, 5000.0, "V", "sQ", trigger_level=15, order_param=6)

    assert high_rop["fill_rate"] >= low_rop["fill_rate"]
    assert high_rop["holding_cost"] >= low_rop["holding_cost"]
