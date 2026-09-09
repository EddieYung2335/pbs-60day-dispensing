"""
Take seven text files, produce one queryable database.
Everything after this file talks to `data/pbs.duckdb` and never the raw csv itself. 
"""

import duckdb
import pandas as pd

from src.config import DB, ENCODING, MAP_FILE, RAW, SUPPLY_FILES

"""
Tell pandas the type of every column. 
This dictionary is a contract with the data.
"""
SUPPLY_DTYPES = {
    "MONTH_OF_SUPPLY": "int32",
    "ITEM_CODE": "string",
    "DRUG_TYPE": "string",
    "PATIENT_CATEGORY": "string",
    "PHARMACY_TYPE": "string",
    "PRESCRIPTIONS": "int64",
    "PATIENT_CONTRIB": "float64",
    "GOVT_CONTRIB": "float64",
    "TOTAL_COST": "float64",
    "RETAIL_MARKUP": "float64",
    "PATIENT_NET_CONTRIB": "float64",
}


def read_supply_csv(path):
    """
    Read one supply CSV into a DataFrame. Handle one file, not multiple. 
    encoding = ENCODING = Latin-1, from config
    dtype = SUPPLY_DTYPES, from the contract we define above

    Args:
        path: the path to the CSV file
    
    Returns:
        A pandas DataFrame with the data from the CSV file.
    """
    return pd.read_csv(path, encoding=ENCODING, dtype=SUPPLY_DTYPES)


def read_item_map(path):
    """
    Read the dictionary file and normalise its column names. 
    Rename (columns={old: new}), takes a dict of old-name -> new-name.

    Args:
        path: the path to the dictionary file

    Returns:
        A pandas DataFrame with the normalised column names.
    """
    df = pd.read_csv(path, encoding=ENCODING, dtype="string")
    df = df.rename(
         columns={
            "ITEM_CODE": "item_code",
            "DRUG_NAME": "drug_name",
            "FORM/STRENGTH": "form_strength",
            "ATC5_Code": "atc5",
        }
    )
    return df[["item_code", "drug_name", "form_strength", "atc5"]]


def group_key_expr():
    """
    Hold the group-key definition in exactly one place.
    """
    return "upper(trim(drug_name)) || '|' || upper(trim(form_strength))"


def build(db_path=DB):
    """
    The actual assembly.
    CSVs in, database out, connection returned.

    Args:
        db_path: the path to the database file. Defaults to DB.
    
    Returns:
        A duckdb connection to the database.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    supply = pd.concat(
        [read_supply_csv(RAW / f) for f in SUPPLY_FILES], ignore_index=True
    )
    item_map = read_item_map(RAW / MAP_FILE)

    con = duckdb.connect(str(db_path))
    con.register("supply_df", supply)
    con.register("item_map_df", item_map)
    con.execute("CREATE OR REPLACE TABLE supply AS SELECT * FROM supply_df")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE item_map AS
        SELECT item_code, drug_name, form_strength, atc5, {group_key_expr()} AS group_key
        FROM item_map_df
        """
    )
    return con


def main():
    """
    Run the build and print four sanity numbers.
    """
    con = build()
    rows = con.execute("SELECT count(*) from supply").fetchone()[0]
    items = con.execute("SELECT count(*) from item_map").fetchone()[0]
    groups = con.execute("SELECT count(DISTINCT group_key) FROM item_map").fetchone()[0]
    months = con.execute(
        "SELECT min(MONTH_OF_SUPPLY), max(MONTH_OF_SUPPLY) from supply"
    ).fetchone()

    print(f"supply rows: {rows:,}")
    print(f"item codes:  {items:,}")
    print(f"drug groups: {groups:,}")
    print(f"months:      {months[0]} to {months[1]}")


if __name__ == "__main__":
    main()
