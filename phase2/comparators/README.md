# Frozen policies and direct hazard grades

This independent Stage 2 supplement adds policy-minus-no-alarm and fixed-XGBoost-minus-grade loss intervals. It reuses the saved fixed XGBoost model decisions and original reference/test rows. It fits no model and does not reselect any ML threshold. The [protocol](protocol.json) was recorded before these supplemental calculations, after inspection of the original study; this is exploratory retrospective work.

Run from the repository root, using the existing research environment and cached audited data mirror:

```text
python -B -m phase2.comparators.run
python -B -m phase2.comparators.verify
```

For each of `seismic`, `seismoacoustic` and `ghazard`, A/B/C selects a grade threshold using only the original historical reference rows. Equal grades stay together. Each distinct reference alert set has one canonical cutoff; absent grade levels do not add duplicate choices. The selected cutoff is frozen for the later block. UCI explicitly defines the seismic severity sequence; the common `a < b < c < d` ordering for the other assessments is the study's ordinal interpretation of their shared ARFF coding, not a verified operational procedure. The mirror contains only a/b for seismic and a/b/c for the other fields.

All original costs and budgets are retained. A is selected once per budget and evaluated at each cost; B is selected per cost without a capacity condition. C uses both settings. No grade field is selected by test performance.

The code saves [references, candidates, audits and row decisions](../../results/phase2/comparators/README.md), all 720 phase/pooled evaluations, all 1,260 paired intervals and every resampling multiplicity/replicate. Resampling uses the existing length-32 within-phase moving-block design, 2,000 draws and seed convention. Both sides always receive identical draws. Intervals condition on frozen decisions and the observed cohort, exclude fitting/reselection uncertainty and are unadjusted across comparisons. Identical or zero-alert policies can give [0,0] intervals by construction.

The independent verifier enumerates grade candidates and optima without calling the production selector, checks saved ML decisions exactly, reconstructs every loss/capacity count, and regenerates all draws and 2,520,000 paired loss replicates. Arithmetic comparisons use a numerical rounding bound of 1e-12; threshold and alert comparisons are exact.

After both verifiers pass, use the [integrated reporting commands](../../reporting/README.md). The original stage papers and experiment outputs remain the locked-study edition; the integrated report and its [complete comparison appendix](../../reports/overall/comparator_appendix.md) present this addition.
