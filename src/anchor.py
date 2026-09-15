"""
Validate the derivation against the government;s published Stage 1 figures. 

Published:
    92 medicines, 256 PBS items

Note that neither number was used to build the derivation rule, so agreement is independent confirmation. 

“256 Items" is ambigious. It may count the new 60-days code only, or the 30-day codes made eligible. Both counts are reported; the band is applied to the new-code count. 
"""

import sys

from src.config import ANCHOR_DRUG_BAND, ANCHOR_ITEM_BAND, STAGE_MONTHS


def anchor_counts(con):
    """
    Calculate `new_items`, `all_items` and `drugs` in the database.

    Args:
        con: Open connection to our duckdb
    
    Returns:
        A dictionary contains {new_items, all_items, drugs}
    """
    s1 = STAGE_MONTHS[1]
    row = con.execute(
        f"""
        SELECT
            COUNT(DISTINCT CASE WHEN f.first_month = {s1} THEN f.item_code END)
            AS new_items,
            COUNT(DISTINCT f.item_code)
            AS all_items,
            COUNT(DISTINCT m.drug_name)
            AS drugs,
        FROM group_stage g
        JOIN item_first f ON f.group_key = g.group_key
        JOIN item_map m ON m.item_code = f.item_code
        WHERE g.stage = 1
        """
    ).fetchone()
    
    return {
        "new_items": row[0],
        "all_items": row[1],
        "drugs": row[2]
    }


def check_anchor(counts):
    """
    Judge the number we counted in `anchor_count()`, compare it to the range we defined in `src/config.py`, and the actual number government announced. 

    Args:
        counts (dict): The dictionary we get from function `anchor_count()

    Returns:
        Whether the number we counted in the range that we pre-defined. 
        A msg contains the number we counted, the range we pre-defined, and the actual number government announced. 
    """
    lo_i, hi_i = ANCHOR_ITEM_BAND
    lo_d, hi_d = ANCHOR_DRUG_BAND

    items_ok = lo_i <= counts["new_items"] <= hi_i
    drugs_ok = lo_d <= counts["drugs"] <= hi_d

    msg = (
        f"new 60-day item codes: {counts['new_items']} "
        f"(band {lo_i}-{hi_i}, published 256)\n"
        f"all item codes in Stage 1 groups: {counts['all_items']}\n"
        f"distinct drug names: {counts['drugs']} "
        f"(band {lo_d}-{hi_d}, published 92)"
    )

    return (items_ok and drugs_ok), msg

    

def main():
    from src.config import DB
    import duckdb

    con = duckdb.connect(str(DB))
    counts = anchor_counts(con)
    ok, msg = check_anchor(counts)  
    print(msg)
    if not ok:
        print("\nANCHOR FAILED. Derivation rule is wrong. Do not proceed.", file=sys.stderr)
        sys.exit(1)
    print("\nAnchor passed.")

if __name__ == "__main__":
    main()