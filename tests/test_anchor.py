from src.anchor import check_anchor


def test_counts_inside_band_pass():
    ok, msg = check_anchor({"new_items": 256, "all_items": 512, "drugs": 92})
    assert ok is True
    assert "256" in msg


def test_item_count_outside_band_fails():
    ok, msg = check_anchor({"new_items": 180, "all_items": 360, "drugs": 92})
    assert ok is False
    assert "230" in msg


def test_drug_count_outside_band_fails():
    ok, msg = check_anchor({"new_items": 256, "all_items": 512, "drugs": 140})
    assert ok is False