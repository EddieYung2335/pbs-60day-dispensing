import duckdb
import pandas as pd
import pytest

from src.derive import build_item_first, build_item_months, build_group_stage


@pytest.fixture
def con():
    """Tiny in-memory fixture: one 30-day code, one 60-day code appearing 202309."""
    c = duckdb.connect(":memory:")
    supply = pd.DataFrame(
        [
            # item,     month,  pharmacy, scripts
            ("08215J", 202307, "S90", 100),
            ("08215J", 202308, "S90", 100),
            ("08215J", 202309, "S90", 90),
            ("13468W", 202309, "S90", 5),
            ("13468W", 202310, "S90", 10),
            # hospital dispensing must be excluded
            ("13468W", 202307, "S94 PUB", 3),
        ],
        columns=["ITEM_CODE", "MONTH_OF_SUPPLY", "PHRMCY_TYPE", "PRESCRIPTIONS"],
    )
    item_map = pd.DataFrame(
        [
            ("08215J", "ATORVASTATIN", "Tablet 40 mg", "C10AA05", "ATORVASTATIN | TABLET 40 MG"),
            ("13468W", "ATORVASTATIN", "Tablet 40 mg", "C10AA05", "ATORVASTATIN | TABLET 40 MG"),
        ],
        columns=["item_code", "drug_name", "form_strength", "atc5", "group_key"],
    )
    c.register("supply_df", supply)
    c.register("item_map_df", item_map)
    c.execute("CREATE TABLE supply AS SELECT * FROM supply_df")
    c.execute("CREATE TABLE item_map AS SELECT * FROM item_map_df")
    return c


def test_first_month_ignores_hospital_dispensing(con):
    build_item_months(con)
    build_item_first(con)
    rows = con.execute(
        "SELECT item_code, first_month FROM item_first ORDER BY item_code"
    ).fetchall()
    assert rows == [("08215J", 202307), ("13468W", 202309)]


def test_item_months_excludes_zero_script_rows(con):
    con.execute(
        "INSERT INTO supply VALUES ('08215J', 202311, 'S90', 0)"
    )
    build_item_months(con)
    months = con.execute(
        "SELECT month FROM item_months WHERE item_code='08215J' ORDER BY month"
    ).fetchall()
    assert 202311 not in [m[0] for m in months]

def test_new_code_on_stage1_month_with_existing_sibling_is_treated(con):
    build_item_months(con)
    build_item_first(con)
    build_group_stage(con)
    row = con.execute(
        "SELECT stage, switch_month FROM group_stage"
    ).fetchone()
    assert row == (1, 202309)


def test_group_that_only_appears_at_stage_month_is_not_treated():
    """A brand new product launching in Sept 2023 is not a 60-day listing."""
    c = duckdb.connect(":memory:")
    supply = pd.DataFrame(
        [("99999X", 202309, "S90", 50), ("99999X", 202310, "S90", 60)],
        columns=["ITEM_CODE", "MONTH_OF_SUPPLY", "PHRMCY_TYPE", "PRESCRIPTIONS"],
    )
    item_map = pd.DataFrame(
        [("99999X", "NEWDRUG", "Tablet 5 mg", "A01AA01", "NEWDRUG | TABLET 5 MG")],
        columns=["item_code", "drug_name", "form_strength", "atc5", "group_key"],
    )
    c.register("supply_df", supply)
    c.register("item_map_df", item_map)
    c.execute("CREATE TABLE supply AS SELECT * FROM supply_df")
    c.execute("CREATE TABLE item_map AS SELECT * FROM item_map_df")
    build_item_months(c)
    build_item_first(c)
    build_group_stage(c)
    assert c.execute("SELECT stage FROM group_stage").fetchone()[0] == 0


def test_earliest_stage_wins_when_group_gains_codes_twice():
    c = duckdb.connect(":memory:")
    supply = pd.DataFrame(
        [
            ("AAA", 202101, "S90", 10),
            ("BBB", 202309, "S90", 5),
            ("CCC", 202403, "S90", 5),
        ],
        columns=["ITEM_CODE", "MONTH_OF_SUPPLY", "PHRMCY_TYPE", "PRESCRIPTIONS"],
    )
    item_map = pd.DataFrame(
        [
            ("AAA", "D", "F", "X", "D | F"),
            ("BBB", "D", "F", "X", "D | F"),
            ("CCC", "D", "F", "X", "D | F"),
        ],
        columns=["item_code", "drug_name", "form_strength", "atc5", "group_key"],
    )
    c.register("supply_df", supply)
    c.register("item_map_df", item_map)
    c.execute("CREATE TABLE supply AS SELECT * FROM supply_df")
    c.execute("CREATE TABLE item_map AS SELECT * FROM item_map_df")
    build_item_months(c)
    build_item_first(c)
    build_group_stage(c)
    assert c.execute("SELECT stage FROM group_stage").fetchone()[0] == 1