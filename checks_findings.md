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

## Panel summary

Run: `python -m src.checks`

| Measure | Value |
|---|---|
| Panel rows | 354,290 |
| Months | 202007 to 202606 |
| Never-eligible groups | 2,065 |
| Stage 1 groups | 244 |
| Stage 2 groups | 213 |
| Stage 3 groups | 227 |

One row is a drug-form group, month, patient type and script type. The full list of guard flags is in `data/processed/guard_flags.csv`.

## The January confounder

The PBS safety net resets every January. Patients who reached the threshold the year before go back to paying full co-payments, so the split of cost between patient and government shifts at the start of every year, for treated and untreated medicines alike.

Calendar-month profile, all groups and all years pooled:

| Month | Govt cost per script ($) | Mean scripts per month (m) |
|---|---|---|
| Jan | 34.24 | 23.6 |
| Feb | 33.82 | 23.7 |
| Mar | 34.28 | 26.5 |
| Apr | 33.73 | 25.3 |
| May | 34.92 | 27.2 |
| Jun | 35.26 | 26.4 |
| Jul | 34.28 | 27.1 |
| Aug | 34.07 | 27.2 |
| Sep | 34.60 | 26.4 |
| Oct | 34.98 | 27.1 |
| Nov | 36.53 | 26.8 |
| Dec | 37.22 | 29.4 |

December to January, year by year:

| January of | Govt cost total | Govt cost per script | Patient cost per script | Scripts |
|---|---|---|---|---|
| 2021 | -30.3% | -10.0% | +47.6% | -22.5% |
| 2022 | -28.1% | -9.6% | +45.3% | -20.4% |
| 2023 | -32.9% | -14.8% | +45.2% | -21.2% |
| 2024 | -21.3% | -6.1% | +54.4% | -16.2% |
| 2025 | -22.9% | -6.7% | +49.8% | -17.4% |
| 2026 | -22.7% | -3.1% | +40.7% | -20.3% |

The design notes expected government cost to fall about 45% each January. The data does not support that figure. Total government cost falls 21 to 33%, and most of that fall is volume: December is the busiest month of the year and January the quietest, which fits patients filling scripts before the reset. Per script, government cost falls only 3 to 15%. The figure close to 45% is the rise in patient cost per script, which is the other side of the same reset. The per-script fall is larger for concessional patients ($41.37 to $38.05) than for general patients ($29.76 to $28.81).

The January swing is smaller from 2024 onward. The cause is not tested here, and because it starts after Stage 1 it is not read as evidence about the policy.

How the estimation handles it:

- The Sun-Abraham model carries calendar-month fixed effects explicitly (`| gid + month_of_year`).
- Callaway-Sant'Anna has no month term. It compares treated and control groups in the same calendar month, so a January shift common to both cancels out. This relies on the reset moving treated and control medicines by the same proportion.

The December peak matters for supply outcomes as well as cost, so no model is run on raw month-to-month changes without one of these two protections.

## Known limitations of the data

- No geography. The Date of Supply files have no state or region field, so regional differences in uptake cannot be studied. The concessional and general split is the only equity dimension available.
- No quantity field. The files count prescriptions, not tablets or days. `supply_months` assumes a 60-day script supplies exactly twice a 30-day script (`SUPPLY_MULTIPLIER = 2.0`).
- No patients. Every row is a monthly total. Nothing can be said about individual adherence, switching or stopping treatment, and a dispensed medicine is not necessarily a medicine taken.
- Under-co-payment scripts carry no government cost. They are 31% of scripts in the panel and have `govt_contrib = 0` by construction, so cost results are reported with and without them.
- Revisions. PBS revises historical files under the same file names, and the most recent months can still change as late claims are processed. The provenance table records which files these results were built on.
