# Frozen-rule decision accounting

This descriptive revision derives seven additional tables from the existing
verified phase-two calculations. It adds no models or policies and does not
use test results to choose thresholds. Original prediction files, candidate
decisions, bootstrap arrays, model settings and the locked plan are unchanged.

## Findings and provenance

- At r=10, pooled fixed XGBoost no-alarm loss is 42.656326 per 100 shifts.
  C has relative differences 0, 0.678623, 0.824043 and 0.581677 at historical
  budgets 1%, 5%, 10% and 20%. Negative relative difference always means lower
  loss under the specified hypothetical cost; per-phase differences are kept.
- All four reference areas contain positives: 21/103, 1/207, 7/310 and 20/413.
  The 40 historical XGBoost C no-alarm choices split into 28 unconstrained cost
  optima and 12 capacity-induced changes. No case is explained by absent
  reference positives, zero reference slots or a tied nonempty optimum.
- XGBoost historical phase-rule counts are A: 16 finite; B: 9 finite and 7
  +infinity; C: 24 finite and 40 +infinity. None selects -infinity in the primary
  cohort. Counts treat A once per budget, even though losses are evaluated at
  four cost ratios. Extreme-rule invariance is distinct from finite transfer.
- At r=10 and the 20% budget, pooled C-A excess drops by 227, TP drops from 25
  to 2, FN rises from 63 to 86, and loss drops by 13.087736 per 100. These
  quantities describe a workload/detection tradeoff, not a general superiority
  claim. Phase-specific comparisons retain all budgets and both workflows.
- Loss gaps are normalized by reference size. The second candidate is a
  distinct feasible alert set, with NA if absent and zero for optimal ties.
- Prevalence scenarios hold class-conditional error rates and selected rules
  fixed. Relative expected loss and expected alert rate are reported together;
  they are neither observed outcomes nor capacity-exceedance probabilities.

## Files and checks

`decision_value.csv` and `decision_value_pooled.csv` retain all original
evaluation columns and add explicit baseline fields. `threshold_explanations.csv`
and `threshold_audit_enriched.csv` preserve historical cause and selection
information. `refit_transfer.csv` contains 540 complete A/B/C contrasts;
`capacity_tradeoffs.csv` contains 576 paired capacity/detection contrasts;
`prevalence_decision_value.csv` retains all 8,064 frozen scenarios.

The separate `supplement_manifest.json` hashes original inputs and derived
outputs. `supplement_verification.json` records 10,902 independent checks.
Original verification replayed all 15 fixed/refitted model pairs and passed
63,862 checks; 52 existing tests and 8,169 first-stage checks also passed.
The decision-accounting edition passed 531 document checks on eleven pages.
The final contextual edition passed 583 checks on twelve pages, with seventeen
tables and three figures; every rendered page was inspected. Earlier
full-reproduction and document-review records describe their report editions;
numerical experiment evidence remains unchanged.

## Final context and interpretation revision

Table 1 pairs reference/test prevalence (20.39%/6.98%, 0.48%/1.94%,
2.26%/4.65%, 4.84%/3.49%). The one-positive phase-2 reference supplies context;
class-conditional scores may also change, so prevalence is not identified as
the sole cause. All reference areas contain positives, as clarified in the abstract.

The body retains Table 9 unchanged and illustrates its uncertainty using fixed
XGBoost C-A at r=10 and budget 20%: phase 1 +1.356589, 95% interval
[-0.968992, 5.426357]; phase 2 -36.504854, interval [-49.126214, -27.184466].
These are existing conditional paired intervals, not a new selection procedure.

Table 8 defines its setting counts and describes finite alert-change ranges
only within the observed grids. The positive C-B transfer difference is an
observed loss tradeoff, not a guaranteed capacity penalty. Table A5 pairs all
sixteen r=10 budget/prevalence values from frozen rules; Table 11 remains a
marginal-range overview whose two endpoints need not share a budget.
