import pandas as pd
import pytest

from src.config import PROCESSED

# pytestmark puts one label on every test in the file
pytestmark = pytest.mark.integration

ATOR = "ATORVASTATIN | TABLET 40 MG (AS CALCIUM)"
AMOX_PREFIX = "AMOXICILLIN"

# Prepare this data once, then share it with every test in this file. 
@pytest.fixture(scope="module")
def cohort():
    path = PROCESSED / "cohort.parquet"
    if not path.exists():
        pytest.skip("run `python -m src.build_cohort` first")
    return pd.read_parquet(path)

def test_atorvastatin_40mg_is_stage_one(cohort):
    row = cohort[cohort["group_key"] == ATOR]
    assert len(row) == 1, f"expected one group for {ATOR}, got {len(row)}"
    assert row["stage"].iloc[0] == 1
    assert row["switch_month"].iloc[0] == 202309

def test_amoxycillin_is_never_eligible(cohort):
    amox = cohort[cohort["drug_name"].str.startswith(AMOX_PREFIX, na=False)]
    assert len(amox) > 0, "amoxycillin missing from cohort entirely"
    assert (amox["stage"] == 0).all()

def test_atorvastatin_supply_months_hold_across_the_switch():
    path = PROCESSED / "panel.parquet"
    if not path.exists():
        pytest.skip("run `python -m src.panel` first")
    panel = pd.read_parquet(path)
    g = panel[panel["group_key"] == ATOR].groupby("month")["supply_months"].sum()
    pre = g.loc[202303:202308].mean()
    post = g.loc[202403:202408].mean()
    assert abs(post - pre) / pre < 0.15, (
        f"supply-months moved {100 * (post - pre) / pre:.1f}% across the switch; "
        "expected roughly flat. Check the 60-day tagging in src/panel.py."
    )