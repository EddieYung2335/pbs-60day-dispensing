import duckdb
import pandas as pd
import pytest

from src.derive import build_item_first, build_item_months


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