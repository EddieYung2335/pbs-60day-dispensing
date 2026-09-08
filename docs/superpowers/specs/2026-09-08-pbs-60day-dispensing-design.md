# Evaluating Australia's 60-Day Dispensing Policy

**Date:** 2026-09-08
**Status:** Approved design, not yet implemented

## 1. The question

From 1 September 2023 the Australian Government allowed certain PBS medicines to be
dispensed as a 60-day supply instead of 30 days, for one co-payment. The change was
rolled out in three stages (September 2023, March 2024, September 2024) and now covers
close to 300 medicines.

This project answers two questions with public data:

1. **Primary — did treatment continuity hold?** Prescription counts necessarily fall
   when one script covers two months. Did the volume of medicine actually supplied fall
   with them?
2. **Secondary — who captured the saving?** What happened to patient co-payments and to
   government cost per month of therapy, and did concessional and general patients
   benefit equally?

The headline deliverable is a causal estimate with its uncertainty, not a description of
uptake.

## 2. Why this is a credible design

The policy did not apply to every medicine, and eligible medicines were phased in on
known dates. That yields two independent control groups: medicines eligible at a later
stage (not yet treated), and medicines never made eligible. Treatment status is
observable in the data itself, because every eligible medicine received a **new PBS item
code** for the 60-day quantity.

Verified directly from the source files on 2026-09-08 — atorvastatin, a Stage 1 medicine:

```
                      Jul  Aug  Sep  Oct  Nov  Dec  Jan  Feb  Mar  Apr  May  Jun   (2023-24, thousands)
  30-day scripts     1042 1078 1003 1006  974 1000  827  818  826  825  844  757
  60-day scripts        0    0   19   42   62   73   80   93  109  124  139  135
  supply-months      1042 1078 1042 1090 1097 1147  987 1004 1043 1073 1121 1027
```

Metformin (Stage 2) shows the same pattern with new codes first appearing in 202403.
Amoxycillin (never eligible) shows no new codes and pronounced winter seasonality
(825 → 619 → 841), confirming that a naive "all other medicines" control would be
invalid.

## 3. Data sources

All sources are public, free, and require no login or application.

### 3.1 PBS Date of Supply data (primary)

Six financial-year CSV files from
`https://www.pbs.gov.au/statistics/dos-and-dop/files/`:

| File | Size |
|---|---|
| `dos-jul-2020-to-jun-2021-phrmcy-type.csv` | 29 MB |
| `dos-jul-2021-to-jun-2022-phrmcy-type.csv` | 30 MB |
| `dos-jul-2022-to-jun-2023-phrmcy-type.csv` | 30 MB |
| `dos-jul-2023-to-jun-2024-phrmcy-type.csv` | 32 MB |
| `dos-jul-2024-to-jun-2025-phrmcy-type.csv` | 17.5 MB |
| `dos-jul-2025-to-jun-2026-phrmcy-type.csv` | 16.5 MB |

Schema (verified):

```
MONTH_OF_SUPPLY, ITEM_CODE, DRUG_TYPE, PATIENT_CAT, PHRMCY_TYPE, SCRIPT_TYPE,
PRESCRIPTIONS, PATIENT_CONTRIB, GOVT_CONTRIB, TOTAL_COST, RETAIL_MARKUP,
PATIENT_NET_CONTRIB
```

Coverage: July 2020 to June 2026. That is 38 months before the Stage 1 switch and 34
months after. Month is date of supply, not date of claim processing.

Observed field values (FY2023-24, prescriptions):

- `PATIENT_CAT`: `G2` 128.5M, `C1` 124.7M, `C0` 72.5M, `R1` 4.0M, `R0` 3.0M, `G1` 2.1M,
  `DB` 0.4M. Concessional is `C*`, general is `G*`, repatriation is `R*`.
- `SCRIPT_TYPE`: above co-payment 229.2M, under co-payment 105.9M. Under-co-payment
  scripts have `GOVT_CONTRIB` of zero by construction.
- `PHRMCY_TYPE`: `S90` (community pharmacy) 331.8M, `S94 PUB` 1.8M, `S94 PRI` 1.5M,
  `S92` negligible.

