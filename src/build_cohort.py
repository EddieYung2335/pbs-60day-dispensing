""" 
Run the full derivation and write `cohort.parquet`. 
Fails loudly on a bad anchor. 
"""

import sys

from src.anchor import anchor_counts, check_anchor
from src.config import DB, PROCESSED, DROP_LIST
from src.derive import build_group_stage, build_item_first, build_item_months, apply_manual_drops
from src.guards import run_guards
from src.load import build


def main():
    con = build(DB)
    build_item_months(con)
    build_item_first(con)
    build_group_stage(con)
    apply_manual_drops(con, DROP_LIST)

    counts = anchor_counts(con)
    ok, msg = check_anchor(counts)
    print(msg)
    if not ok:
        print("\nANCHOR FAILED. Fix the derivation rule before continuing.", file=sys.stderr)
        sys.exit(1)

    flags = run_guards(con)
    print(f"\nguard flags: {len(flags)} across {flags['group_key'].nunique() if len(flags) else 0} groups")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    cohort = con.execute(
    """
    SELECT g.group_key, g.stage, g.switch_month, g.group_first_month,
            any_value(m.drug_name) AS drug_name,
            any_value(m.form_strength) AS form_strength,
            any_value(m.atc5) AS atc5,
            count(DISTINCT f.item_code) AS n_items
    FROM group_stage g
    JOIN item_first f ON f.group_key = g.group_key
    JOIN item_map   m ON m.item_code = f.item_code
    GROUP BY 1, 2, 3, 4
    """
    ).df()
    cohort.to_parquet(PROCESSED / "cohort.parquet", index=False)
    flags.to_csv(PROCESSED / "guard_flags.csv", index=False)
    print(f"wrote {len(cohort):,} groups to {PROCESSED / 'cohort.parquet'}")

if __name__ == "__main__":
    main()

