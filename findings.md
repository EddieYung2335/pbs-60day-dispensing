# Findings and recommendations

## Summary

From September 2023, many common PBS medicines could be dispensed as a 60-day supply
instead of 30 days. This report asks whether patients ended up with less medicine, or
whether only the number of prescriptions changed.

| Question | Short answer | Recommendation |
|---|---|---|
| Did prescription counts fall? | Yes, but counts stopped measuring treatment once one script could cover two months. | Stop using prescription counts to monitor this policy. Report months of supply instead. |
| Did patients keep getting the same amount of medicine? | Supply did not fall while counts did. Whether the policy caused that cannot be shown with this data. | Retire script counts as a measure, but do not credit the policy with protecting supply. |
| What happened to cost? | Patients paid less for each month of medicine. The government figure is not a budget saving. | Do not quote the government-cost estimate as a saving. |
| Did all patients benefit equally? | In dollars, general patients saved about six times more. As a share of their bills, the savings were close to even. | Report both views, never one average. |

One caveat applies to everything here. Medicines that switched to 60-day supply were
already trending differently from the comparison medicines in the year before the policy.
That means the numbers below describe what happened alongside the policy. They do not prove
the policy caused it. The section "Why this is not proof" under Q2 explains the test.

## How to read this report

- **Supply-month.** One month of medicine. A 30-day script is one supply-month and a 60-day
  script is two: `supply = 30-day scripts + 2 x 60-day scripts`.
- **Comparison group.** Medicines that had not switched at the time, used to show what
  would probably have happened without the policy. Two comparison groups are used and
  reported separately.
- **Confidence interval (CI).** The range the true value plausibly sits in. A range that
  includes zero means the data cannot rule out "no change".
- **Log points.** The unit the models work in. For changes this size, 0.036 log points is
  about +3.7%. Tables give both.

**Scope.** Community pharmacy dispensing only, for concessional and general patients, July
2020 to June 2026. Q1 and the never-eligible comparison cover the 244 Stage 1 medicines
(September 2023). The other estimates pool all three rollout stages (September 2023, March
2024 and September 2024). The final months of the series are partial and may be revised as
late claims are processed.

## Q1. Did prescription counts fall?

Yes, by 3.4%. Stage 1 medicines were dispensed 117,991,684 times in the twelve months
before September 2023 and 113,992,638 times in the twelve months after.

That number should not be used for anything. It has no comparison group, so it cannot
separate the policy from everything else that happened in 2024. It also measures the wrong
thing. A 60-day script covers two months, so one dispensing event after the switch can mean
twice as much medicine as before. Counting events treats the two as equal.

The fall is small because uptake was slow. The share of Stage 1 dispensing that used a
60-day item code was 2.0% in September 2023, 11.1% by March 2024 and 25.0% by June 2026.
Atorvastatin, the obvious medicine to check first, ran slightly ahead of the group and
reached 27.2% by June 2026. Judging the policy from a single well-known medicine would
overstate how quickly it spread. These shares are calculated directly from
`data/processed/panel.parquet` as 60-day scripts over all scripts for Stage 1.

**Recommend:** Do not use prescription counts to monitor this policy. Any dashboard still
counting scripts is reporting a decline in a measure that stopped meaning what it used to
in September 2023. Report supply instead.

## Q2. Did patients keep getting the same amount of medicine?

Prescription counts fell and supply did not follow them down. Every version of the
analysis agrees on that. Whether the policy caused it is a question this design cannot
answer, for the reasons under "Why this is not proof" below.