### 3.2 PBS item-to-drug mapping

`https://www.pbs.gov.au/statistics/dos-and-dop/files/pbs-item-drug-map.csv`, 1.1 MB,
12,162 rows, item codes `00000A` to `15502X`.

Schema: `ITEM_CODE, DRUG_NAME, FORM/STRENGTH, ATC5_Code`.

### 3.3 Encoding

Both files are **Latin-1, not UTF-8**. Reading them as UTF-8 fails on drug names
containing accented characters. Every reader must specify the encoding explicitly.

### 3.4 What is deliberately not used

The Department of Health page listing official 60-day item codes
(`health.gov.au/our-work/60-day-dispensing/pbs-medicines-current-item-codes`) now
redirects to a 404 and is treated as unavailable. Treatment status is derived from the
dispensing data instead, which removes the dependency on a page that has already proven
unstable.

The Date of Supply data contains **no state or geographic field**. Geographic analysis is
out of scope; the concessional/general split serves the equity question instead.

The data contains **no quantity or units field**. Supply volume is inferred (section 6).

## 4. Scope

**In scope:** Stage 1 medicines only — 92 medicines across 256 PBS items per the
government's own published figures. Stage 1 is a boundary drawn by the policy rather than
by the analyst, and covers the longest post-period.

**Out of scope:** Stage 2 and Stage 3 medicines as treated units. They appear only as
not-yet-treated controls, and as a validation check that the derivation rule fires on the
correct dates.

**Out of scope entirely:** health outcomes, individual patient adherence, GP appointment
volumes, pharmacy revenue or viability, geographic variation. The data contains
transactions, not patients.

## 5. Architecture

Six sequential scripts, each writing a file the next reads.

```
01_download.py       → data/raw/*.csv                   cached; delete a file to refetch
02_load_duckdb.py    → data/pbs.duckdb                  typed tables, latin-1 decoded
03_derive_cohort.py  → data/processed/cohort.parquet    treatment status per drug group
04_build_panel.py    → data/processed/panel.parquet     monthly analysis panel
05_checks.py         → checks_findings.md               validation; run before trusting output
06_export_tableau.py → data/processed/dashboard.csv     flattened for Tableau

analysis/01_event_study.R  → reports/figures/, reports/estimates.csv
analysis/02_did.R
analysis/03_robustness.R
```

`data/raw/` and `data/pbs.duckdb` are gitignored. `cohort.parquet` and `panel.parquet`
are committed as a snapshot of one pipeline run, so the R analysis and the dashboard work
on a fresh clone without a 180 MB download. This follows the same convention as the
`aus_housing_forecast` repo.

**Storage:** DuckDB, reading the CSVs directly. The dataset is too large to be pleasant in
pandas and far too small to justify a database server. Postgres is deliberately avoided;
the `olist-ecommerce-analytics` repo already demonstrates it.

**Languages:** Python for ingestion, derivation, validation and export. R (`did`,
`fixest`) for estimation, where the staggered difference-in-differences ecosystem is
strongest. The seam between them is a single Parquet file.

## 6. The unit of analysis

**The drug-form group, keyed on `(DRUG_NAME, FORM/STRENGTH)`.**

A 60-day listing shares its drug name and form/strength string exactly with its 30-day
sibling. Verified:

```
08215J  ATORVASTATIN  Tablet 40 mg (as calcium)   30-day, pre-existing
13468W  ATORVASTATIN  Tablet 40 mg (as calcium)   60-day, first appears 202309
09232X  ATORVASTATIN  Tablet 40 mg (as calcium)   30-day, separate listing
```

This gives an exact join key. No fuzzy matching, no manual mapping, no external list.

**Supply volume** is inferred as:

```
supply_months = scripts_30 + 2 * scripts_60
```

The 2x multiplier holds for both 30→60 day and 28→56 day items, since both double. This
is an assumption, is stated as one in every output, and is tested for sensitivity in
section 9.

**Panel grain:** group x month x patient_type, where patient_type is concessional (`C0`,
`C1`) or general (`G1`, `G2`). Repatriation categories (`R0`, `R1`, `DB`) are excluded as
a distinct scheme with different co-payment rules. Restricted to `PHRMCY_TYPE = S90`.

