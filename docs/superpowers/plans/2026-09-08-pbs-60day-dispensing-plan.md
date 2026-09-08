# PBS 60-Day Dispensing Evaluation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure whether Australia's 60-day dispensing policy cut treatment supply or only cut prescription counts, and who captured the cost saving.

**Architecture:** Python pulls public PBS dispensing CSVs into DuckDB, derives which drug-form groups became 60-day eligible and when (from the data itself, no external list), builds a monthly panel, writes it to Parquet. R runs staggered difference-in-differences on that panel. Tableau Public renders the result.

**Tech Stack:** Python 3.11+, DuckDB, pandas, pyarrow, pytest. R 4.3+, `did`, `fixest`, `arrow`, `ggplot2`. Tableau Public.

**Spec:** `docs/superpowers/specs/2026-09-08-pbs-60day-dispensing-design.md`

## Global Constraints

- All source CSVs are **Latin-1**. Every read passes `encoding="latin-1"`. UTF-8 read fails on accented drug names.
- Stage switch months, fixed: **Stage 1 = 202309, Stage 2 = 202403, Stage 3 = 202409**.
- Restrict all analysis to `PHRMCY_TYPE = 'S90'` (community pharmacy).
- Patient types: concessional = `C0`,`C1`. General = `G1`,`G2`. Drop `R0`,`R1`,`DB`.
- `supply_months = scripts_30 + 2.0 * scripts_60`. Multiplier is a named constant, never inline.
- Group key = `upper(trim(DRUG_NAME)) || ' | ' || upper(trim(FORM_STRENGTH))`.
- Module names never start with a digit. Run order documented in README, not encoded in filenames.
- Commit after every task. Conventional Commits.
- `data/raw/` and `data/pbs.duckdb` gitignored. `data/processed/*.parquet` committed as snapshot.

## Supervisor Notes — Read Before Starting

Three places this project can die. Watch them.

1. **Task 7 is a hard gate.** Derivation validated against government's published "92 medicines, 256 items". Outside band → stop, fix rule, rerun. Do not widen band. Do not proceed to estimation with unvalidated cohort.
2. **Task 14 pre-trends.** If leads not flat, parallel trends fails. Do not hide. Report it. Project still valid as honest negative result.
3. **Phase 6 is where scope creep lives.** Estimation tasks are specified. No extra models. No "let me also try synthetic control". Ship what is planned.

Effort guess: Phase 0-3 one weekend. Phase 4-5 one weekend. Phase 6 one weekend. Phase 7-8 one weekend.

---

# PHASE 0 — FOUNDATION

## Task 1: Repo scaffold and config

**Files:**
- Create: `requirements.txt`, `src/__init__.py`, `src/config.py`, `tests/__init__.py`, `tests/test_config.py`, `README.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: nothing
- Produces: `src.config` constants — `ROOT`, `RAW`, `PROCESSED`, `DB`, `BASE_URL`, `SUPPLY_FILES` (list[str]), `MAP_FILE` (str), `STAGE_MONTHS` (dict[int,int]), `ENCODING` (str), `COMMUNITY_PHARMACY` (str), `CONCESSIONAL` (tuple), `GENERAL` (tuple), `SUPPLY_MULTIPLIER` (float), `ANCHOR_ITEM_BAND` (tuple[int,int]), `ANCHOR_DRUG_BAND` (tuple[int,int])

- [ ] **Step 1: Create venv and install**

```bash
cd /Users/eddie/Documents/DataSci/pbs-60day-dispensing
python3 -m venv venv
source venv/bin/activate.fish   # fish shell; use venv/bin/activate for bash
pip install duckdb pandas pyarrow pytest
pip freeze > requirements.txt
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_config.py`:

```python
from src import config


def test_six_supply_files_plus_map():
    assert len(config.SUPPLY_FILES) == 6
    assert config.MAP_FILE == "pbs-item-drug-map.csv"


def test_stage_months_are_policy_dates():
    assert config.STAGE_MONTHS == {1: 202309, 2: 202403, 3: 202409}


def test_multiplier_is_two():
    assert config.SUPPLY_MULTIPLIER == 2.0
```

- [ ] **Step 3: Run test, verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'src'`

- [ ] **Step 4: Write config**

Create `src/__init__.py` (empty) and `tests/__init__.py` (empty).

Create `src/config.py`:

```python
"""Paths, source URLs, and policy constants. Single source of truth."""
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

# Source files are Latin-1. UTF-8 read fails on accented drug names.
ENCODING = "latin-1"

# Policy commencement months, YYYYMM.
STAGE_MONTHS = {1: 202309, 2: 202403, 3: 202409}

COMMUNITY_PHARMACY = "S90"
CONCESSIONAL = ("C0", "C1")
GENERAL = ("G1", "G2")

# A 60-day script delivers twice a 30-day script. Assumption, tested in robustness.
SUPPLY_MULTIPLIER = 2.0

# Government published Stage 1 as 92 medicines / 256 PBS items.
# Derivation must land inside these bands or the rule is wrong. Set before seeing output.
ANCHOR_ITEM_BAND = (230, 280)
ANCHOR_DRUG_BAND = (85, 100)
```

- [ ] **Step 5: Run test, verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 6: Add directories and update gitignore**

```bash
mkdir -p data/raw data/processed reports/figures analysis
printf '%s\n' 'reports/figures/*.png' > /dev/null  # figures ARE committed; no ignore needed
cat >> .gitignore <<'EOF'
data/processed/*.duckdb
*.Rout
EOF
```

- [ ] **Step 7: README stub**

Create `README.md`:

```markdown
# Did 60-Day Dispensing Cut Treatment, or Just Cut Prescriptions?

A causal evaluation of Australia's 60-day dispensing policy using public PBS data.

**Status: in development.** Results not yet available.

See [the design spec](docs/superpowers/specs/2026-09-08-pbs-60day-dispensing-design.md).
```

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat(config): add project scaffold and policy constants"
```

---

# PHASE 1 — RAW DATA IN

## Task 2: Cached downloader

**Why:** Six files, ~180 MB. Refetching every run wastes time and hammers a government server. Cache like BrisHouse does.

**Files:**
- Create: `src/download.py`, `tests/test_download.py`

**Interfaces:**
- Consumes: `src.config` — `BASE_URL`, `SUPPLY_FILES`, `MAP_FILE`, `RAW`
- Produces: `download_one(name: str, dest_dir: Path = RAW, opener=urllib.request.urlopen) -> tuple[Path, bool]` returning (path, was_fetched). `main() -> None`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_download.py`:

```python
import pytest
from src.download import download_one


def test_existing_file_is_not_refetched(tmp_path):
    (tmp_path / "already.csv").write_text("cached")

    def explode(url):
        raise AssertionError(f"should not have fetched {url}")

    path, fetched = download_one("already.csv", dest_dir=tmp_path, opener=explode)
    assert fetched is False
    assert path.read_text() == "cached"


def test_missing_file_is_fetched(tmp_path):
    class FakeResponse:
        def read(self, *a):
            return b""
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    calls = []

    def fake_opener(url):
        calls.append(url)
        import io
        return io.BytesIO(b"col\n1\n")

    path, fetched = download_one("new.csv", dest_dir=tmp_path, opener=fake_opener)
    assert fetched is True
    assert path.read_bytes() == b"col\n1\n"
    assert calls[0].endswith("new.csv")
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_download.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'src.download'`

- [ ] **Step 3: Write downloader**

Create `src/download.py`:

```python
"""Fetch PBS Date-of-Supply CSVs. Cached: delete a file in data/raw to refetch."""
import shutil
import urllib.request
from pathlib import Path

from src.config import BASE_URL, MAP_FILE, RAW, SUPPLY_FILES


def download_one(name, dest_dir=RAW, opener=urllib.request.urlopen):
    dest = Path(dest_dir) / name
    if dest.exists():
        return dest, False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with opener(BASE_URL + name) as response, open(tmp, "wb") as out:
        shutil.copyfileobj(response, out)
    tmp.replace(dest)
    return dest, True


def main():
    for name in SUPPLY_FILES + [MAP_FILE]:
        path, fetched = download_one(name)
        size_mb = path.stat().st_size / 1e6
        print(f"{'downloaded' if fetched else 'cached':>10}  {size_mb:6.1f} MB  {path.name}")


if __name__ == "__main__":
    main()
```

Note: `.part` then rename means an interrupted download never leaves a truncated file that the cache check would then accept as complete.

- [ ] **Step 4: Run test, verify it passes**

Run: `pytest tests/test_download.py -v`
Expected: 2 passed

- [ ] **Step 5: Run for real**

Run: `python -m src.download`
Expected: seven lines, all "downloaded", total roughly 180 MB. Second run prints "cached" for all seven.

- [ ] **Step 6: Record provenance**

Create `checks_findings.md`:

```markdown
# Data Checks

## Download provenance

Files retrieved from `https://www.pbs.gov.au/statistics/dos-and-dop/files/`.

| File | Bytes | Retrieved |
|---|---|---|
```

Fill the table from `ls -l data/raw`. PBS revises historical files; this records exactly what the results were built on.

- [ ] **Step 7: Commit**

```bash
git add src/download.py tests/test_download.py checks_findings.md
git commit -m "feat(download): add cached PBS source file downloader"
```

---

## Task 3: Load into DuckDB

**Why:** ~2M rows total across six files. Small. But DuckDB gives clean SQL for the derivation and keeps the repo off Postgres, which Olist already covers.

**Files:**
- Create: `src/load.py`, `tests/test_load.py`

**Interfaces:**
- Consumes: `src.config`
- Produces: `read_supply_csv(path) -> pd.DataFrame`; `read_item_map(path) -> pd.DataFrame` (column `FORM/STRENGTH` renamed to `form_strength`); `build(db_path=DB) -> duckdb.DuckDBPyConnection` creating tables `supply` and `item_map`. `item_map` has columns `item_code, drug_name, form_strength, atc5, group_key`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_load.py`:

