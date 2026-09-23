# Findings and recommendations

**Status: incomplete, and the headline is descriptive rather than causal.** The parallel
trends test in `analysis/03_event_study.R` fails. Stage 1 medicines were already moving
relative to their controls before September 2023, so the difference-in-differences
estimates below describe what happened alongside the policy and should not be read as
what the policy caused. The detail is in Q2. Cost and equity are not yet estimated.

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

Prescription counts fell and supply did not follow them down. That much is in the data
across every specification tried. Whether the policy caused it is a question this design
cannot answer, for reasons set out under "The pre-trend test fails" below.

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

### The pre-trend test fails

Difference-in-differences assumes that treated and control medicines would have moved in
parallel without the policy. The event study in `reports/event_study.csv` tests that by
estimating an effect for each of the twelve months before the switch, when by definition
there is no effect to find. Those coefficients should be flat and centred on zero.

They are not. Counting the reference month at -1, which is zero by construction and
excluded, four of eleven leads are individually significant against the not-yet-treated
arm and five of eleven against the never-eligible arm. The threshold set in advance was
about two.

The shape is worse than the count. Both arms drift in the same direction:

| Months before switch | Not yet treated | Never eligible |
|---|---|---|
| -12 | -0.062 | -0.337 |
| -9 | +0.003 | -0.291 |
| -6 | -0.049 | -0.156 |
| -3 | +0.004 | +0.005 |
| -2 | +0.003 | +0.040 |

Stage 1 medicines were running below their controls a year out and had closed most of that
gap by the month before the switch. This is convergence that was already underway, not
noise scattered around zero. A design that compares before with after will read the tail of
that convergence as policy effect, which biases the supply estimate upward. The +3.7% is
therefore an overstatement of whatever the policy did, by an amount this design cannot
measure.

Trimming the series to start in September 2021, the one remedy specified before the test
was run, changes nothing. The failing leads sit inside the trimmed window already, so the
trim cannot reach them. Both specifications are in `reports/event_study.csv` and the
attempt is left in the script rather than described after the fact.

### What survives the failure

The gap between prescriptions and supply does not depend on parallel trends. It is
arithmetic on the treated series: the same dispensing events, counted two ways. Supply
falls 13 to 15 log points less than counts do, in both control arms. That is the
measurement artefact this project was built to show, and a pre-trend cannot manufacture it.

What does not survive is any claim about the level. "Supply held steady because of the
policy" is not supported. "Supply did not fall while counts did" is.

### The two control arms disagree

Arm A compares Stage 1 medicines with Stage 2 and Stage 3 medicines, which switch later.
Arm B compares them with 199 medicines matched on ATC class and pre-period volume that
never became eligible at all.

On supply the two arms sit 2.05 standard errors apart, well outside the one standard error
fixed as the agreement threshold before the models were run. Arm A puts supply slightly up,
Arm B puts it down 16.3%. This is reported rather than resolved, and neither arm is
presented as the answer. Arm B also carries the worse pre-trend, which is consistent with
its much larger negative point estimate.

Both intervals do include zero. Arm B's runs from -31.4% to +2.1% and Arm A's from -1.5% to
+9.2%. Arm B is far less certain, with a standard error of 0.101 against Arm A's 0.026,
because it uses 443 groups rather than 2,392.

### The second estimator agrees

Sun-Abraham (`fixest::sunab`) returns +0.041 log points on supply against Callaway-
Sant'Anna's +0.036, a gap of 0.0046 against a 0.02 threshold set before estimation. Two
different estimators on the same design give the same answer.

Agreement between estimators is not evidence for the identifying assumption. Both rest on
the same parallel trends assumption and both inherit the same pre-trend bias. The
cross-check rules out an implementation error, nothing more.

**Recommend:** Judge this policy on supply, not on dispensing events, and read the numbers
above as description. Prescription counts fell about 9.5% while supply did not fall with
them, which is enough to retire script counts as a monitoring measure. It is not enough to
credit the policy with protecting treatment volumes. Anyone needing that causal claim needs
a design that survives a pre-trend test, and this one does not.

## Q3. What happened to patient and government cost?

Not yet estimated. Output will land in `reports/estimates_cost.csv`.

## Q4. Did concessional and general patients benefit equally?

Not yet estimated. Same model as Q3, split by patient category.

## What this analysis cannot tell you

Parallel trends does not hold here, so nothing above establishes cause. That is the first
and largest limit, and it is documented in Q2 rather than left for a reader to discover.

Dispensing is not consumption. A script collected is not a dose taken.

There is no patient-level data here, so nothing can be said about individual adherence or
about patients who stopped treatment. The dataset has no geographic field, so regional
differences are out of reach. Nothing here measures GP appointment volumes or pharmacy
viability, both of which were argued about when the policy was announced.

The model covers 2,392 drug-form groups, not the 2,749 in the cohort. The 357 missing
groups are all never-eligible, and they have no rows in the panel at all once the
community-pharmacy and patient-category filters are applied. They were never available as
controls.

Standard errors from `did` come from a bootstrap, so they move between runs. The analysis
scripts set a seed, and every number above is reproducible from a fresh clone.