Measures per cell: `scripts_30`, `scripts_60`, `supply_months`, `patient_contrib`,
`govt_contrib`, `total_cost`.

Approximate size: 250 Stage 1 groups plus controls, x 72 months, x 2 patient types.

## 7. Deriving treatment status

### 7.1 The rule

A drug-form group is **Stage 1 treated** if it contains an item code whose first non-zero
dispensing month is 2023-09, **and** the group had at least one item code dispensing
before 2023-09.

Stage 2 applies the same test at 2024-03, Stage 3 at 2024-09. A group failing all three
tests is never-eligible.

### 7.2 Guards against misclassification

Each guard addresses a specific failure mode.

1. **A new brand launching coincidentally in September 2023.** Require substitution: the
   group's 30-day scripts must fall as the new code rises, and supply-months must remain
   continuous within tolerance across the switch. A new brand adds volume rather than
   shifting it. This is a numeric test, not a judgement call.
2. **A new strength appearing.** Handled by the sibling requirement — a new strength has
   no pre-existing code with identical form/strength text.
3. **A delisted product relisted under a new code.** Flag any group where a pre-existing
   code's volume drops to zero rather than falling partially. Genuine substitution leaves
   the 30-day code alive.
4. **Cosmetic differences in form/strength text between the 30- and 60-day listings.**
   This is the highest-risk failure because it causes false *negatives*, silently moving a
   treated group into the control pool. Mitigation: after derivation, manually review
   every Stage 1 group whose 60-day code never exceeds 5% of group volume, and every
   never-eligible group whose ATC-5 class contains a treated group.

Every group touched by a guard is listed in `checks_findings.md` with the reason.

### 7.3 External validation anchor

The government published that Stage 1 covered **92 medicines and 256 PBS items**. The
derivation must be compared against those figures.

Decision rule, fixed in advance: if the derived item count falls within 230-280 and the
distinct drug-name count within 85-100, the derivation is accepted and the exact numbers
are reported alongside the official ones. Outside those bands, the derivation is treated
as failed, the discrepancy is investigated, and the rule is revised before any estimation
is run.

This is a falsifiable prediction about the pipeline, made against a source not used in
building it.

## 8. Control groups

Both arms are constructed; both are reported.

**Arm A — not yet treated.** Stage 2 and Stage 3 groups, valid as controls until their own
switch month. Clean window for Stage 1 is September 2023 to February 2024. These are
chronic medicines the government itself judged similar enough to make eligible, which is
the strongest available comparability argument.

**Arm B — matched never-eligible.** Never-eligible groups matched to Stage 1 groups by
coarsened exact matching on ATC level-1 class and pre-period volume decile, then filtered
on pre-period trend similarity. No propensity model: with roughly 250 groups a stratified
match is more defensible and far easier to explain. Arm B extends the horizon past
February 2024 at the cost of weaker comparability.

If the two arms agree, the result is reported as robust. If they diverge, the divergence
is reported as a finding in its own right rather than resolved by choosing the more
convenient number.

## 9. Estimation

### 9.1 Outcomes, in reporting order

1. `log(scripts)` — the naive outcome. Estimated and reported **first**, to establish the
   misleading headline figure that motivates the rest of the analysis.
2. `log(supply_months)` — the primary outcome. Treatment continuity.
3. `patient_contrib / supply_month` and `govt_contrib / supply_month` — secondary cost
   outcomes, estimated separately for concessional and general patients.

### 9.2 Estimator

Treatment timing is staggered and effects plausibly differ by stage, so plain two-way
fixed effects is inappropriate — later-treated units enter as controls for earlier-treated
ones with negative weights.

- **Primary: Callaway–Sant'Anna**, R `did` package. The control arm is selected by
  argument: `control_group = "notyettreated"` for Arm A, `control_group = "nevertreated"`
  restricted to the matched set for Arm B. One estimator, one flag, genuinely comparable
  results.
- **Cross-check: Sun–Abraham**, `fixest::sunab()`. Different estimator, same design.
  Material disagreement between them is reported.

