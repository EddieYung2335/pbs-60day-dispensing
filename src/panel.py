from src.config import (COMMUNITY_PHARMACY, CONCESSIONAL, GENERAL, PROCESSED,
                    SUPPLY_MULTIPLIER)

_NEVER = 999999

def build_panel(con):
    conc = ", ".join(f"'{c}'" for c in CONCESSIONAL)
    gen = ", ".join(f"'{c}'" for c in GENERAL)

    df = con.execute(
        f"""
        WITH tagged AS (
            SELECT
                m.group_key,
                s.MONTH_OF_SUPPLY as month,
                CASE WHEN s.PATIENT_CAT IN ({conc}) THEN 'concessional'
                    ELSE 'general' END AS patient_type,
                s.SCRIPT_TYPE as script_type,
                CASE WHEN f.first_month >= COALESCE(g.switch_month, {_NEVER})
                    THEN 60 ELSE 30 END AS days,
                s.PRESCRIPTIONS, s.PATIENT_CONTRIB, s.GOVT_CONTRIB, s.TOTAL_COST
            FROM supply s
            JOIN item_map m ON m.item_code = s.ITEM_CODE
            JOIN item_first f ON f.item_code = s.ITEM_CODE
            JOIN group_stage g ON g.group_key = m.group_key
            WHERE s.PHRMCY_TYPE = '{COMMUNITY_PHARMACY}'
                AND s.PATIENT_CAT IN ({conc}, {gen})
        )
        SELECT group_key, month, patient_type, script_type,
               SUM(CASE WHEN days = 30 THEN PRESCRIPTIONS ELSE 0 END) AS scripts_30,
               SUM(CASE WHEN days = 60 THEN PRESCRIPTIONS ELSE 0 END) AS scripts_60,
               SUM(PRESCRIPTIONS)    AS scripts_total,
               SUM(PATIENT_CONTRIB)  AS patient_contrib,
               SUM(GOVT_CONTRIB)     AS govt_contrib,
               SUM(TOTAL_COST)       AS total_cost
        FROM tagged
        GROUP BY 1, 2, 3, 4
        ORDER BY 1, 2, 3, 4
        """
    ).df()
    df["supply_months"] = df["scripts_30"] + SUPPLY_MULTIPLIER * df["scripts_60"]
    return df



def main():
    import duckdb
    from src.config import DB

    con = duckdb.connect(str(DB))
    panel = build_panel(con)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(PROCESSED / "panel.parquet", index=False)
    print(f"panel rows: {len(panel):,}")
    print(f"groups:     {panel['group_key'].nunique():,}")
    print(f"months:     {panel['month'].min()} to {panel['month'].max()}")

if __name__ == "__main__":
    main()