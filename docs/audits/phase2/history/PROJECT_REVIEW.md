# Full project review on 3 October 2026

This review covers both stages, their actual calculations, data provenance,
saved predictions and reference scores, threshold selection, statistical
analyses and final papers. No fabricated observations, substituted model
predictions or placeholder experimental results were found in the checked
materials. Hypothetical costs and prevalence scenarios are explicitly separated
from observed test outcomes.

## Fresh execution and numerical reproduction

A separate project copy started without saved experimental CSVs, fitted models
or bootstrap arrays. The original UCI archive was downloaded again through the
available local proxy. Keeping the first occurrence of every complete ARFF row
reproduces the input mirror in the same order: 2,584 original records, 2,578
mirror records and 170 retained positive targets. All six removed occurrences
are negative duplicates. Both source hashes match the published source audit.

Baseline and engineering fits were repeated with their recorded Python 3.7.0 /
NumPy 1.21.6 environment. XGBoost research and phase two used Python 3.12.14 /
NumPy 2.3.5 / XGBoost 3.1.3. All execution stages exited successfully.

| Fresh comparison | Outcome |
| --- | --- |
| First-stage result tables | All 44 CSVs reproduced |
| Second-stage result tables | All 11 CSVs reproduced |
| Numeric comparison | Maximum absolute difference 4.0245584642661925e-16 |
| Shapes, column names, labels, empty-field positions | Matched |
| Second-stage paired bootstrap arrays | All 3,960,000 values matched |
| Fresh result-only verifier | 8,167 checks passed |
| Fresh phase-two model replay and verifier | 63,853 checks passed |

Fresh verification counts differ from the working-repository counts because
the verifier also checks preserved first-stage files, and the isolated copy
contains fewer historical logs. This does not change the tested records or
experimental results. Per-file hashes and comparisons are retained in
`full_reproduction_review.json`; raw outputs remain in the ignored isolated
audit directory and copied reproduction logs.

Measured execution times were 323.52 seconds for baseline experiments, 81.75
seconds for engineering ablations, 10.53 seconds for extended research and
19.32 seconds for phase two. The tree computations continued to emit progress;
no hung process was observed. Timings describe this machine and these recorded
environments, rather than a runtime guarantee for every installation.

## Logical consistency

- Source measurements and target labels come from the audited mirror. Random
  generators implement declared fold assignment, tree bootstrap, permutation
  analysis and uncertainty resampling. Synthetic test fixtures remain outside
  the experimental evidence.
- The first-stage matched-cohort comparison controls test rows, not training
  history or size. It is not a causal decomposition of temporal leakage.
- LR weighting and historical-prior correction agree with the implementation.
  Bagged CART and XGBoost are unweighted and are not given that correction.
  Raw scores are used for discrimination and frozen-cutoff comparisons.
- Phase-two initial fitting and XGBoost tuning exclude the policy-reference
  area. The refitted comparison deliberately includes that area, retains the
  selected parameters and applies the same numerical threshold to the same
  test rows. Changing test labels cannot change fitted scores or alert rules.
- A, B and C use the locked whole-tie candidate sets and declared tie rules.
  C satisfies historical capacity and has historical loss no lower than B.
  Future capacity and future loss ordering are evaluated outcomes.
- Paired intervals preserve phase sizes and condition on fixed fitted models,
  policies and the observed cohort. Every one of the 2,000 samples per phase
  is independently reconstructed. Complete fitting/selection uncertainty is
  not claimed.
- Prevalence scenarios retain empirical class-conditional error rates and
  frozen rules. They are expected-loss calculations, not new observed shifts,
  real monetary losses, accident avoidance or capacity-excess probabilities.
- Record order remains a time proxy. The previously viewed holdout overlaps
  the primary cohort and supplies descriptive supplementary evidence.

## Repairs made during this review

1. Failed or interrupted reruns now invalidate previous verification success;
   completed-run status is required before accepting evidence.
2. Imported XGBoost settings are checked against the locked protocol. LR and
   CART explicitly consume the locked settings. Imported source dependency
   hashes and the actual XGBoost version are recorded.
3. Verification now reconstructs all paired bootstrap replicates, extending
   the previous eight-sample replay plus full interval-quantile checks.
4. Paper generation checks verified CSVs, manifests, replicate arrays and core
   experimental source hashes. Changed evidence is rejected before authoring.

These repairs do not amend the locked study plan or change its models,
parameters, thresholds, observed decisions or reported scientific conclusions.
Two regression tests cover the newly identified execution/provenance risks.

## Floating-point sensitivity and empty fields

An additional all-Python-3.12 first-stage run also completed and passed 8,167
consistency checks. Near-tied LR scores produced one different historical
reference count (39 versus 61, both within 62 slots) and two small ROC-AUC
differences for the without-geophone subset. The largest ROC difference was
0.0001980198019801982. Permutation importance values match by feature, but tied
row ordering can differ. Published warning/loss results were unchanged. Exact
published-result reproduction uses the recorded stage-specific environments;
the alternative computation is retained in `cross_environment_review.json`.

All 307 first-stage and 2,952 second-stage empty cells were classified by file
and column in `undefined_field_review.json`. They indicate inapplicable budgets
or cost objectives, pooled policies without one scalar cutoff, correlations
with constant features or division by zero detection counts. They are not
replacement observations. Actual per-phase cutoffs and decisions remain saved.
Infinity is the declared all/no-alarm cutoff sentinel, not a model prediction.

## Code and paper checks

All 43 Python source files parse. All 52 tests pass (42 existing and 10
phase-two tests). Working-repository verification passes 8,169 integrated
checks, 7,460 extended checks with independent XGBoost/TreeSHAP replay, and
63,862 phase-two checks with all fixed/refitted model pairs replayed.

The unchanged first-stage Word paragraphs and tables match its result-driven
manuscript; 207 distinct four-decimal values match the 15-page PDF. The updated
second-stage Word/PDF/manuscript passed 352 correspondence checks. All nine
second-stage pages were inspected: no clipped content, broken tables, orphan
references or inherited title borders were found. The report remains three
figures, eight main tables and one supplementary pooled table.

The principal scientific results and study plan are retained. The code now has
stronger safeguards against stale execution records and evidence mismatch.
