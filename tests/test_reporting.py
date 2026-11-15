from src.reporting.action_plan import classify_part_action


def test_classify_part_action_rules():
    assert "Eskime" in classify_part_action(2, 1, "D", 0.0, 0.0, 0)
    assert "Kritik Stok Artışı" in classify_part_action(3, 7, "V", 12.0, 1.0, 2)
    assert "Aşırı Stoğu Erit" in classify_part_action(10, 4, "E", 24.0, 2.0, 0)
    assert "Dengeli" in classify_part_action(5, 5, "C", 18.0, 1.5, 0)