Group fixed effects, calendar-month fixed effects, standard errors clustered at the
drug-group level (~250 clusters).

### 9.3 Event study

Coefficients from -12 to +12 months around each group's own switch month. Pre-period
coefficients are load-bearing: if the leads are not flat, parallel trends is not
supported, and that is reported rather than omitted.

### 9.4 Robustness, fixed in advance

- **Placebo switch date at September 2022.** Expected null. A non-null placebo invalidates
  the headline estimate.
- **Both control arms**, reported side by side in every results table.
- **Cost models with and without under-co-payment scripts**, since those carry
  `GOVT_CONTRIB = 0` by construction and would otherwise bias government cost downward as
  the patient mix shifts.
- **Supply-month multiplier sensitivity.** The primary specification uses 2.0.
  Re-estimate with 1.8 and 1.9 to show the result does not depend on the exact value.
  Only values below 2.0 are tested: a 60-day script cannot deliver more than double a
  30-day script, but it can deliver less in effect if some patients would not have
  refilled the second month.

### 9.5 Known confounder

Government cost falls roughly 45% every January across all medicines, including controls,
from the calendar-year safety net reset. Script volumes show a January dip in treated and
control groups alike. Calendar-month fixed effects are mandatory in every specification.
The confounder, and the chart demonstrating it, are documented in `checks_findings.md`.

## 10. Deliverables

**`README.md`** — headline result in the first two sentences, then setup, results table,
and limitations. Follows the structure of the `aus_housing_forecast` README.

**`findings.md`** — one section per question with a plain-language recommendation:
continuity, patient cost, government cost, distribution of benefit. Follows the
`olist-ecommerce-analytics` convention.

**`checks_findings.md`** — derivation validation against the 256-item anchor, every
guard-flagged group with its reason, the January confounder with its chart, and the
pre-trend test results.

**Tableau Public, two pages:**

- *Page 1 — the headline.* Scripts and supply-months for Stage 1 medicines on one axis,
  vertical rule at September 2023, control group alongside. One line falls, the other does
  not; the argument is visible without reading anything.
- *Page 2 — the detail.* Event-study coefficients with confidence bands, and cost per
  supply-month split concessional versus general.

**`reports/figures/`** — R-generated event study and pre-trend plots, referenced from
`findings.md`.

## 11. Testing

`tests/test_derive.py`, asserting on the hand-verified atorvastatin case:

- Group `ATORVASTATIN / Tablet 40 mg (as calcium)` classifies as Stage 1 treated.
- Its 60-day item code's first non-zero month is `202309`.
- Supply-months across the switch stay within 10% of the pre-switch mean.
- A known never-eligible group (amoxycillin) classifies as never-eligible.

Small, real, and it fails loudly if the derivation logic drifts. Mirrors
`tests/test_predict.py` in the housing repo.

## 12. Stated limitations

These appear in the README, not only here.

- Dispensing volume is a proxy for treatment received. A dispensed medicine is not
  necessarily a taken medicine.
- `supply_months` rests on the 2x multiplier assumption.
- No patient-level data, so nothing can be said about individual adherence, switching, or
  discontinuation.
- No geographic breakdown available in this dataset.
- Parallel trends is an assumption, tested but not proven.
- The 2026 financial year is partial and trailing months may revise as late claims
  process.

## 13. Related work

UNSW's Centre for Research Excellence in Medicines Intelligence runs a 60-day prescribing
research program using the restricted PBS 10% sample and PLIDA. Their published output is
descriptive uptake analysis. This project is causal, uses only public aggregate data, and
is positioned as complementary. Their work is cited in the README.

## 14. Risks

| Risk | Mitigation |
|---|---|
| Derivation misses treated groups via cosmetic string differences, contaminating controls | Section 7.2 guard 4; validation anchor in 7.3 catches large misses |
| Not-yet-treated window (6 months) too short for a stable estimate | Arm B extends the horizon; report both |
| PBS revises historical files between download and analysis | Record download date and file sizes in `checks_findings.md` |
| Parallel trends fails visibly in the event study | Report it; the project still stands as an honest negative methodological result |
