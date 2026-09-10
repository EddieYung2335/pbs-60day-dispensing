"""
Derive which drug-from groups beame 60-day eligible, and when. 
"""

from src.config import COMMUNITY_PHARMACY, STAGE_MONTHS

def build_item_months(con):
    """
    Collapse raw rows to one row per (item_code, month), counting scripts. 

    Args:
        con: an open DuckDB connection holding tables supply and item_map. 
    
    Returns:
        nothing, but will creates table `item_months` in DuckDB
    """

    con.execute(
        f"""
        CREATE OR REPLACE TABLE item_months AS
        SELECT s.ITEM_CODE          AS item_code,
               m.group_key          AS group_key,
               s.MONTH_OF_SUPPLY    AS month,
               SUM(s.PRESCRIPTIONS) AS scripts
        FROM supply s
        JOIN item_map m ON m.item_code = s.ITEM_CODE
        WHERE s.PHRMCY_TYPE = '{COMMUNITY_PHARMACY}'
          AND s.PRESCRIPTIONS > 0
        GROUP BY 1, 2, 3
        """
    )

def build_item_first(con):
    """
    Reduce each item code to its earliest month and lifetime volume. 

    Args:
        con: DuckDB connection that hold `item_months` table
    
    Returns:
        nothing; creates table `item_first`
    """
    con.execute(
        """
        CREATE OR REPLACE TABLE item_first AS
        SELECT item_code,
               group_key,
               MIN(month)   AS first_month,
               SUM(scripts) AS total_scripts
        FROM item_months
        GROUP BY 1, 2
        """
    )

def build_group_stage(con):
    """
    Label each group with its stage and switch month. 

    Args:
        con: open Duckdb connection, holding `item_first`
    
    Returns:
        nothing. side effect: creates table group_stage(group_key, group_first_month, stage, switch_month)
    """
    s1 = STAGE_MONTHS[1]
    s2 = STAGE_MONTHS[2]
    s3 = STAGE_MONTHS[3]

    con.execute(
        f"""
        CREATE OR REPLACE TABLE group_stage AS
        WITH flags AS (
            SELECT group_key,
                   MAX(CASE WHEN first_month = {s1} THEN 1 ELSE 0 END) AS new_s1,
                   MAX(CASE WHEN first_month = {s2} THEN 1 ELSE 0 END) AS new_s2,
                   MAX(CASE WHEN first_month = {s3} THEN 1 ELSE 0 END) AS new_s3,
                   MIN(first_month)                                    AS group_first_month
            FROM item_first
            GROUP BY 1
        )
        SELECT group_key,
               group_first_month,
               CASE
                   WHEN new_s1 = 1 AND group_first_month < {s1} THEN 1
                   WHEN new_s2 = 1 AND group_first_month < {s2} THEN 2
                   WHEN new_s3 = 1 AND group_first_month < {s3} THEN 3
                   ELSE 0
               END AS stage,
               CASE
                   WHEN new_s1 = 1 AND group_first_month < {s1} THEN {s1}
                   WHEN new_s2 = 1 AND group_first_month < {s2} THEN {s2}
                   WHEN new_s3 = 1 AND group_first_month < {s3} THEN {s3}
                   ELSE NULL
               END AS switch_month
        FROM flags      
        """
    )