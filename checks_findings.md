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


## Derivation anchor

The government published Stage 1 as 92 medicines and 256 PBS items. The derivation rule never uses either number, so landing close to them is an independent check. The bands in `src/config` were set before any output was seen and have not been changed. 

Run: `python -m src.anchor`

| Measure | Derived | Band | Published |
|---|---|---|---|
| New 60-day item codes, Stage 1 | 249 | 230-280 | 256 |
| Distinct drug names, Stage 1 | 91 | 85-100 | 92 |
| All item codes in Stage 1 groups | 586 | not tested | - |

**Result: pass** No rule changes were made. 

### "256" PBS Items
"256 items" could mean the new 60-day codes or every code in an eligible group. 

The two derived counts are 249 and 586. Only the first is close, so the band is applied to new codes. 

### The signal is distinct from background listings

New item codes appearing in groups that already exists (per month):

| Month | Codes |
|---|---|
| 202307 | 5 |
| 202308 | 8 |
| **202309** | **249** |
| 202310 | 3 |
| 202311 | 27 |
| **202403** | **233** |
| **202409** | **263** |

Outside the three stage months, existing groups gain 1-31 new codes a month. Stage 2 and 3 have no published anchor, but they show the same step as Stage 1. The **202311** rise is almost entirely biologics (adalimumab, etanercept, tocilizumab, golimumab, abatacept, baricitinib,
tofacitinib). These are not stage months and those groups stay untreated. 

### Where the 7-item (249 vs 256 ) gap could come from

The count has small errors in both directions, and they partly cancel. 

- **Possible over-count**. At the background rate, a few of the 249 codes may be ordinary new listings that happens to land in September 2023. Candidates to check in the guard review zanubrutinib 80 mg (two new codes in one group) and infliximab (a biologic with under 1,000 lifetime scripts). 

- **Possible under-count**. `MESALAZINE | SACHET CONTAINING GRANULES, 500 MG PER SACHET` gained a new code (13361F) in 202310, not 202309, so it is classed as never eligible. Mesalazine is the largest Stage 1 drug (14 groups), which suggests a Stage 1 item with no dispensing in its first month. Only 2 codes in the whole dataset first appear in 202310, so at most 1-2 items are missed this way. That is too few to justify widening the stage window.


### The new-product filter works

Nine codes first dispensed in 202309 belong to groups that did not exist before that month: patiromer, glucagon, Alfamino and azacitidine 300 mg. The rule correctly leaves them out of stage 1. 

### Drug-count caveat

`drug_name` counts combination products (for example `AMLODIPINE + ATORVASTATIN`) as separate medicines. The government's counting convention is not published, so 91 vs 92 is treated as agreement, not an exact match. The 249 new codes fall into 246 groups because three groups gained two codes each:
furosemide 20 mg, mesalazine 1.2 g prolonged release, and zanubrutinib 80 mg.

## Guard flag review

456 flags on 386 of 689 treated groups. Reviewed on 2026-09-15.

- low_uptake (347): kept. 60-day switching was slow for all medicines
  (median 7% in first 6 months even for unflagged groups), so a 5% threshold
  catches real listings. Most flagged groups keep growing after a year.
- no_substitution (109): kept. With a small 60-day share, the fall in 30-day
  scripts is too small to see against normal growth.
- Dropped 5 groups where the new code is not a 60-day pack:
  - MORPHINE oral solution 100 mL and 500 mL (S19A): shortage import that
    replaced the old pack.
  - INFLIXIMAB 120 mg syringe: same price as old code, uptake 0.4%.
  - ADALIMUMAB 40 mg 0.8 mL syringe: same price as old code, uptake under 3%.
  - ZANUBRUTINIB 80 mg: two new codes at the same price as the old code.
- Anchor after drops: about 246 items, 89 drugs. Still inside both bands.

## Never-eligible controls (Arm B)

Run: `python -m src.controls`

Each Stage 1 group is matched to never-eligible (stage 0) groups on two things: ATC level-1 class and pre-period volume decile. Volume is the mean monthly `supply_months` up to 202308, so the policy itself cannot move a group into a different stratum. A stratum is kept only if it holds at least one group from each side. Stage 2 and 3 groups are not used here; they are the Arm A controls.

| Measure | Count |
|---|---|
| Stage 1 groups | 244 |
| Stage 1 groups matched | 244 |
| Stage 1 groups with no available control | 0 |
| Stage 0 groups available | 2,065 |
| Stage 0 groups kept as controls | 199 |
| Strata used | 21 |

**Result: pass.** The plan treats Arm B as weak if more than 30% of Stage 1 groups go unmatched. None did, so the Arm B estimate covers all of Stage 1.

The other 1,866 stage 0 groups sit in strata with no Stage 1 group, such as anti-infectives (J), and are left out.

### Overlap is thin where Stage 1 is concentrated

Stage 1 leans towards high-volume cardiovascular medicines: 168 of the 244 groups are in C-8, C-9 or C-10. Controls are scarce in that same corner.

| Stratum | Treated | Controls |
|---|---|---|
| C-10 | 81 | 2 |
| B-10 | 9 | 4 |
| M-5 | 1 | 4 |

91 treated groups (37%) are in strata with fewer than five controls. The C-10 comparison rests on two medicines, amiodarone 200 mg and sotalol 80 mg, both anti-arrhythmics. If either follows its own trend over 2023 to 2026, the Arm B estimate for a third of Stage 1 moves with it.

This goes in the limitations section. It is not a reason to change the match: redrawing the strata after seeing these counts would undermine the check in the same way widening the anchor band would. Arm A gives an independent comparison for these groups up to March 2024.

### Test data fix

`test_stratum_combines_atc1_and_volume_decile` failed as written in the plan. With three groups, percentile ranks are 0.33 apart, so volumes of 1,000 and 900 land in deciles 10 and 7 and can never share a stratum. The test now uses 20 groups, which puts neighbouring ranks 0.05 apart, and also checks that a very different volume lands in a different decile. `assign_strata` was not changed.
