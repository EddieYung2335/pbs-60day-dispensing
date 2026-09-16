import duckdb
import pandas as pd

from src.panel import build_panel


def _con():
    c = duckdb.connect(":memory:")
    supply = pd.DataFrame(
        [
            ("AAA", 202308, "S90", "C1", "ABOVE CO-PAYMENT", 100, 700.0, 300.0, 1000.0),
            ("AAA", 202309, "S90", "C1", "ABOVE CO-PAYMENT", 60, 420.0, 180.0, 600.0),
            ("BBB", 202309, "S90", "C1", "ABOVE CO-PAYMENT", 20, 140.0, 60.0, 200.0),
            ("AAA", 202309, "S90", "G2", "ABOVE CO-PAYMENT", 10, 70.0, 30.0, 100.0),
            # excluded: repatriation patient and hospital pharmacy
            ("AAA", 202309, "S90", "R1", "ABOVE CO-PAYMENT", 99, 0.0, 0.0, 0.0),
            ("AAA", 202309, "S94 PUB", "C1", "ABOVE CO-PAYMENT", 99, 0.0, 0.0, 0.0),
        ],
        columns=["ITEM_CODE", "MONTH_OF_SUPPLY", "PHRMCY_TYPE", "PATIENT_CAT",
                 "SCRIPT_TYPE", "PRESCRIPTIONS", "PATIENT_CONTRIB", "GOVT_CONTRIB",
                 "TOTAL_COST"],
    )
    item_map = pd.DataFrame(
        [("AAA", "D", "F", "X", "D | F"), ("BBB", "D", "F", "X", "D | F")],
        columns=["item_code", "drug_name", "form_strength", "atc5", "group_key"],
    )
    item_first = pd.DataFrame(
        [("AAA", "D | F", 202101, 160), ("BBB", "D | F", 202309, 20)],
        columns=["item_code", "group_key", "first_month", "total_scripts"],
    )
    group_stage = pd.DataFrame(
        [("D | F", 202101, 1, 202309)],
        columns=["group_key", "group_first_month", "stage", "switch_month"],
    )
    for name, df in [("supply", supply), ("item_map", item_map),
                     ("item_first", item_first), ("group_stage", group_stage)]:
        c.register(f"{name}_df", df)
        c.execute(f"CREATE TABLE {name} AS SELECT * FROM {name}_df")
    return c


def test_supply_months_doubles_sixty_day_scripts():
    p = build_panel(_con())
    row = p[(p["month"] == 202309) & (p["patient_type"] == "concessional")].iloc[0]
    assert row["scripts_30"] == 60
    assert row["scripts_60"] == 20
    assert row["supply_months"] == 100.0  # 60 + 2*20


def test_repatriation_and_hospital_rows_excluded():
    p = build_panel(_con())
    assert set(p["patient_type"]) == {"concessional", "general"}
    assert p["scripts_total"].sum() == 190  # 100 + 60 + 20 + 10


def test_never_treated_group_has_no_sixty_day_scripts():
    c = _con()
    c.execute("UPDATE group_stage SET stage = 0, switch_month = NULL")
    p = build_panel(c)
    assert p["scripts_60"].sum() == 0