The estimates compare switched medicines with medicines that had not switched, month by
month, using a difference-in-differences method built for staggered rollouts
(Callaway-Sant'Anna, `did::att_gt`). A simpler two-way fixed effects model would let
medicines that had already switched act as the comparison for later ones, which biases the
result. The model covers 2,392 drug-form groups over 72 months. Figures are in
`reports/estimates_primary.csv`.

| Outcome | Compared with | Change | 95% CI | Log points | Groups |
|---|---|---|---|---|---|
| Supply | Medicines not yet switched | +3.7% | -1.5% to +9.2% | +0.036 | 2,392 |
| Prescriptions | Medicines not yet switched | -9.5% | -13.7% to -5.0% | -0.100 | 2,392 |
| Supply | Matched never-eligible medicines | -16.3% | -31.4% to +2.1% | -0.178 | 443 |
| Prescriptions | Matched never-eligible medicines | -28.3% | -40.7% to -13.4% | -0.333 | 443 |
| Supply (Sun-Abraham check) | Never-switched medicines | +4.2% | +2.3% to +6.0% | +0.041 | 2,392 |

### Why this is not proof

The method assumes that, without the policy, switched and comparison medicines would have
moved in parallel. The event study in `reports/event_study.csv` tests this by estimating a
"policy effect" for each of the twelve months before the switch, when there was no policy
yet. Those estimates should sit flat around zero.

They do not. Month -1 is the reference point and is zero by definition, which leaves
eleven months to test. Four of the eleven are individually significant against the
not-yet-switched comparison and five of eleven against the never-eligible comparison. The
limit set before the test was run was about two.

The pattern matters more than the count. In both comparisons the gap starts negative and
closes as the switch approaches:

| Months before switch | Not yet switched | Never eligible |
|---|---|---|
| -12 | -0.062 | -0.337 |
| -9 | +0.003 | -0.291 |
| -6 | -0.049 | -0.156 |
| -3 | +0.004 | +0.005 |
| -2 | +0.003 | +0.040 |

Switched medicines were running below their comparison group a year out and had closed most
of that gap by the month before the switch. That catch-up was already under way. A design
that compares before with after will count the end of it as a policy effect, which pushes
the supply estimate up. The +3.7% therefore overstates whatever the policy did, by an
amount this design cannot measure.

Starting the series in September 2021, the one remedy specified before the test, changes
nothing. The failing months already sit inside the shorter window. Both versions are in
`reports/event_study.csv`, and the attempt stays in the script.

### What still holds

The gap between prescriptions and supply does not depend on this assumption. It is
arithmetic on the same dispensing events, counted two ways. Supply falls 14 to 16 log
points less than prescriptions do, in both comparisons. That is the measurement problem
this project set out to show, and a pre-existing trend cannot create it.

What does not hold is any claim about the level. "Supply held steady because of the
policy" is not supported. "Supply did not fall while counts did" is.

### The two comparison groups disagree

The first comparison (Arm A) sets each stage against every medicine that had not switched
yet at that point: medicines from later stages and medicines that were never eligible. The
second (Arm B) sets Stage 1 against 199 never-eligible medicines matched on therapeutic
class (ATC) and pre-policy volume.

On supply the two sit 2.05 standard errors apart. The agreement limit set before the models
were run was one standard error. Arm A puts supply slightly up and Arm B puts it down
16.3%. The disagreement is reported rather than resolved, and neither arm is presented as
the answer. Arm B also has the worse pre-policy trend, which fits its much lower estimate.

Both ranges include zero: Arm B runs from -31.4% to +2.1% and Arm A from -1.5% to +9.2%.
Arm B is much less precise, with a standard error of 0.101 against Arm A's 0.026, because
it covers 443 groups rather than 2,392.

### A second method gives the same answer

A different estimator (Sun-Abraham, `fixest::sunab`) returns +0.041 log points on supply,
against +0.036 from Callaway-Sant'Anna. The gap of 0.0046 is well inside the 0.02 limit set
before estimation.

This agreement does not rescue the parallel trends assumption. Both methods rely on it and
both inherit the same bias. The check rules out a coding error, nothing more.

**Recommend:** Judge this policy on supply, not on dispensing events, and read the numbers
above as description. Prescriptions fell about 9.5% while supply did not fall with them.
That is enough to retire script counts as a monitoring measure. It is not enough to credit
the policy with protecting treatment volumes. That claim needs a design that passes the
pre-trend test, and this one does not.

## Q3. What happened to patient and government cost?

Patients paid less for each month of medicine. The government-cost estimate is negative
too, but it cannot be read the same way, for the reasons below. Both come from the same
design as Q2 and inherit the same failed assumption, so they describe what moved alongside
the policy rather than what it caused.

The outcome is dollars per supply-month, so the numbers read directly as dollars. Figures
are in `reports/estimates_cost.csv`, compared with medicines not yet switched.

| Outcome | Patient type | Change per month of medicine | 95% CI |
|---|---|---|---|
| Patient cost | Concessional | -$0.53 | -$0.58 to -$0.47 |
| Patient cost | General | -$3.32 | -$3.50 to -$3.14 |
| Government cost | Concessional | -$160 | -$234 to -$87 |
| Government cost | General | -$150 | -$230 to -$70 |

The patient figures are straightforward. A general patient paid about $3.32 less per month
of medicine and a concessional patient about 53 cents less. Both are small next to the
co-payments themselves, which is what you would expect from a policy that halves the number
of co-payments without changing their size.

The government figures should not be read as a budget number. The model gives every
drug-form group the same weight, however much of it is dispensed, and government cost per
supply-month is extremely uneven across groups. Before their switch, the median switched
group cost the government about $24 per supply-month for concessional patients, the mean
was $110, and the most expensive group-month cost almost $10,000. Weighted by how much is
actually dispensed, which is what a budget line shows, the cost is about $21. These
baselines are in `reports/cost_baseline.csv`, written by `analysis/04_cost.R`.

The estimate is also larger than the thing it is measured against. Averaged the same way as
the estimate, a switched group cost the government $116 per supply-month for concessional
patients before its switch. A $160 fall cannot be the switched medicines getting cheaper,
because they only had $116 to lose. At least part of it has to be the comparison medicines,
which are dominated by high-cost specialty items, becoming more expensive over the same
months. The estimate describes a difference between two sets of expensive medicines, not
the cost of the medicines most people collect.

Leaving out scripts priced below the co-payment does not change this. Those scripts carry
no government contribution by definition, so a shift in patient mix could have created a
false cost effect on its own. The check in `reports/robustness.csv` gives -$177 with all
scripts and -$178 without them, so that concern does not apply here.

**Recommend:** Do not quote the government-cost estimate as a saving to the budget. It
answers a different question from the one a costing needs, and quoting it without the
weighting caveat would overstate the effect on a typical script several times over. A
volume-weighted or logged cost model would answer the budget question, and is not part of
this analysis.

## Q4. Did concessional and general patients benefit equally?

In dollars, no. General patients saved about six times more per month of medicine than
concessional patients: $3.32 against $0.53.

The reason is the co-payment structure, not anything in the policy itself. A general
patient pays the full co-payment on each script until they reach the safety net, so halving
the number of scripts halves a larger amount. A concessional patient pays a much smaller
co-payment, so the same halving saves less in dollars.

Against what each group was paying before, the gap almost disappears. Measured the same way
as the estimates (each medicine's pre-switch average, then averaged across medicines),
concessional patients paid $4.63 per supply-month before the switch and general patients
$26.19 (`reports/cost_baseline.csv`). The savings are about 11% and 13% of those bills. In
proportion to what they paid, the two groups gained almost equally. The sixfold gap is a
dollar gap, and it comes from the size of the co-payment.

**Recommend:** Report the equity result both ways rather than as one average across
patient types. In dollars, a policy presented as cost-of-living relief delivered most of
its per-patient saving to the group with the higher co-payment. As a share of what each
group was paying, the relief was close to even. Both are true. An average hides the first,
and a dollar figure on its own overstates it.

## Checks on the method

Three checks were fixed before any results were seen. Results are in
`reports/robustness.csv`.

**Placebo test: passed.** Pretending the switch happened twelve months early, and using
only data from before the real policy, gives +0.013 log points (95% CI -0.030 to +0.056).
The method finds nothing on a date when nothing happened, which is the correct result. Had
it found an effect, the method would have been fitting noise and none of the numbers above
would be worth reporting.

**Supply multiplier: stable.** Every estimate treats a 60-day script as exactly two months
of medicine. Using 1.8 instead gives a supply estimate of +0.011 log points, and 1.9 gives
+0.024, against +0.036 at 2.0. All three ranges include zero, so the finding that supply
did not fall does not depend on the exact multiplier.

**Scripts below the co-payment: no effect on the result.** Covered under Q3.

Passing the placebo does not fix the parallel trends failure, because the two tests ask
different questions. The placebo asks whether the method invents effects, and it does not.
The event study asks whether switched and comparison medicines were comparable to begin
with, and they were not. The second question decides whether these estimates can be read
as cause and effect, and the answer is still no.

## What this analysis cannot tell you

The parallel trends assumption does not hold, so nothing above establishes cause. That is
the largest limit, and it is set out in Q2 rather than left for a reader to discover.

Dispensing is not consumption. A script collected is not a dose taken.

There is no patient-level data, so nothing can be said about individual adherence or about
patients who stopped treatment. The dataset has no geographic field, so regional
differences are out of reach. Nothing here measures GP appointment volumes or pharmacy
viability, both of which were debated when the policy was announced.

The model covers 2,392 drug-form groups, not the 2,749 in the cohort. The 357 missing
groups are all never-eligible, and they have no rows at all once the community-pharmacy and
patient-category filters are applied. They were never available as comparisons.

Standard errors from `did` come from a bootstrap, so they can move slightly between runs.
The analysis scripts set a seed, and every model estimate above is reproduced exactly by
rerunning `analysis/01_naive.R` to `analysis/05_robustness.R` on the committed data.