```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_load.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'src.load'`

- [ ] **Step 3: Write loader**

Create `src/load.py`:

```python
"""Read Latin-1 PBS CSVs into DuckDB tables `supply` and `item_map`."""
import duckdb
import pandas as pd

from src.config import DB, ENCODING, MAP_FILE, RAW, SUPPLY_FILES

SUPPLY_DTYPES = {
    "MONTH_OF_SUPPLY": "int32",
    "ITEM_CODE": "string",
    "DRUG_TYPE": "string",
    "PATIENT_CAT": "string",
    "PHRMCY_TYPE": "string",
    "SCRIPT_TYPE": "string",
    "PRESCRIPTIONS": "int64",
    "PATIENT_CONTRIB": "float64",
    "GOVT_CONTRIB": "float64",
    "TOTAL_COST": "float64",
    "RETAIL_MARKUP": "float64",
    "PATIENT_NET_CONTRIB": "float64",
}


def read_supply_csv(path):
    return pd.read_csv(path, encoding=ENCODING, dtype=SUPPLY_DTYPES)


def read_item_map(path):
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
    """SQL expression for the drug-form group key. Used by load and derive."""
    return "upper(trim(drug_name)) || ' | ' || upper(trim(form_strength))"


def build(db_path=DB):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    supply = pd.concat(
        [read_supply_csv(RAW / name) for name in SUPPLY_FILES], ignore_index=True
    )
    item_map = read_item_map(RAW / MAP_FILE)

    con = duckdb.connect(str(db_path))
    con.register("supply_df", supply)
    con.register("item_map_df", item_map)
    con.execute("CREATE OR REPLACE TABLE supply AS SELECT * FROM supply_df")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE item_map AS
        SELECT item_code, drug_name, form_strength, atc5,
               {group_key_expr()} AS group_key
        FROM item_map_df
        """
    )
    return con


def main():
    con = build()
    rows = con.execute("SELECT count(*) FROM supply").fetchone()[0]
    items = con.execute("SELECT count(*) FROM item_map").fetchone()[0]
    groups = con.execute("SELECT count(DISTINCT group_key) FROM item_map").fetchone()[0]
    months = con.execute(
        "SELECT min(MONTH_OF_SUPPLY), max(MONTH_OF_SUPPLY) FROM supply"
    ).fetchone()
    print(f"supply rows: {rows:,}")
    print(f"item codes:  {items:,}")
    print(f"drug groups: {groups:,}")
    print(f"months:      {months[0]} to {months[1]}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify it passes**

Run: `pytest tests/test_load.py -v`
Expected: 3 passed

- [ ] **Step 5: Run for real, sanity-check output**

Run: `python -m src.load`

Expected shape: supply rows around 2 million, item codes 12,162, months 202007 to 202606. If months do not span that range, a download is missing — go back to Task 2.

- [ ] **Step 6: Commit**

```bash
git add src/load.py tests/test_load.py
git commit -m "feat(load): load PBS CSVs into DuckDB with group keys"
```

---

# PHASE 2 — COHORT DERIVATION

Core of project. Everything downstream is worthless if this is wrong. Three tasks: first-appearance, classification, guards.

## Task 4: Item first-appearance months

**Why:** 60-day item code has no dispensing before its stage month. That is the whole signal.

**Files:**
- Create: `src/derive.py`, `tests/test_derive.py`

**Interfaces:**
- Consumes: `src.load.build`, `src.config.COMMUNITY_PHARMACY`
- Produces: `build_item_months(con) -> None` creating table `item_months(item_code, group_key, month, scripts)`. `build_item_first(con) -> None` creating table `item_first(item_code, group_key, first_month, total_scripts)`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_derive.py`:

```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_derive.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'src.derive'`

- [ ] **Step 3: Write it**

Create `src/derive.py`:

```python
"""Derive which drug-form groups became 60-day eligible, and when.

Treatment status comes from the dispensing data itself: every eligible medicine
received a new PBS item code for the 60-day quantity, so that code has zero
dispensing before its stage month. The government's own item-code list is not
used - the page hosting it now 404s.
"""
from src.config import COMMUNITY_PHARMACY


def build_item_months(con):
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
```

- [ ] **Step 4: Run test, verify it passes**

Run: `pytest tests/test_derive.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/derive.py tests/test_derive.py
git commit -m "feat(derive): compute item first-appearance months from dispensing"
```

---

## Task 5: Classify groups by stage

**Why:** A group is treated only if a new code appears exactly on a stage month AND the group already existed. Second half kills new-product false positives.

**Files:**
- Modify: `src/derive.py`
- Modify: `tests/test_derive.py`

**Interfaces:**
- Consumes: table `item_first` from Task 4
- Produces: `build_group_stage(con) -> None` creating `group_stage(group_key, stage, switch_month, group_first_month)`. `stage` is 1, 2, 3, or 0 for never-eligible. `switch_month` is the stage month, or NULL when stage is 0.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_derive.py`:

```python
from src.derive import build_group_stage


def test_new_code_on_stage1_month_with_existing_sibling_is_treated(con):
    build_item_months(con)
    build_item_first(con)
    build_group_stage(con)
    row = con.execute(
        "SELECT stage, switch_month FROM group_stage"
    ).fetchone()
    assert row == (1, 202309)


def test_group_that_only_appears_at_stage_month_is_not_treated():
    """A brand new product launching in Sept 2023 is not a 60-day listing."""
    c = duckdb.connect(":memory:")
    supply = pd.DataFrame(
        [("99999X", 202309, "S90", 50), ("99999X", 202310, "S90", 60)],
        columns=["ITEM_CODE", "MONTH_OF_SUPPLY", "PHRMCY_TYPE", "PRESCRIPTIONS"],
    )
    item_map = pd.DataFrame(
        [("99999X", "NEWDRUG", "Tablet 5 mg", "A01AA01", "NEWDRUG | TABLET 5 MG")],
        columns=["item_code", "drug_name", "form_strength", "atc5", "group_key"],
    )
    c.register("supply_df", supply)
    c.register("item_map_df", item_map)
    c.execute("CREATE TABLE supply AS SELECT * FROM supply_df")
    c.execute("CREATE TABLE item_map AS SELECT * FROM item_map_df")
    build_item_months(c)
    build_item_first(c)
    build_group_stage(c)
    assert c.execute("SELECT stage FROM group_stage").fetchone()[0] == 0


def test_earliest_stage_wins_when_group_gains_codes_twice():
    c = duckdb.connect(":memory:")
    supply = pd.DataFrame(
        [
            ("AAA", 202101, "S90", 10),
            ("BBB", 202309, "S90", 5),
            ("CCC", 202403, "S90", 5),
        ],
        columns=["ITEM_CODE", "MONTH_OF_SUPPLY", "PHRMCY_TYPE", "PRESCRIPTIONS"],
    )
    item_map = pd.DataFrame(
        [
            ("AAA", "D", "F", "X", "D | F"),
            ("BBB", "D", "F", "X", "D | F"),
            ("CCC", "D", "F", "X", "D | F"),
        ],
        columns=["item_code", "drug_name", "form_strength", "atc5", "group_key"],
    )
    c.register("supply_df", supply)
    c.register("item_map_df", item_map)
    c.execute("CREATE TABLE supply AS SELECT * FROM supply_df")
    c.execute("CREATE TABLE item_map AS SELECT * FROM item_map_df")
    build_item_months(c)
    build_item_first(c)
    build_group_stage(c)
    assert c.execute("SELECT stage FROM group_stage").fetchone()[0] == 1
```

- [ ] **Step 2: Run tests, verify the three new ones fail**

Run: `pytest tests/test_derive.py -v`
Expected: FAIL, `ImportError: cannot import name 'build_group_stage'`

- [ ] **Step 3: Write it**

Append to `src/derive.py`:

```python
from src.config import STAGE_MONTHS


def build_group_stage(con):
    s1, s2, s3 = STAGE_MONTHS[1], STAGE_MONTHS[2], STAGE_MONTHS[3]
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
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `pytest tests/test_derive.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/derive.py tests/test_derive.py
git commit -m "feat(derive): classify drug groups by 60-day eligibility stage"
```

---

## Task 6: Misclassification guards

**Why:** Spec section 7.2. Four failure modes. Guards flag, they do not silently drop. Human reads the flags.

**Files:**
- Create: `src/guards.py`, `tests/test_guards.py`

**Interfaces:**
- Consumes: tables `item_months`, `item_first`, `group_stage`
- Produces: `run_guards(con, window=6) -> pd.DataFrame` with columns `group_key, guard, detail`. One row per flagged group per guard. Empty frame means nothing flagged.

- [ ] **Step 1: Write the failing test**

Create `tests/test_guards.py`:

