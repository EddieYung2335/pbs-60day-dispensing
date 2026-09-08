from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
DB = ROOT / "data" / "pbs.duckdb"
REPORTS = ROOT / "reports"

BASE_URL = "https://www.pbs.gov.au/statistics/dos-and-dop/files/"

SUPPLY_FILES = [
    "dos-jul-2020-to-jun-2021-phrmcy-type.csv",
    "dos-jul-2021-to-jun-2022-phrmcy-type.csv",
    "dos-jul-2022-to-jun-2023-phrmcy-type.csv",
    "dos-jul-2023-to-jun-2024-phrmcy-type.csv",
    "dos-jul-2024-to-jun-2025-phrmcy-type.csv",
    "dos-jul-2025-to-jun-2026-phrmcy-type.csv",
]
MAP_FILE = "pbs-item-drug-map.csv"

ENCODING = "latin-1"

# Stage months maps which months each policy stage kicked in. 
# First stage, there is 202309 batch added etc.
STAGE_MONTHS = {1: 202309, 2: 202403, 3: 202409}

COMMUNITY_PHARMACY = "S90"
CONCESSIONAL = ("C0", "C1")
GENERAL = ("G1", "G2")

# Very Important for this project
# Before 60-day policy: 1 prescription = 1 month of supply
# After 60-day policy: 1 prescription = 2 months of supply
# Example:

# Month before policy: 100 prescriptions (30-day), all for Drug X.
# Prescription count: 100
# Supply months: 100

# Month after policy: 70 30-day prescriptions + 15 60-day prescriptions for Drug X.
# Prescription count: 85 (dropped 15%)
# Supply months: 70 + (15 × 2) = 100 (unchanged)

# If we look at the prescription, we will think that the supply has dropped by 15%, which is incorrect.
# Correct way is to: supply_months = script_30 + 2.0*script_60
SUPPLY_MULTIPLIER = 2.0


ANCHOR_ITEM_BAND = (230, 280)
ANCHOR_DRUG_BAND = (85, 100)