import duckdb
import pandas as pd

from src.guards import run_guards


def _seed(rows):
    """rows: (item_code, month, scripts). All map to one group with a 60-day code BBB."""
    c = duckdb.connect(":memory:")
    im = pd.DataFrame(
        [(i, "D", "F", "X", "D | F") for i in {r[0] for r in rows}],
        columns=["item_code", "drug_name", "form_strength", "atc5", "group_key"],
    )
    months = pd.DataFrame(rows, columns=["item_code", "month", "scripts"])
    months["group_key"] = "D | F"
    first = months.groupby(["item_code", "group_key"], as_index=False).agg(
        first_month=("month", "min"), total_scripts=("scripts", "sum")
    )
    stage = pd.DataFrame(
        [("D | F", 202101, 1, 202309)],
        columns=["group_key", "group_first_month", "stage", "switch_month"],
    )
    for name, df in [("item_map", im), ("item_months", months), ("item_first", first), ("group_stage", stage)]:
        c.register(f"{name}_df", df)
        c.execute(f"CREATE TABLE {name} AS SELECT * FROM {name}_df")
    return c


def test_clean_substitution_is_not_flagged():
    rows = [("AAA", m, 100) for m in [202303, 202304, 202305, 202306, 202307, 202308]]
    rows += [("AAA", m, s) for m, s in zip(
        [202309, 202310, 202311, 202312, 202401, 202402], [90, 80, 70, 60, 55, 50])]
    rows += [("BBB", m, s) for m, s in zip(
        [202309, 202310, 202311, 202312, 202401, 202402], [5, 10, 15, 20, 22, 25])]
    flags = run_guards(_seed(rows))
    assert flags.empty


def test_volume_added_not_shifted_is_flagged_as_new_brand():
    """30-day scripts do not fall. That is a new product, not a 60-day listing."""
    rows = [("AAA", m, 100) for m in
            [202303, 202304, 202305, 202306, 202307, 202308,
             202309, 202310, 202311, 202312, 202401, 202402]]
    rows += [("BBB", m, 50) for m in
             [202309, 202310, 202311, 202312, 202401, 202402]]
    flags = run_guards(_seed(rows))
    assert "no_substitution" in set(flags["guard"])


def test_thirty_day_code_dying_completely_is_flagged_as_relisting():
    rows = [("AAA", m, 100) for m in
            [202303, 202304, 202305, 202306, 202307, 202308]]
    rows += [("BBB", m, 50) for m in
             [202309, 202310, 202311, 202312, 202401, 202402]]
    flags = run_guards(_seed(rows))
    assert "possible_relisting" in set(flags["guard"])
