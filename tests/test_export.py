import pandas as pd

from src.export import build_trend


def test_trend_labels_stages_readably():
    panel = pd.DataFrame(
        [("a", 202309, 10, 5, 20.0), ("b", 202309, 10, 0, 10.0)],
        columns=["group_key", "month", "scripts_30", "scripts_60", "supply_months"],
    )
    panel["scripts_total"] = panel["scripts_30"] + panel["scripts_60"]
    cohort = pd.DataFrame(
        [("a", 1), ("b", 0)], columns=["group_key", "stage"]
    )
    out = build_trend(panel, cohort)
    assert set(out["group_set"]) == {"Stage 1", "Never eligible"}
    assert out[out["group_set"] == "Stage 1"]["supply_months"].iloc[0] == 20.0
