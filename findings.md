# Findings and recommendations

**Status: incomplete.** The supply results below are final. The cost and equity questions
are not yet estimated. The causal reading of Q2 is provisional: it holds only if the
pre-trend test in `analysis/03_event_study.R` and the placebo test in
`analysis/05_robustness.R` pass. If either fails, Q2 will be rewritten as description
rather than cause.

**Scope:** Stage 1 PBS medicines (September 2023), community pharmacy dispensing only,
concessional and general patients. Supply volume is inferred as
`30-day scripts + 2 x 60-day scripts`. The final months of the series are partial and
may revise as late claims process.

## Q1. Did prescription counts fall?

Yes, by 3.4%. Stage 1 medicines were dispensed 117,991,684 times in the twelve months
before September 2023 and 113,992,638 times in the twelve months after.

That number should not be used for anything. It has no control group, so it cannot
separate the policy from everything else that happened in 2024. Worse, it measures the
wrong thing. A 60-day script covers two months, so one dispensing event after the switch
can mean twice the medicine it used to. Counting events treats those as equal.

The 3.4% is smaller than a quick look at a single medicine would suggest, and the reason
matters. Uptake was slow. The share of Stage 1 dispensing that used a 60-day item code
was 2.0% in September 2023, 11.1% by March 2024, and 25.0% by June 2026. Atorvastatin, an
obvious medicine to check first, moved faster than the cohort as a whole. Reading the
policy off one fast-moving drug overstates the effect on everything else.

**Recommend:** Do not use prescription counts to monitor this policy. Any dashboard still
counting scripts is reporting a decline in a measure that stopped meaning what it meant in
September 2023. Report supply volume instead.

## Q2. Did treatment supply hold?

Measured against medicines that had not yet switched, prescription counts fell about 9.5%
and supply did not fall at all. The point estimate for supply is a 3.7% rise, with a
confidence interval running from a 1.5% fall to a 9.2% rise. Because that interval crosses
zero, the defensible claim is that supply did not drop, not that it grew.

Estimates come from `did::att_gt` (Callaway-Sant'Anna) on 2,392 drug-form groups over 72
months, aggregated to a single average treatment effect. Staggered timing across the three
rollout stages is why this estimator is used instead of two-way fixed effects, which would
let already-treated medicines act as controls for later ones. All figures are in log points
in `reports/estimates_primary.csv`; percentages below are exponentiated.

| Outcome | Control arm | Log points | 95% CI | Approx. percent | Groups |
|---|---|---|---|---|---|
| Supply | Not yet treated | +0.036 | -0.015 to 0.088 | +3.7% | 2,392 |
| Prescriptions | Not yet treated | -0.100 | -0.148 to -0.052 | -9.5% | 2,392 |
| Supply | Never eligible | -0.178 | -0.377 to 0.021 | -16.3% | 443 |
| Prescriptions | Never eligible | -0.333 | -0.522 to -0.144 | -28.3% | 443 |
| Supply (Sun-Abraham) | Never treated, implicit | +0.041 | 0.023 to 0.059 | +4.2% | 2,392 |

### The two control arms disagree

Arm A compares Stage 1 medicines with Stage 2 and Stage 3 medicines, which switch later.
Arm B compares them with 199 medicines matched on ATC class and pre-period volume that
never became eligible at all.

On supply the two arms sit 2.05 standard errors apart, well outside the one standard error
fixed as the agreement threshold before the models were run. Arm A says supply rose
slightly. Arm B says it fell 16.3%. This is reported rather than resolved, and neither arm
is presented as the answer.

Two things hold across both arms. Prescription counts fall, and supply falls by 13 to 15
log points less than counts do. That gap is the measurement artefact this project exists to
show, and changing the comparison group does not remove it.

Where the arms overlap is instructive. Arm B's interval runs from -31.4% to +2.1% and Arm
A's from -1.5% to +9.2%, so both are consistent with no change in supply. Arm B is simply
far less certain, with a standard error of 0.101 against Arm A's 0.026, because it uses 443
groups instead of 2,392. The disagreement is in the point estimates, not in what either arm
rules out.

### The second estimator agrees

Sun-Abraham (`fixest::sunab`) returns +0.041 log points on supply against Callaway-
Sant'Anna's +0.036, a gap of 0.0046 against a 0.02 threshold set before estimation. Two
different estimators on the same design give the same answer.

Their standard errors do not match. Sun-Abraham reports 0.009 against 0.026, and its
estimate is significant at p < 0.001 while Callaway-Sant'Anna's is not. Sun-Abraham includes
calendar-month fixed effects, which absorb the January safety-net reset, and `fixest`
computes clustered standard errors analytically where `did` bootstraps them. The
conservative reading is the one reported above: supply did not fall.

**Recommend:** Judge this policy on supply, not on dispensing events. On the evidence so
far, patients kept receiving their medicines through the Stage 1 switch, and the visible
drop in prescription counts was mostly a change in how supply was packaged. Treat this as
provisional until the pre-trend and placebo tests are in.

## Q3. What happened to patient and government cost?

Not yet estimated. Output will land in `reports/estimates_cost.csv`.

## Q4. Did concessional and general patients benefit equally?

Not yet estimated. Same model as Q3, split by patient category.

## What this analysis cannot tell you

Dispensing is not consumption. A script collected is not a dose taken.

There is no patient-level data here, so nothing can be said about individual adherence or
about patients who stopped treatment. The dataset has no geographic field, so regional
differences are out of reach. Nothing here measures GP appointment volumes or pharmacy
viability, both of which were argued about when the policy was announced.

Parallel trends is an assumption, not a finding. The event study tests it and can fail it,
but cannot prove it.

The model covers 2,392 drug-form groups, not the 2,749 in the cohort. The 357 missing
groups are all never-eligible, and they have no rows in the panel at all once the
community-pharmacy and patient-category filters are applied. They were never available as
controls.

Standard errors from `did` come from a bootstrap, so they move between runs.
`analysis/02_did.R` sets a seed, and every number above is reproducible from a fresh clone.