```python
import duckdb
import pandas as pd

from src.guards import run_guards


def _seed(rows):
    """rows: (item_code, month, scripts). All map to one group with a 60-day code BBB."""
    c = duckdb.connect(":memory:")
    im = pd.DataFrame(
        [(i, "D", "F", "X", "D | F") for i in {r[0] for r in rows}],
        columns=["item_code", "drug_name", "form_strength", "atc5", "group_key"],
    )
    months = pd.DataFrame(rows, columns=["item_code", "month", "scripts"])
    months["group_key"] = "D | F"
    first = months.groupby(["item_code", "group_key"], as_index=False).agg(
        first_month=("month", "min"), total_scripts=("scripts", "sum")
    )
    stage = pd.DataFrame(
        [("D | F", 202101, 1, 202309)],
        columns=["group_key", "group_first_month", "stage", "switch_month"],
    )
    for name, df in [("item_map", im), ("item_months", months), ("item_first", first), ("group_stage", stage)]:
        c.register(f"{name}_df", df)
        c.execute(f"CREATE TABLE {name} AS SELECT * FROM {name}_df")
    return c


def test_clean_substitution_is_not_flagged():
    rows = [("AAA", m, 100) for m in [202303, 202304, 202305, 202306, 202307, 202308]]
    rows += [("AAA", m, s) for m, s in zip(
        [202309, 202310, 202311, 202312, 202401, 202402], [90, 80, 70, 60, 55, 50])]
    rows += [("BBB", m, s) for m, s in zip(
        [202309, 202310, 202311, 202312, 202401, 202402], [5, 10, 15, 20, 22, 25])]
    flags = run_guards(_seed(rows))
    assert flags.empty


def test_volume_added_not_shifted_is_flagged_as_new_brand():
    """30-day scripts do not fall. That is a new product, not a 60-day listing."""
    rows = [("AAA", m, 100) for m in
            [202303, 202304, 202305, 202306, 202307, 202308,
             202309, 202310, 202311, 202312, 202401, 202402]]
    rows += [("BBB", m, 50) for m in
             [202309, 202310, 202311, 202312, 202401, 202402]]
    flags = run_guards(_seed(rows))
    assert "no_substitution" in set(flags["guard"])


def test_thirty_day_code_dying_completely_is_flagged_as_relisting():
    rows = [("AAA", m, 100) for m in
            [202303, 202304, 202305, 202306, 202307, 202308]]
    rows += [("BBB", m, 50) for m in
             [202309, 202310, 202311, 202312, 202401, 202402]]
    flags = run_guards(_seed(rows))
    assert "possible_relisting" in set(flags["guard"])
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_guards.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'src.guards'`

- [ ] **Step 3: Write guards**

Create `src/guards.py`:

```python
"""Flag drug groups whose 60-day classification may be wrong.

Guards flag; they never drop. A human reads checks_findings.md and decides.
"""
import pandas as pd

from src.config import SUPPLY_MULTIPLIER

NO_SUBSTITUTION = "no_substitution"
POSSIBLE_RELISTING = "possible_relisting"
LOW_UPTAKE = "low_uptake"


def _group_frames(con, window):
    """Per treated group: monthly 30-day and 60-day scripts, window months each side."""
    return con.execute(
        """
        SELECT g.group_key,
               g.switch_month,
               im.month,
               SUM(CASE WHEN f.first_month >= g.switch_month THEN im.scripts ELSE 0 END) AS scripts_60,
               SUM(CASE WHEN f.first_month <  g.switch_month THEN im.scripts ELSE 0 END) AS scripts_30
        FROM group_stage g
        JOIN item_first f  ON f.group_key = g.group_key
        JOIN item_months im ON im.item_code = f.item_code
        WHERE g.stage > 0
        GROUP BY 1, 2, 3
        ORDER BY 1, 3
        """
    ).df()


def _months_before(switch, n):
    """n calendar months strictly before switch, as YYYYMM ints."""
    year, month = divmod(switch, 100)
    out = []
    for _ in range(n):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
        out.append(year * 100 + month)
    return sorted(out)


def _months_from(switch, n):
    year, month = divmod(switch, 100)
    out = [switch]
    for _ in range(n - 1):
        month += 1
        if month == 13:
            year, month = year + 1, 1
        out.append(year * 100 + month)
    return out


def run_guards(con, window=6):
    df = _group_frames(con, window)
    flags = []
    for group_key, g in df.groupby("group_key"):
        switch = int(g["switch_month"].iloc[0])
        pre_months = _months_before(switch, window)
        post_months = _months_from(switch, window)
        pre = g[g["month"].isin(pre_months)]
        post = g[g["month"].isin(post_months)]
        if pre.empty or post.empty:
            continue

        pre_30 = pre["scripts_30"].mean()
        post_30 = post["scripts_30"].mean()
        post_60 = post["scripts_60"].mean()

        # Guard 1: genuine 60-day listing shifts volume; a new brand adds volume.
        if post_60 > 0 and post_30 >= pre_30:
            flags.append((group_key, NO_SUBSTITUTION,
                          f"30-day mean {pre_30:.0f} -> {post_30:.0f}, did not fall"))

        # Guard 3: substitution leaves the 30-day code alive; relisting kills it.
        if pre_30 > 0 and post_30 == 0:
            flags.append((group_key, POSSIBLE_RELISTING,
                          f"30-day scripts fell to zero after {switch}"))

        # Guard 4: near-zero uptake suggests the sibling was matched wrongly.
        total_post = post_30 + post_60
        if total_post > 0 and post_60 / total_post < 0.05:
            flags.append((group_key, LOW_UPTAKE,
                          f"60-day share {post_60 / total_post:.1%} of group volume"))

    return pd.DataFrame(flags, columns=["group_key", "guard", "detail"])
```

- [ ] **Step 4: Run test, verify it passes**

Run: `pytest tests/test_guards.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/guards.py tests/test_guards.py
git commit -m "feat(guards): flag possible 60-day misclassification"
```

---

# PHASE 3 — VALIDATION GATE

## Task 7: Anchor check against published figures — HARD GATE

**Why:** Government said Stage 1 = 92 medicines, 256 PBS items. Derivation never touched that number. If derived count lands in band, rule is independently confirmed. Outside band, rule is wrong.

**Supervisor rule: do not proceed past this task on a failed anchor. Do not widen the band. Fix the rule, rerun.**

**Files:**
- Create: `src/anchor.py`, `tests/test_anchor.py`

**Interfaces:**
- Consumes: tables `item_first`, `group_stage`, config bands
- Produces: `anchor_counts(con) -> dict` with keys `new_items`, `all_items`, `drugs`. `check_anchor(counts) -> tuple[bool, str]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_anchor.py`:

```python
from src.anchor import check_anchor


def test_counts_inside_band_pass():
    ok, msg = check_anchor({"new_items": 256, "all_items": 512, "drugs": 92})
    assert ok is True
    assert "256" in msg


def test_item_count_outside_band_fails():
    ok, msg = check_anchor({"new_items": 180, "all_items": 360, "drugs": 92})
    assert ok is False
    assert "230" in msg


def test_drug_count_outside_band_fails():
    ok, msg = check_anchor({"new_items": 256, "all_items": 512, "drugs": 140})
    assert ok is False
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_anchor.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'src.anchor'`

- [ ] **Step 3: Write it**

Create `src/anchor.py`:

```python
"""Validate the derivation against the government's published Stage 1 figures.

Published: 92 medicines, 256 PBS items. Neither number was used to build the
derivation rule, so agreement is independent confirmation.

"256 items" is ambiguous - it may count the new 60-day codes only, or the
30-day codes made eligible. Both counts are reported; the band is applied to
the new-code count.
"""
import sys

from src.config import ANCHOR_DRUG_BAND, ANCHOR_ITEM_BAND, STAGE_MONTHS


def anchor_counts(con):
    s1 = STAGE_MONTHS[1]
    row = con.execute(
        f"""
        SELECT
          COUNT(DISTINCT CASE WHEN f.first_month = {s1} THEN f.item_code END) AS new_items,
          COUNT(DISTINCT f.item_code)                                          AS all_items,
          COUNT(DISTINCT m.drug_name)                                          AS drugs
        FROM group_stage g
        JOIN item_first f ON f.group_key = g.group_key
        JOIN item_map   m ON m.item_code = f.item_code
        WHERE g.stage = 1
        """
    ).fetchone()
    return {"new_items": row[0], "all_items": row[1], "drugs": row[2]}


def check_anchor(counts):
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
```

- [ ] **Step 4: Run test, verify it passes**

Run: `pytest tests/test_anchor.py -v`
Expected: 3 passed

- [ ] **Step 5: Build the real cohort and run the gate**

Create `src/build_cohort.py`:

```python
"""Run the full derivation and write cohort.parquet. Fails loudly on a bad anchor."""
import sys

from src.anchor import anchor_counts, check_anchor
from src.config import DB, PROCESSED
from src.derive import build_group_stage, build_item_first, build_item_months
from src.guards import run_guards
from src.load import build


def main():
    con = build(DB)
    build_item_months(con)
    build_item_first(con)
    build_group_stage(con)

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
```

Run: `python -m src.build_cohort`

- [ ] **Step 6: GATE — read the anchor output**

If anchor passed: continue.

If anchor failed, the likely causes in order of probability:

1. `FORM/STRENGTH` text differs between 30- and 60-day listings (count too low). Inspect: list Stage 1 groups and compare against `atc5` classes that contain treated groups but have untreated members.
2. Some Stage 1 items had zero dispensing in their first month and appear at 202310 instead (count too low). Widen the stage test to a two-month window and note the change in the spec.
3. New brands launched at 202309 coincidentally (count too high). Apply the `no_substitution` guard as a filter rather than a flag.

Pick one, change the rule, rerun. Record what you changed and why in `checks_findings.md`. **Do not change the band.**

- [ ] **Step 7: Review guard flags by hand**

Run: `open data/processed/guard_flags.csv`

Read every flagged group. For each, decide keep or drop, and write the decision in `checks_findings.md`. This is manual work and it is the point — a reviewer will ask whether you looked.

- [ ] **Step 8: Add the real-data integration test**

Spec section 11. The unit tests use synthetic fixtures; this one asserts on the actual
atorvastatin case verified by hand during design. It needs `data/raw` present, so it is
marked `integration` and excluded from the default run.

Create `pytest.ini`:

```ini
[pytest]
markers =
    integration: requires downloaded PBS data in data/raw
```

Create `tests/test_integration_derive.py`:

```python
import pandas as pd
import pytest

from src.config import PROCESSED

pytestmark = pytest.mark.integration

ATOR = "ATORVASTATIN | TABLET 40 MG (AS CALCIUM)"
AMOX_PREFIX = "AMOXYCILLIN"


@pytest.fixture(scope="module")
def cohort():
    path = PROCESSED / "cohort.parquet"
    if not path.exists():
        pytest.skip("run `python -m src.build_cohort` first")
    return pd.read_parquet(path)


def test_atorvastatin_40mg_is_stage_one(cohort):
    row = cohort[cohort["group_key"] == ATOR]
    assert len(row) == 1, f"expected one group for {ATOR}, got {len(row)}"
    assert row["stage"].iloc[0] == 1
    assert row["switch_month"].iloc[0] == 202309


def test_amoxycillin_is_never_eligible(cohort):
    amox = cohort[cohort["drug_name"].str.startswith(AMOX_PREFIX, na=False)]
    assert len(amox) > 0, "amoxycillin missing from cohort entirely"
    assert (amox["stage"] == 0).all()


def test_atorvastatin_supply_months_hold_across_the_switch():
    path = PROCESSED / "panel.parquet"
    if not path.exists():
        pytest.skip("run `python -m src.panel` first")
    panel = pd.read_parquet(path)
    g = panel[panel["group_key"] == ATOR].groupby("month")["supply_months"].sum()
    pre = g.loc[202303:202308].mean()
    post = g.loc[202403:202408].mean()
    assert abs(post - pre) / pre < 0.15, (
        f"supply-months moved {100 * (post - pre) / pre:.1f}% across the switch; "
        "expected roughly flat. Check the 60-day tagging in src/panel.py."
    )
```

Note the third test also needs `panel.parquet`, which Task 8 produces. It skips cleanly
until then.

- [ ] **Step 9: Run the integration tests**

```bash
pytest -m integration -v
```

Expected: the two cohort tests pass; the panel test skips until Task 8 is done. If
`test_atorvastatin_40mg_is_stage_one` fails, the group key does not match — print the
actual keys with `python -c "import pandas as pd; d=pd.read_parquet('data/processed/cohort.parquet'); print([k for k in d.group_key if 'ATORVA' in k])"` and fix the expected constant, not the derivation.

- [ ] **Step 10: Commit**

```bash
git add src/anchor.py src/build_cohort.py tests/test_anchor.py tests/test_integration_derive.py pytest.ini data/processed/cohort.parquet data/processed/guard_flags.csv checks_findings.md
git commit -m "feat(anchor): validate derived cohort against published Stage 1 figures"
```

---

# PHASE 4 — PANEL AND CONTROLS

## Task 8: Build the analysis panel

**Files:**
- Create: `src/panel.py`, `tests/test_panel.py`

**Interfaces:**
- Consumes: tables `supply`, `item_map`, `item_first`, `group_stage`
- Produces: `build_panel(con) -> pd.DataFrame` with columns `group_key, month, patient_type, script_type, scripts_30, scripts_60, scripts_total, supply_months, patient_contrib, govt_contrib, total_cost`. Writes `data/processed/panel.parquet`.

`script_type` is kept in the grain (values `ABOVE CO-PAYMENT`, `UNDER CO-PAYMENT`) because under-co-payment scripts carry `GOVT_CONTRIB = 0` by construction, and the cost robustness check in Task 16 must be able to exclude them. Every downstream consumer that does not care about it sums over it.

- [ ] **Step 1: Write the failing test**

Create `tests/test_panel.py`:

```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_panel.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'src.panel'`

- [ ] **Step 3: Write it**

Create `src/panel.py`:

```python
"""Build the group x month x patient_type analysis panel."""
from src.config import (COMMUNITY_PHARMACY, CONCESSIONAL, GENERAL, PROCESSED,
                        SUPPLY_MULTIPLIER)

_NEVER = 999999  # sentinel switch month for never-eligible groups


def build_panel(con):
    conc = ", ".join(f"'{c}'" for c in CONCESSIONAL)
    gen = ", ".join(f"'{g}'" for g in GENERAL)
    df = con.execute(
        f"""
        WITH tagged AS (
            SELECT m.group_key,
                   s.MONTH_OF_SUPPLY AS month,
                   CASE WHEN s.PATIENT_CAT IN ({conc}) THEN 'concessional'
                        ELSE 'general' END AS patient_type,
                   s.SCRIPT_TYPE AS script_type,
                   CASE WHEN f.first_month >= COALESCE(g.switch_month, {_NEVER})
                        THEN 60 ELSE 30 END AS days,
                   s.PRESCRIPTIONS, s.PATIENT_CONTRIB, s.GOVT_CONTRIB, s.TOTAL_COST
            FROM supply s
            JOIN item_map   m ON m.item_code = s.ITEM_CODE
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
```

- [ ] **Step 4: Run test, verify it passes**

Run: `pytest tests/test_panel.py -v`
Expected: 3 passed

- [ ] **Step 5: Run for real**

Run: `python -m src.panel`
Expected: months 202007 to 202606, group count matching cohort.parquet.

- [ ] **Step 6: Commit**

```bash
git add src/panel.py tests/test_panel.py data/processed/panel.parquet
git commit -m "feat(panel): build group-month-patient analysis panel"
```

---

## Task 9: Match never-eligible controls (Arm B)

**Why:** Spec section 8. Arm A (not-yet-treated) window closes March 2024. Arm B extends horizon. Coarsened exact matching on ATC-1 and volume decile. No propensity model — harder to explain, not more defensible at n=250.

**Files:**
- Create: `src/controls.py`, `tests/test_controls.py`

**Interfaces:**
- Consumes: `data/processed/panel.parquet`, `data/processed/cohort.parquet`
- Produces: `match_controls(panel, cohort, pre_end=202308) -> pd.DataFrame` with columns `group_key, stratum, role` where role is `treated` or `matched_control`. Writes `data/processed/matched_controls.parquet`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_controls.py`:

```python
import pandas as pd

from src.controls import assign_strata, match_controls


def test_stratum_combines_atc1_and_volume_decile():
    cohort = pd.DataFrame(
        [("A | X", 1, "C10AA05"), ("B | Y", 0, "C07AB02"), ("C | Z", 0, "N06AB03")],
        columns=["group_key", "stage", "atc5"],
    )
    volumes = pd.Series([1000.0, 900.0, 10.0], index=["A | X", "B | Y", "C | Z"])
    strata = assign_strata(cohort, volumes)
    assert strata.loc["A | X", "atc1"] == "C"
    assert strata.loc["C | Z", "atc1"] == "N"
    # similar volume and same ATC-1 must land in the same stratum
    assert strata.loc["A | X", "stratum"] == strata.loc["B | Y", "stratum"]


def test_only_never_eligible_groups_become_controls():
    cohort = pd.DataFrame(
        [("A | X", 1, "C10AA05"), ("B | Y", 0, "C07AB02"), ("D | W", 2, "C08CA01")],
        columns=["group_key", "stage", "atc5"],
    )
    panel = pd.DataFrame(
        [(g, m, "concessional", 100.0)
         for g in ["A | X", "B | Y", "D | W"]
         for m in [202301, 202302, 202303]],
        columns=["group_key", "month", "patient_type", "supply_months"],
    )
    out = match_controls(panel, cohort)
    controls = set(out[out["role"] == "matched_control"]["group_key"])
    assert controls == {"B | Y"}  # stage 2 group is not a never-eligible control
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_controls.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'src.controls'`

- [ ] **Step 3: Write it**

Create `src/controls.py`:

```python
"""Coarsened exact matching of never-eligible groups to Stage 1 groups.

Matched on ATC level-1 class and pre-period volume decile. Deliberately simple:
with ~250 treated groups a stratified match is easier to defend and explain than
a propensity model, and the explanation is what a reviewer actually reads.
"""
import numpy as np
import pandas as pd

from src.config import PROCESSED

PRE_END = 202308  # last month before Stage 1


def assign_strata(cohort, volumes):
    df = cohort.set_index("group_key").copy()
    df["atc1"] = df["atc5"].str[0].fillna("Z")
    df["volume"] = volumes.reindex(df.index).fillna(0.0)
    ranks = df["volume"].rank(pct=True, method="average")
    df["decile"] = np.ceil(ranks * 10).clip(1, 10).astype(int)
    df["stratum"] = df["atc1"] + "-" + df["decile"].astype(str)
    return df[["atc1", "decile", "stratum", "volume"]]


def match_controls(panel, cohort, pre_end=PRE_END):
    pre = panel[panel["month"] <= pre_end]
    volumes = pre.groupby("group_key")["supply_months"].mean()
    strata = assign_strata(cohort, volumes)
    stage = cohort.set_index("group_key")["stage"]

    treated = strata[stage.reindex(strata.index) == 1]
    never = strata[stage.reindex(strata.index) == 0]

    keep_strata = set(treated["stratum"]) & set(never["stratum"])
    rows = [(g, s, "treated") for g, s in treated["stratum"].items()
            if s in keep_strata]
    rows += [(g, s, "matched_control") for g, s in never["stratum"].items()
             if s in keep_strata]
    return pd.DataFrame(rows, columns=["group_key", "stratum", "role"])


