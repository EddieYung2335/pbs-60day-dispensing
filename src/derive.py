"""
Derive which drug-from groups beame 60-day eligible, and when. 
"""

from src.config import COMMUNITY_PHARMACY

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



