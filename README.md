# Did 60-day dispensing cut treatment, or just cut prescriptions?

A causal evaluation of Australia's 60-day dispensing policy using public PBS data.

**Status: in development.** The Python pipeline is built and produces the analysis panel. The R estimation is in progress, so there are no results yet.

## The question

From September 2023, eligible PBS medicines could be dispensed as a 60-day supply on one script. A 60-day script covers two months, so prescription counts fall even when patients get exactly the same amount of medicine. This project measures supply (`scripts_30 + 2 × scripts_60`) instead of counts, and asks whether treatment actually changed.

The rollout came in three stages (September 2023, March 2024, September 2024). That staggered timing is why the estimation uses Callaway-Sant'Anna and Sun-Abraham difference-in-differences instead of plain two-way fixed effects.

## Repository structure

```
.
├── src/                        Python pipeline: raw CSVs -> DuckDB -> parquet
│   ├── config.py               paths, PBS URLs, stage months, supply multiplier, anchor bands
│   ├── download.py             cached fetch of the PBS Date-of-Supply CSVs
│   ├── load.py                 build data/pbs.duckdb from the CSVs
│   ├── derive.py               derive each drug-form group's stage from new item codes
│   ├── guards.py               flag groups the stage rule may misclassify
│   ├── anchor.py               compare derived Stage 1 counts with the published 92 / 256
│   ├── build_cohort.py         run derivation, guards and anchor; write cohort.parquet
│   ├── panel.py                monthly panel by group, patient type and script type
│   ├── controls.py             match never-eligible controls to Stage 1 groups
│   └── checks.py               diagnostics reported in checks_findings.md
├── analysis/                   R estimation
│   └── 00_prep.R               load the panel, add month index and treatment timing
├── tests/                      pytest suite, one module per src module
├── data/
│   ├── raw/                    source CSVs, ~190 MB, gitignored
│   ├── pbs.duckdb              built database, gitignored
│   └── processed/              committed snapshot of one pipeline run
│       ├── cohort.parquet      one row per group with its stage and switch month
│       ├── panel.parquet       group x month x patient type x script type
│       ├── matched_controls.parquet
│       └── guard_flags.csv
├── checks_findings.md          data provenance, derivation checks, known data limits
├── requirements.txt
└── README.md
```

## Running it

The processed parquet files are committed, so the R analysis runs on a fresh clone without downloading anything. To rebuild them from source:

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python -m src.download        # fetch PBS CSVs into data/raw (cached)
python -m src.load            # load into DuckDB
python -m src.build_cohort    # derive the cohort; exits 1 if the anchor check fails
python -m src.panel           # write data/processed/panel.parquet
python -m src.controls        # match never-eligible controls
python -m src.checks          # print diagnostics
```

Tests:

```bash
pytest -v -m "not integration"   # unit tests, no data needed
pytest -m integration -v         # needs data/raw and the built parquet
```

The R side needs `arrow`, `dplyr`, `did` and `fixest`.

## Data

PBS Date-of-Supply statistics, community pharmacy only (`PHRMCY_TYPE = 'S90'`), concessional and general patients, July 2020 to June 2026. The source CSVs are Latin-1 encoded. `checks_findings.md` has the download record and the limits of the data: no geography, no quantity field and no patient-level records.