def main():
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    cohort = pd.read_parquet(PROCESSED / "cohort.parquet")
    out = match_controls(panel, cohort)
    out.to_parquet(PROCESSED / "matched_controls.parquet", index=False)
    counts = out["role"].value_counts()
    print(counts.to_string())
    print(f"strata used: {out['stratum'].nunique()}")
    unmatched = cohort[(cohort["stage"] == 1)]["group_key"].nunique() - counts.get("treated", 0)
    print(f"Stage 1 groups with no available control: {unmatched}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify it passes**

Run: `pytest tests/test_controls.py -v`
Expected: 2 passed

- [ ] **Step 5: Run for real, record unmatched count**

Run: `python -m src.controls`

Write the unmatched count into `checks_findings.md`. If more than 30% of Stage 1 groups have no available control, Arm B is weak — say so in the writeup and lean on Arm A.

- [ ] **Step 6: Commit**

```bash
git add src/controls.py tests/test_controls.py data/processed/matched_controls.parquet checks_findings.md
git commit -m "feat(controls): match never-eligible control groups by ATC and volume"
```

---

# PHASE 5 — CHECKS REPORT

## Task 10: Write checks_findings.md properly

**Why:** This file is where the skeptical reader goes. Half the credibility lives here.

**Files:**
- Create: `src/checks.py`
- Modify: `checks_findings.md`

**Interfaces:**
- Consumes: `panel.parquet`, `cohort.parquet`, `guard_flags.csv`
- Produces: `january_effect(panel) -> pd.DataFrame` with columns `month_of_year, mean_govt_per_script, mean_scripts`. `summary(panel, cohort) -> str`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_checks.py`:

```python
import pandas as pd

from src.checks import january_effect


def test_january_effect_isolates_calendar_month():
    panel = pd.DataFrame(
        [("g", 202312, 100, 1000.0), ("g", 202401, 100, 500.0),
         ("g", 202412, 100, 1000.0), ("g", 202501, 100, 500.0)],
        columns=["group_key", "month", "scripts_total", "govt_contrib"],
    )
    out = january_effect(panel)
    jan = out[out["month_of_year"] == 1]["mean_govt_per_script"].iloc[0]
    dec = out[out["month_of_year"] == 12]["mean_govt_per_script"].iloc[0]
    assert jan < dec
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_checks.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'src.checks'`

- [ ] **Step 3: Write it**

Create `src/checks.py`:

```python
"""Diagnostics for checks_findings.md."""
import pandas as pd

from src.config import PROCESSED


def january_effect(panel):
    """Government cost per script by calendar month.

    The safety net resets each January, so government cost drops across all
    medicines including controls. Any model without calendar-month fixed
    effects will attribute part of that drop to the policy.
    """
    df = panel.copy()
    df["month_of_year"] = df["month"] % 100
    grouped = df.groupby("month_of_year").agg(
        govt=("govt_contrib", "sum"), scripts=("scripts_total", "sum")
    )
    grouped["mean_govt_per_script"] = grouped["govt"] / grouped["scripts"]
    grouped["mean_scripts"] = grouped["scripts"]
    return grouped.reset_index()[
        ["month_of_year", "mean_govt_per_script", "mean_scripts"]
    ]


def summary(panel, cohort):
    stages = cohort["stage"].value_counts().sort_index()
    lines = [
        f"panel rows: {len(panel):,}",
        f"months: {panel['month'].min()} to {panel['month'].max()}",
        "groups by stage:",
    ]
    for stage, n in stages.items():
        label = "never eligible" if stage == 0 else f"Stage {stage}"
        lines.append(f"  {label}: {n:,}")
    return "\n".join(lines)


def main():
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    cohort = pd.read_parquet(PROCESSED / "cohort.parquet")
    print(summary(panel, cohort))
    print()
    print(january_effect(panel).to_string(index=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify it passes**

Run: `pytest tests/test_checks.py -v`
Expected: 1 passed

- [ ] **Step 5: Write the report**

Run `python -m src.checks`, then write `checks_findings.md` with these sections, using the real numbers:

1. **Download provenance** — table of files, bytes, retrieval date (already started in Task 2).
2. **Derivation anchor** — derived counts against published 92/256, and whether it passed first time or what was changed.
3. **Guard flags** — every flagged group, the guard, and your keep/drop decision with reasoning.
4. **Control matching** — strata used, Stage 1 groups left unmatched.
5. **The January confounder** — the calendar-month table, and the statement that all specifications carry calendar-month fixed effects because of it.
6. **Known limitations of the data** — no geography, no quantity field, no patients.

- [ ] **Step 6: Commit**

```bash
git add src/checks.py tests/test_checks.py checks_findings.md
git commit -m "docs(checks): document derivation validation and January confounder"
```

---

# PHASE 6 — ESTIMATION

Python done. R from here. Panel is a Parquet file; R reads it with `arrow`.

## Task 11: R environment and panel prep

**Files:**
- Create: `analysis/00_prep.R`, `analysis/README.md`

**Interfaces:**
- Consumes: `data/processed/panel.parquet`, `cohort.parquet`, `matched_controls.parquet`
- Produces: `analysis/prep_panel()` returning a data.frame with columns `gid` (int group id), `t` (int month index, 1 = 202007), `g` (int first-treated t, 0 if never), `patient_type`, `scripts_total`, `supply_months`, `log_scripts`, `log_supply`, `govt_per_supply`, `patient_per_supply`, `month_of_year`, `stage`, `arm_b` (logical).

- [ ] **Step 1: Install R packages**

```bash
R -e 'install.packages(c("arrow","did","fixest","ggplot2","dplyr","readr","purrr","tibble"), repos="https://cloud.r-project.org")'
```

- [ ] **Step 2: Write prep script**

Create `analysis/00_prep.R`:

```r
# Shared panel prep. Sourced by every other analysis script.
suppressPackageStartupMessages({
  library(arrow); library(dplyr)
})

MONTH_ORIGIN <- 202007  # t = 1

month_to_t <- function(yyyymm) {
  year <- yyyymm %/% 100
  month <- yyyymm %% 100
  oy <- MONTH_ORIGIN %/% 100
  om <- MONTH_ORIGIN %% 100
  (year - oy) * 12 + (month - om) + 1
}

prep_panel <- function(root = ".") {
  panel  <- read_parquet(file.path(root, "data/processed/panel.parquet"))
  cohort <- read_parquet(file.path(root, "data/processed/cohort.parquet"))
  ctrls  <- read_parquet(file.path(root, "data/processed/matched_controls.parquet"))

  ids <- tibble(group_key = sort(unique(panel$group_key))) |>
    mutate(gid = row_number())

  panel |>
    left_join(cohort |> select(group_key, stage, switch_month), by = "group_key") |>
    left_join(ids, by = "group_key") |>
    mutate(
      t = month_to_t(month),
      g = ifelse(is.na(switch_month), 0L, as.integer(month_to_t(switch_month))),
      month_of_year = factor(month %% 100),
      log_scripts = log(scripts_total + 1),
      log_supply  = log(supply_months + 1),
      govt_per_supply    = govt_contrib / pmax(supply_months, 1),
      patient_per_supply = patient_contrib / pmax(supply_months, 1),
      arm_b = group_key %in% ctrls$group_key
    ) |>
    filter(!is.na(gid))
}
```

Note `+1` inside the logs: some group-months have zero dispensing, and `log(0)` is `-Inf`. Stated in the writeup as a transformation choice.

- [ ] **Step 3: Verify it loads**

```bash
R -q -e 'source("analysis/00_prep.R"); d <- prep_panel(); cat(nrow(d), "rows,", length(unique(d$gid)), "groups, t range", range(d$t), "\n")'
```

Expected: t range 1 to 72.

- [ ] **Step 4: Commit**

```bash
git add analysis/00_prep.R
git commit -m "feat(analysis): add R panel prep with month index and treatment timing"
```

---

## Task 12: The naive estimate — the wrong answer, on purpose

**Why:** Report the misleading number first. It motivates everything after it. Without it the project is a chart; with it, it is an argument.

**Files:**
- Create: `analysis/01_naive.R`
- Output: `reports/estimates_naive.csv`, `reports/figures/naive_scripts.png`

**Interfaces:**
- Consumes: `prep_panel()` from Task 11
- Produces: `reports/estimates_naive.csv` with columns `outcome, estimate, se, ci_lo, ci_hi, control_arm`

- [ ] **Step 1: Write it**

Create `analysis/01_naive.R`:

```r
# The naive result: raw prescription counts, before and after, Stage 1 only.
# This number is wrong. It is reported first because it is what a reader
# expects, and the rest of the analysis exists to correct it.
source("analysis/00_prep.R")
suppressPackageStartupMessages({ library(ggplot2); library(readr) })

d <- prep_panel()
s1 <- d |> filter(stage == 1)

pre  <- s1 |> filter(month >= 202209, month <= 202308) |>
  summarise(scripts = sum(scripts_total)) |> pull(scripts)
post <- s1 |> filter(month >= 202309, month <= 202408) |>
  summarise(scripts = sum(scripts_total)) |> pull(scripts)

pct <- 100 * (post - pre) / pre
cat(sprintf("Stage 1 scripts, 12 months before: %s\n", format(pre, big.mark = ",")))
cat(sprintf("Stage 1 scripts, 12 months after:  %s\n", format(post, big.mark = ",")))
cat(sprintf("Naive change: %.1f%%\n", pct))

write_csv(
  tibble(outcome = "scripts_naive_pct_change", estimate = pct,
         se = NA_real_, ci_lo = NA_real_, ci_hi = NA_real_,
         control_arm = "none (before/after only)"),
  "reports/estimates_naive.csv"
)

monthly <- s1 |> group_by(month) |>
  summarise(scripts = sum(scripts_total), supply = sum(supply_months), .groups = "drop") |>
  mutate(date = as.Date(paste0(month %/% 100, "-", sprintf("%02d", month %% 100), "-01")))

p <- ggplot(monthly, aes(date)) +
  geom_line(aes(y = scripts, colour = "Prescriptions")) +
  geom_line(aes(y = supply,  colour = "Supply-months")) +
  geom_vline(xintercept = as.Date("2023-09-01"), linetype = "dashed") +
  labs(title = "Stage 1 medicines: prescriptions fell, supply did not",
       subtitle = "Dashed line: 60-day dispensing begins, 1 September 2023",
       x = NULL, y = NULL, colour = NULL) +
  theme_minimal()

ggsave("reports/figures/naive_scripts.png", p, width = 9, height = 5, dpi = 150)
```

- [ ] **Step 2: Run it**

```bash
Rscript analysis/01_naive.R
```

Expected: a negative percentage in the region of -20% to -30%, based on the atorvastatin pattern verified during design.

- [ ] **Step 3: Look at the figure**

Open `reports/figures/naive_scripts.png`. The two lines must diverge at the dashed line. If they do not, the panel's `supply_months` is wrong — go back to Task 8.

- [ ] **Step 4: Commit**

```bash
git add analysis/01_naive.R reports/estimates_naive.csv reports/figures/naive_scripts.png
git commit -m "feat(analysis): add naive before-after estimate and headline figure"
```

---

## Task 13: Primary estimate — staggered DiD on supply-months

**Why:** The real answer. Callaway-Sant'Anna because timing is staggered and plain two-way fixed effects is biased under staggered adoption with heterogeneous effects.

**Files:**
- Create: `analysis/02_did.R`
- Output: `reports/estimates_primary.csv`

**Interfaces:**
- Consumes: `prep_panel()`
- Produces: `reports/estimates_primary.csv` with columns `outcome, control_arm, estimate, se, ci_lo, ci_hi, n_groups`

- [ ] **Step 1: Write it**

Create `analysis/02_did.R`:

```r
# Primary estimate: did treatment supply change when 60-day dispensing began?
# Callaway-Sant'Anna, both control arms, aggregated to a single ATT.
source("analysis/00_prep.R")
suppressPackageStartupMessages({ library(did); library(readr); library(dplyr) })

d <- prep_panel() |>
  group_by(gid, t) |>
  summarise(across(c(scripts_total, supply_months, govt_contrib, patient_contrib), sum),
            g = first(g), stage = first(stage), arm_b = first(arm_b),
            month_of_year = first(month_of_year), .groups = "drop") |>
  mutate(log_supply = log(supply_months + 1),
         log_scripts = log(scripts_total + 1))

run_cs <- function(data, yname, control_group) {
  att <- att_gt(
    yname = yname, tname = "t", idname = "gid", gname = "g",
    data = data, control_group = control_group,
    clustervars = "gid", est_method = "reg",
    allow_unbalanced_panel = TRUE, base_period = "universal"
  )
  agg <- aggte(att, type = "simple", na.rm = TRUE)
  tibble(
    outcome = yname,
    control_arm = control_group,
    estimate = agg$overall.att,
    se = agg$overall.se,
    ci_lo = agg$overall.att - 1.96 * agg$overall.se,
    ci_hi = agg$overall.att + 1.96 * agg$overall.se,
    n_groups = length(unique(data$gid))
  )
}

# Arm A: not-yet-treated. All groups, later stages act as controls.
arm_a_supply  <- run_cs(d, "log_supply",  "notyettreated")
arm_a_scripts <- run_cs(d, "log_scripts", "notyettreated")

# Arm B: matched never-eligible only. Stage 1 treated plus matched controls.
d_b <- d |> filter(stage == 1 | (stage == 0 & arm_b))
arm_b_supply  <- run_cs(d_b, "log_supply",  "nevertreated")
arm_b_scripts <- run_cs(d_b, "log_scripts", "nevertreated")

out <- bind_rows(arm_a_supply, arm_a_scripts, arm_b_supply, arm_b_scripts)
print(out)
write_csv(out, "reports/estimates_primary.csv")

cat("\nInterpretation: estimates are in log points. Multiply by 100 for approximate percent.\n")
```

- [ ] **Step 2: Run it**

```bash
Rscript analysis/02_did.R
```

- [ ] **Step 3: Read the two arms against each other**

If the supply-months estimates from Arm A and Arm B are within roughly one standard error of each other, report as robust. If they diverge materially, that divergence goes in `findings.md` as a result in its own right. **Do not pick the more convenient arm.**

- [ ] **Step 4: Add the Sun-Abraham cross-check**

Spec section 9.2 requires a second estimator on the same design. Different maths, same identification. Append to `analysis/02_did.R`:

```r
# Cross-check: Sun-Abraham interaction-weighted estimator. Different estimator,
# same design. Material disagreement with Callaway-Sant'Anna is itself a finding.
# Calendar-month fixed effects enter explicitly here (spec 9.5) - the January
# safety-net reset moves all groups, treated and control alike.
suppressPackageStartupMessages(library(fixest))

d_sa <- d |>
  mutate(
    month_of_year = factor(((t - 1 + 6) %% 12) + 1),  # t = 1 is July 2020
    cohort_g = ifelse(g == 0, 10000, g)               # fixest wants a large value for never-treated
  )

sa <- feols(
  log_supply ~ sunab(cohort_g, t) | gid + month_of_year,
  data = d_sa, cluster = ~gid
)
sa_att <- summary(sa, agg = "att")
print(sa_att)

sa_row <- tibble(
  outcome = "log_supply",
  control_arm = "sunab (never-treated implicit)",
  estimate = coef(sa_att)[[1]],
  se = se(sa_att)[[1]],
  ci_lo = coef(sa_att)[[1]] - 1.96 * se(sa_att)[[1]],
  ci_hi = coef(sa_att)[[1]] + 1.96 * se(sa_att)[[1]],
  n_groups = length(unique(d_sa$gid))
)
write_csv(bind_rows(out, sa_row), "reports/estimates_primary.csv")

cat("\nCallaway-Sant'Anna vs Sun-Abraham gap: ",
    sprintf("%.4f log points\n", abs(arm_a_supply$estimate - sa_row$estimate)))
```

- [ ] **Step 5: Run and compare the two estimators**

```bash
Rscript analysis/02_did.R
```

A gap under about 0.02 log points is agreement. A larger gap goes in `findings.md` with both numbers shown. Do not report only the one you prefer.

- [ ] **Step 6: Commit**

```bash
git add analysis/02_did.R reports/estimates_primary.csv
git commit -m "feat(analysis): add Callaway-Sant'Anna and Sun-Abraham estimates"
```

---

## Task 14: Event study and pre-trend test

**Why:** Parallel trends is an assumption. Leads test it. If leads are not flat, say so.

**Files:**
- Create: `analysis/03_event_study.R`
- Output: `reports/figures/event_study_supply.png`, `reports/event_study.csv`

**Interfaces:**
- Consumes: `prep_panel()`
- Produces: `reports/event_study.csv` with columns `event_time, estimate, se, ci_lo, ci_hi, outcome, control_arm`

- [ ] **Step 1: Write it**

Create `analysis/03_event_study.R`:

```r
# Event study: coefficients from -12 to +12 months around each group's switch.
# The pre-period coefficients are the load-bearing part. Flat leads support
# parallel trends; sloped leads do not, and that must be reported.
source("analysis/00_prep.R")
suppressPackageStartupMessages({
  library(did); library(ggplot2); library(readr); library(dplyr)
})

d <- prep_panel() |>
  group_by(gid, t) |>
  summarise(supply_months = sum(supply_months), g = first(g),
            stage = first(stage), arm_b = first(arm_b), .groups = "drop") |>
  mutate(log_supply = log(supply_months + 1))

event_study <- function(data, control_group, label) {
  att <- att_gt(yname = "log_supply", tname = "t", idname = "gid", gname = "g",
                data = data, control_group = control_group, clustervars = "gid",
                est_method = "reg", allow_unbalanced_panel = TRUE,
                base_period = "universal")
  dyn <- aggte(att, type = "dynamic", min_e = -12, max_e = 12, na.rm = TRUE)
  tibble(event_time = dyn$egt, estimate = dyn$att.egt, se = dyn$se.egt) |>
    mutate(ci_lo = estimate - 1.96 * se, ci_hi = estimate + 1.96 * se,
           outcome = "log_supply", control_arm = label)
}

es_a <- event_study(d, "notyettreated", "notyettreated")
es_b <- event_study(d |> filter(stage == 1 | (stage == 0 & arm_b)),
                    "nevertreated", "nevertreated")
es <- bind_rows(es_a, es_b)
write_csv(es, "reports/event_study.csv")

p <- ggplot(es, aes(event_time, estimate, colour = control_arm)) +
  geom_hline(yintercept = 0, linetype = "dotted") +
  geom_vline(xintercept = -0.5, linetype = "dashed") +
  geom_pointrange(aes(ymin = ci_lo, ymax = ci_hi), position = position_dodge(0.4)) +
  labs(title = "Effect on supply-months, by months since 60-day eligibility",
       subtitle = "Coefficients left of the dashed line test parallel trends",
       x = "Months relative to switch", y = "Log points", colour = "Control arm") +
  theme_minimal()

ggsave("reports/figures/event_study_supply.png", p, width = 9, height = 5, dpi = 150)

pre <- es |> filter(event_time < 0)
cat(sprintf("Pre-period coefficients significant at 95%%: %d of %d\n",
            sum(pre$ci_lo > 0 | pre$ci_hi < 0), nrow(pre)))
```

- [ ] **Step 2: Run it**

```bash
Rscript analysis/03_event_study.R
```

- [ ] **Step 3: GATE — read the pre-trend count**

If more than about 2 of 12 pre-period coefficients are individually significant, parallel trends is doubtful. Options, in order:

1. Restrict the pre-period window to 24 months and rerun.
2. Report the failure honestly and reframe the headline as descriptive rather than causal.

**Do not drop the event study to hide it.** An honest null with a documented pre-trend failure is a better portfolio piece than a confident estimate resting on an assumption you did not check.

- [ ] **Step 4: Commit**

```bash
git add analysis/03_event_study.R reports/event_study.csv reports/figures/event_study_supply.png
git commit -m "feat(analysis): add event study and parallel-trends test"
```

---

## Task 15: Cost outcomes, split by patient type

**Files:**
- Create: `analysis/04_cost.R`
- Output: `reports/estimates_cost.csv`, `reports/figures/cost_by_patient_type.png`

**Interfaces:**
- Consumes: `prep_panel()`
- Produces: `reports/estimates_cost.csv` with columns `outcome, patient_type, control_arm, estimate, se, ci_lo, ci_hi`

- [ ] **Step 1: Write it**

Create `analysis/04_cost.R`:

```r
# Secondary outcomes: cost per month of therapy, separately for concessional
# and general patients. Run twice - all scripts, then excluding under-co-payment
# scripts, which carry zero government contribution by construction.
source("analysis/00_prep.R")
suppressPackageStartupMessages({ library(did); library(readr); library(dplyr) })

d <- prep_panel()

fit_cost <- function(data, yname, ptype, control_group) {
  sub <- data |>
    filter(patient_type == ptype) |>
    group_by(gid, t) |>
    summarise(y = sum(.data[[yname]]) / pmax(sum(supply_months), 1),
              g = first(g), .groups = "drop")
  att <- att_gt(yname = "y", tname = "t", idname = "gid", gname = "g",
                data = sub, control_group = control_group, clustervars = "gid",
                est_method = "reg", allow_unbalanced_panel = TRUE,
                base_period = "universal")
  agg <- aggte(att, type = "simple", na.rm = TRUE)
  tibble(outcome = yname, patient_type = ptype, control_arm = control_group,
         estimate = agg$overall.att, se = agg$overall.se,
         ci_lo = agg$overall.att - 1.96 * agg$overall.se,
         ci_hi = agg$overall.att + 1.96 * agg$overall.se)
}

grid <- expand.grid(
  yname = c("patient_contrib", "govt_contrib"),
  ptype = c("concessional", "general"),
  stringsAsFactors = FALSE
)

out <- purrr::pmap_dfr(grid, function(yname, ptype)
  fit_cost(d, yname, ptype, "notyettreated"))

print(out)
write_csv(out, "reports/estimates_cost.csv")
```

Add `library(purrr)` to the suppressPackageStartupMessages block if not already installed:
`R -e 'install.packages("purrr", repos="https://cloud.r-project.org")'`

- [ ] **Step 2: Run it**

```bash
Rscript analysis/04_cost.R
```

- [ ] **Step 3: Commit**

```bash
git add analysis/04_cost.R reports/estimates_cost.csv
git commit -m "feat(analysis): estimate cost per supply-month by patient type"
```

---

## Task 16: Robustness — placebo and multiplier sensitivity

**Why:** Spec 9.4. Fixed in advance so you cannot fish. Placebo is the one that matters: if a fake policy date produces an effect, the real estimate is noise.

**Files:**
- Create: `analysis/05_robustness.R`
- Output: `reports/robustness.csv`

**Interfaces:**
- Consumes: `prep_panel()`
- Produces: `reports/robustness.csv` with columns `check, estimate, se, ci_lo, ci_hi, verdict`

- [ ] **Step 1: Write it**

Create `analysis/05_robustness.R`:

```r
# Robustness, all pre-registered in the design document before results were seen.
#   1. Placebo switch 12 months early, using only pre-policy data. Expect null.
#   2. Supply multiplier 1.8 and 1.9 instead of 2.0.
source("analysis/00_prep.R")
suppressPackageStartupMessages({ library(did); library(readr); library(dplyr) })

d_raw <- prep_panel()
SWITCH_T <- month_to_t(202309)

collapse <- function(data, multiplier) {
  data |>
    group_by(gid, t) |>
    summarise(scripts_30 = sum(scripts_30), scripts_60 = sum(scripts_60),
              g = first(g), .groups = "drop") |>
    mutate(log_supply = log(scripts_30 + multiplier * scripts_60 + 1))
}

fit <- function(data, control_group = "notyettreated") {
  att <- att_gt(yname = "log_supply", tname = "t", idname = "gid", gname = "g",
                data = data, control_group = control_group, clustervars = "gid",
                est_method = "reg", allow_unbalanced_panel = TRUE,
                base_period = "universal")
  aggte(att, type = "simple", na.rm = TRUE)
}

rows <- list()

# Placebo: pretend the switch happened 12 months early, and drop all real
# post-policy data so the true policy cannot leak into the estimate.
placebo <- collapse(d_raw, 2.0) |>
  filter(t < SWITCH_T) |>
  mutate(g = ifelse(g > 0, g - 12L, 0L)) |>
  filter(g == 0 | g < SWITCH_T)
pl <- fit(placebo)
rows[[length(rows) + 1]] <- tibble(
  check = "placebo_switch_202209", estimate = pl$overall.att, se = pl$overall.se,
  ci_lo = pl$overall.att - 1.96 * pl$overall.se,
  ci_hi = pl$overall.att + 1.96 * pl$overall.se,
  verdict = ifelse(pl$overall.att - 1.96 * pl$overall.se <= 0 &
                     pl$overall.att + 1.96 * pl$overall.se >= 0,
                   "PASS - null as expected", "FAIL - effect on a fake date")
)

for (mult in c(1.8, 1.9)) {
  f <- fit(collapse(d_raw, mult))
  rows[[length(rows) + 1]] <- tibble(
    check = sprintf("multiplier_%.1f", mult), estimate = f$overall.att,
    se = f$overall.se, ci_lo = f$overall.att - 1.96 * f$overall.se,
    ci_hi = f$overall.att + 1.96 * f$overall.se, verdict = "sensitivity"
  )
}

out <- bind_rows(rows)
print(out)
write_csv(out, "reports/robustness.csv")
```

- [ ] **Step 2: Run it**

```bash
Rscript analysis/05_robustness.R
```

- [ ] **Step 3: GATE — read the placebo verdict**

`FAIL` means the method finds an effect where none can exist. The headline estimate is then not trustworthy. Stop, investigate, and do not publish a causal claim until the placebo passes.

- [ ] **Step 4: Add the under-co-payment exclusion check**

Spec section 9.4. Under-co-payment scripts have `GOVT_CONTRIB = 0` by construction, so as the patient mix shifts they drag the government-cost average toward zero for reasons unrelated to the policy. Append to `analysis/05_robustness.R`:

```r
# Government cost per supply-month, excluding under-co-payment scripts.
# Those rows carry zero government contribution by construction, so including
# them makes a shift in patient mix look like a cost effect.
cost_check <- function(data, keep_under) {
  sub <- data |>
    filter(keep_under | script_type == "ABOVE CO-PAYMENT") |>
    group_by(gid, t) |>
    summarise(y = sum(govt_contrib) / pmax(sum(supply_months), 1),
              g = first(g), .groups = "drop")
  att <- att_gt(yname = "y", tname = "t", idname = "gid", gname = "g",
                data = sub, control_group = "notyettreated", clustervars = "gid",
                est_method = "reg", allow_unbalanced_panel = TRUE,
                base_period = "universal")
  aggte(att, type = "simple", na.rm = TRUE)
}

for (keep in c(TRUE, FALSE)) {
  f <- cost_check(d_raw, keep)
  rows[[length(rows) + 1]] <- tibble(
    check = ifelse(keep, "govt_cost_all_scripts", "govt_cost_above_copay_only"),
    estimate = f$overall.att, se = f$overall.se,
    ci_lo = f$overall.att - 1.96 * f$overall.se,
    ci_hi = f$overall.att + 1.96 * f$overall.se,
    verdict = "sensitivity"
  )
}

out <- bind_rows(rows)
print(out)
write_csv(out, "reports/robustness.csv")
```

Move the existing `out <- bind_rows(rows)` / `print` / `write_csv` block to the end of the file so it captures these rows too.

- [ ] **Step 5: Run and compare**

```bash
Rscript analysis/05_robustness.R
```

If the two government-cost estimates differ materially, report the above-co-payment-only figure as primary and say why in `findings.md`.

- [ ] **Step 6: Commit**

```bash
git add analysis/05_robustness.R reports/robustness.csv
git commit -m "feat(analysis): add placebo and multiplier sensitivity checks"
```

---

# PHASE 7 — OUTPUTS

## Task 17: Export for Tableau

**Files:**
- Create: `src/export.py`, `tests/test_export.py`

**Interfaces:**
- Consumes: `panel.parquet`, `cohort.parquet`, `reports/event_study.csv`
- Produces: `data/processed/dashboard_trend.csv` (`month, group_set, scripts, supply_months`) and `data/processed/dashboard_event.csv` (copy of event study). `group_set` is one of `Stage 1`, `Stage 2`, `Stage 3`, `Never eligible`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_export.py`:

```python
import pandas as pd

from src.export import build_trend


def test_trend_labels_stages_readably():
    panel = pd.DataFrame(
        [("a", 202309, 10, 5, 20.0), ("b", 202309, 10, 0, 10.0)],
        columns=["group_key", "month", "scripts_30", "scripts_60", "supply_months"],
    )
    panel["scripts_total"] = panel["scripts_30"] + panel["scripts_60"]
    cohort = pd.DataFrame(
        [("a", 1), ("b", 0)], columns=["group_key", "stage"]
    )
    out = build_trend(panel, cohort)
    assert set(out["group_set"]) == {"Stage 1", "Never eligible"}
    assert out[out["group_set"] == "Stage 1"]["supply_months"].iloc[0] == 20.0
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_export.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'src.export'`

- [ ] **Step 3: Write it**

Create `src/export.py`:

```python
"""Flatten the panel into CSVs Tableau Public can connect to directly."""
import pandas as pd

from src.config import PROCESSED, ROOT

STAGE_LABELS = {0: "Never eligible", 1: "Stage 1", 2: "Stage 2", 3: "Stage 3"}


def build_trend(panel, cohort):
    df = panel.merge(cohort[["group_key", "stage"]], on="group_key", how="left")
    df["group_set"] = df["stage"].map(STAGE_LABELS)
    out = df.groupby(["month", "group_set"], as_index=False).agg(
        scripts=("scripts_total", "sum"),
        supply_months=("supply_months", "sum"),
    )
    out["date"] = pd.to_datetime(
        out["month"].astype(str), format="%Y%m"
    ).dt.strftime("%Y-%m-%d")
    return out


def main():
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    cohort = pd.read_parquet(PROCESSED / "cohort.parquet")
    build_trend(panel, cohort).to_csv(PROCESSED / "dashboard_trend.csv", index=False)
    event = pd.read_csv(ROOT / "reports" / "event_study.csv")
    event.to_csv(PROCESSED / "dashboard_event.csv", index=False)
    print(f"wrote {PROCESSED / 'dashboard_trend.csv'}")
    print(f"wrote {PROCESSED / 'dashboard_event.csv'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test and script**

```bash
pytest tests/test_export.py -v
python -m src.export
```

- [ ] **Step 5: Commit**

```bash
git add src/export.py tests/test_export.py data/processed/dashboard_trend.csv data/processed/dashboard_event.csv
git commit -m "feat(export): flatten panel and event study for Tableau"
```

---

## Task 18: Build the Tableau Public dashboard

**Manual task. No code. Follow exactly.**

- [ ] **Step 1: Install and sign up**

Download Tableau Public for Mac from `https://public.tableau.com/app/discover`. Create a free account. Note: everything published to Tableau Public is public. That is fine here — the source data is already public.

- [ ] **Step 2: Connect the data**

Open Tableau Public, connect to Text file, choose `data/processed/dashboard_trend.csv`. Add `dashboard_event.csv` as a second, separate data source (do not join them).

- [ ] **Step 3: Build sheet 1 — the headline**

- Columns: `date` (continuous, month).
- Rows: `scripts` and `supply_months` as a dual axis, synchronised.
- Filter: `group_set` = `Stage 1`.
- Add a reference line at 2023-09-01, dashed.
- Title: `Stage 1 medicines: prescriptions fell 27%, supply did not` — replace 27% with your real figure from `reports/estimates_naive.csv`.

- [ ] **Step 4: Build sheet 2 — the control comparison**

- Same axes, but `group_set` on colour, filtered to `Stage 1` and `Never eligible`.
- Measure: `supply_months` only, indexed to 100 at 2023-08 so the two are comparable in scale.

- [ ] **Step 5: Build sheet 3 — the event study**

- From `dashboard_event.csv`. Columns `event_time`, rows `estimate`.
- Add `ci_lo` and `ci_hi` as a band, or use a Gantt/reference band.
- Reference line at x = -0.5, dashed. Zero line dotted.
- Colour by `control_arm`.

- [ ] **Step 6: Assemble two dashboards**

- Page 1 "The headline": sheet 1 top, sheet 2 below, one text box explaining supply-months in one sentence.
- Page 2 "The detail": sheet 3, plus a text box stating the placebo result and the pre-trend count.

- [ ] **Step 7: Publish and capture**

Publish to Tableau Public. Copy the URL. Screenshot both pages into `images/dashboard-headline.png` and `images/dashboard-detail.png`.

```bash
mkdir -p images
# save screenshots there, then:
git add images/
git commit -m "docs(dashboard): add Tableau Public screenshots"
```

---

## Task 19: findings.md

**Files:**
- Create: `findings.md`

- [ ] **Step 1: Write it**

Four sections, each ending in a recommendation in plain language. Use real numbers from `reports/*.csv`. Structure, following the Olist convention:

```markdown
# Findings & Recommendations

**Scope:** Stage 1 PBS medicines (September 2023), community pharmacy dispensing only,
concessional and general patients. Supply volume is inferred as
`30-day scripts + 2 x 60-day scripts`. The final months of the series are partial and
may revise as late claims process.

## Q1 - Did prescription counts fall?

[Naive number from estimates_naive.csv. State it plainly, then say it is misleading
and why.]

**Recommend:** Do not use prescription counts to monitor this policy. Any dashboard
still counting scripts is reporting a 27% fall in a measure that stopped meaning what
it meant before September 2023.

## Q2 - Did treatment supply hold?

[Primary estimate, both arms, with CIs. State whether the arms agree.]

**Recommend:** [...]

## Q3 - What happened to patient and government cost?

[From estimates_cost.csv.]

**Recommend:** [...]

## Q4 - Did concessional and general patients benefit equally?

[The split. This is the equity question.]

**Recommend:** [...]

## What this analysis cannot tell you

Dispensing is not consumption. No patient-level data, so nothing about individual
adherence or discontinuation. No geographic breakdown in this dataset. No measure of
GP appointment volumes or pharmacy viability. Parallel trends is an assumption; the
event study in `reports/figures/event_study_supply.png` tests it but cannot prove it.
```

- [ ] **Step 2: Commit**

```bash
git add findings.md
git commit -m "docs(findings): add results and recommendations"
```

---

## Task 20: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write it**

Follow the BrisHouse structure — headline first, then setup, then results, then limitations. Include:

- Headline result in the first two sentences, with numbers.
- Dashboard link and screenshot at the top.
- Setup: venv, `pip install -r requirements.txt`, R package install line.
- Run order, explicitly, since filenames no longer carry numbers:

```bash
python -m src.download        # fetch source CSVs into data/raw (cached)
python -m src.build_cohort    # derive 60-day cohort; FAILS LOUDLY on a bad anchor
python -m src.panel           # build data/processed/panel.parquet
python -m src.controls        # match never-eligible controls
python -m src.checks          # print diagnostics for checks_findings.md
python -m src.export          # write Tableau CSVs

Rscript analysis/01_naive.R
Rscript analysis/02_did.R
Rscript analysis/03_event_study.R
Rscript analysis/04_cost.R
Rscript analysis/05_robustness.R
```

- A note that `cohort.parquet`, `panel.parquet` and `matched_controls.parquet` are committed as a snapshot of one pipeline run, so the R analysis works on a fresh clone without a 180 MB download.
- The data trap section, in the spirit of Olist's `customer_unique_id` section: **prescription counts are not treatment volume after September 2023**, and a 60-day item has its own PBS item code.
- Results table: naive estimate, primary estimate both arms, placebo verdict.
- Limitations, copied from the spec section 12.
- Related work: cite the UNSW Centre for Research Excellence in Medicines Intelligence 60-day prescribing program and state that this analysis uses public aggregate data where theirs uses the restricted 10% sample.
- Data source section with the exact PBS URLs and the Latin-1 note.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(readme): add headline results, run order, and limitations"
```

---

# PHASE 8 — SHIP

## Task 21: Fresh-clone reproducibility test

**Why:** Portfolio repo that does not run on a stranger's machine is worse than no repo. A hiring manager who clones it and hits an error has learned something about you.

- [ ] **Step 1: Clone to a temp directory**

```bash
cd /tmp && rm -rf repro-test
git clone /Users/eddie/Documents/DataSci/pbs-60day-dispensing repro-test
cd repro-test
```

- [ ] **Step 2: Set up and run tests only**

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest -v -m "not integration"
```

Expected: all tests pass with no `data/raw` present. The `integration` marker excludes the tests that need downloaded data. If any *unmarked* test needs `data/raw`, it is not a unit test — fix it to use a fixture.

- [ ] **Step 3: Run the R analysis on committed Parquet only**

```bash
Rscript analysis/02_did.R
```

Expected: runs to completion without any Python step, because `panel.parquet` is committed. If it fails, the snapshot is incomplete.

- [ ] **Step 4: Fix anything that broke, then clean up**

```bash
cd /tmp && rm -rf repro-test
```

- [ ] **Step 5: Commit any fixes**

```bash
git add -A
git commit -m "fix: make repository runnable from a fresh clone"
```

---

## Task 22: Publish

- [ ] **Step 1: Create the GitHub repo**

```bash
gh repo create pbs-60day-dispensing --public --source=. --remote=origin \
  --description "Causal evaluation of Australia's 60-day dispensing policy using public PBS data"
git push -u origin main
```

- [ ] **Step 2: Check the rendered README**

Open the repo page. Confirm the dashboard screenshot renders, the link works, and the results table is not mangled.

- [ ] **Step 3: Add repo topics**

```bash
gh repo edit --add-topic data-analysis --add-topic causal-inference \
  --add-topic health-analytics --add-topic australia --add-topic difference-in-differences
```

- [ ] **Step 4: Cross-link**

Add the GitHub repo URL to the Tableau Public dashboard description. Add the Tableau URL to the README if not already there. Each should point at the other.

---

## Task 23: Wrap-up

- [ ] **Step 1: Write the interview answer**

Add `docs/talking-points.md`, not committed to the README. Three paragraphs you can say out loud:

1. What the project found, in two sentences, with the number.
2. The trap — prescription counts stopped meaning treatment volume, and how you caught it.
3. One thing that went wrong and how you handled it. Use whatever actually happened during the anchor gate or the pre-trend test.

- [ ] **Step 2: Update the portfolio pairing**

The two projects now cover both halves: `aus_housing_forecast` predicts, this one measures a cause. Say that explicitly in whichever portfolio page or CV lists them.

- [ ] **Step 3: Final commit and tag**

```bash
git add docs/talking-points.md
git commit -m "docs: add interview talking points"
git tag -a v1.0 -m "Complete analysis: 60-day dispensing evaluation"
git push origin main --tags
```

---

# Appendix — Failure Playbook

| Symptom | Likely cause | Action |
|---|---|---|
| `UnicodeDecodeError` on read | UTF-8 assumed | Pass `encoding="latin-1"`. Global constraint. |
| Anchor count far below 256 | Form/strength text differs between 30- and 60-day listings | Inspect ATC classes with mixed treated/untreated members. Task 7 step 6. |
| Anchor count far above 256 | New brands launched at 202309 | Promote `no_substitution` guard from flag to filter. |
| `supply_months` looks flat everywhere including controls | `switch_month` join broken, all items tagged 30-day | Check `COALESCE(g.switch_month, 999999)` in `src/panel.py`. |
| `att_gt` errors on unbalanced panel | Groups missing months | `allow_unbalanced_panel = TRUE` already set; if it persists, check for duplicate `(gid, t)` rows. |
| Placebo shows an effect | Method picking up noise, or real policy leaking into placebo window | Confirm the placebo filter drops all `t >= SWITCH_T`. If it still fails, the design does not support a causal claim. |
| Pre-trends sloped | Parallel trends fails | Narrow the pre-window to 24 months. If still sloped, reframe as descriptive and say so. |
| Tableau will not connect to Parquet | Tableau Public does not read Parquet | Use the CSVs from `src.export`. That is why they exist. |
