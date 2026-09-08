# Data Checks

## Download provenance

Files retrieved from `https://www.pbs.gov.au/statistics/dos-and-dop/files/`.

| File | Bytes | Retrieved |
|---|---|---|
| `dos-jul-2020-to-jun-2021-phrmcy-type.csv` | 29,359,211 | 2026-09-09 |
| `dos-jul-2021-to-jun-2022-phrmcy-type.csv` | 30,271,123 | 2026-09-09 |
| `dos-jul-2022-to-jun-2023-phrmcy-type.csv` | 31,112,576 | 2026-09-09 |
| `dos-jul-2023-to-jun-2024-phrmcy-type.csv` | 32,713,376 | 2026-09-09 |
| `dos-jul-2024-to-jun-2025-phrmcy-type.csv` | 35,384,567 | 2026-09-09 |
| `dos-jul-2025-to-jun-2026-phrmcy-type.csv` | 36,381,946 | 2026-09-09 |
| `pbs-item-drug-map.csv` | 1,063,694 | 2026-09-09 |
| **Total** | **196,286,493** | |

PBS revises historical files without changing their names. This table records
exactly which bytes the results were built on. To refetch a file, delete it from
`data/raw/` and rerun `python -m src.download`.
