import pandas as pd
from src.load import read_item_map, group_key_expr

def test_item_map_builds_group_key(tmp_path):
    src = tmp_path / "map.csv"
    src.write_bytes(
        "ITEM_CODE,DRUG_NAME,FORM/STRENGTH,ATC5_Code\n"
        '"08215J","ATORVASTATIN","Tablet 40 mg (as calcium)","C10AA05"\n'
        .encode("latin-1")
    )
    df = read_item_map(src)
    assert list(df.columns) == ["item_code", "drug_name", "form_strength", "atc5"]
    assert df.loc[0, "item_code"] == "08215J"
    assert df.loc[0, "form_strength"] == "Tablet 40 mg (as calcium)"


def test_latin1_drug_name_survives(tmp_path):
    src = tmp_path / "map.csv"
    src.write_bytes(
        "ITEM_CODE,DRUG_NAME,FORM/STRENGTH,ATC5_Code\n"
        '"99999X","CAF\xc9INE","Tablet 1 mg","N06BC01"\n'.encode("latin-1")
    )
    df = read_item_map(src)
    assert df.loc[0, "drug_name"] == "CAFÉINE"


def test_group_key_expr_mentions_both_fields():
    expr = group_key_expr()
    assert "drug_name" in expr and "form_strength" in expr