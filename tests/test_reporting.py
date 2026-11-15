from src.reporting.action_plan import classify_part_action

def test_classify_part_action_rules():
    assert "Eskime" in classify_part_action(2, 1, "D", 0.0, 0.0)
    assert "Vital" in classify_part_action(2, 5, "V", 10.0, 1.0)
    assert "Hizmet" in classify_part_action(2, 5, "E", 10.0, 1.0)
    assert "Erit" in classify_part_action(5, 2, "E", 10.0, 1.0)
    assert "Dengeli" in classify_part_action(3, 3, "E", 10.0, 1.0)
