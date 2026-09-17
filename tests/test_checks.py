import pandas as pd

from src.checks import january_effect


def test_january_effect_isolates_calendar_month():
    panel = pd.DataFrame(
        [("g", 202312, 100, 1000.0), ("g", 202401, 100, 500.0),
         ("g", 202412, 100, 1000.0), ("g", 202501, 100, 500.0)],
        columns=["group_key", "month", "scripts_total", "govt_contrib"],
    )
    out = january_effect(panel)
    jan = out[out["month_of_year"] == 1]
    dec = out[out["month_of_year"] == 12]
    assert jan["mean_govt_per_script"].iloc[0] < dec["mean_govt_per_script"].iloc[0]
    # two Januaries of 100 scripts each: a mean per year, not a 200 total
    assert jan["mean_scripts"].iloc[0] == 100
