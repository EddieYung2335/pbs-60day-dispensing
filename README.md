# Did 60-Day Dispensing Cut Treatment, or Just Cut Prescriptions?
A causal evaluation of Australia's 60-day dispensing policy using public PBS data.

**Status: in development.** Results not yet available.

## Repository structure

```
.
├── src/                  Python pipeline: raw CSVs -> DuckDB -> panel.parquet
│   ├── config.py         paths, PBS URLs, stage months, supply multiplier, anchor bands
│   ├── download.py       cached fetch of the PBS Date-of-Supply CSVs
│   └── load.py           build data/pbs.duckdb from the CSVs
├── tests/                pytest suite, one module per src module
│   ├── test_config.py
│   ├── test_download.py
│   └── test_load.py
├── data/
│   ├── raw/              source CSVs, ~190 MB, gitignored
│   └── pbs.duckdb        built database, gitignored
├── checks_findings.md    data provenance and diagnostics
├── requirements.txt
└── README.md
```
