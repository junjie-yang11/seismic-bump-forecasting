# Second-stage change record

Structure cleanup, 3 October 2026: Stage 1 commands now use phase1; final papers
are centralized in reports/phase1 and reports/phase2, and experimental outputs
are separated in results/phase1 and results/phase2. Historical reviews are
archived under docs/audits. Removed verified dead helpers/imports and duplicate
SVG exports; consolidated reporting dependencies. All 62 CSVs and 3,960,000
bootstrap values remain unchanged. See docs/audits/STRUCTURE_REVIEW.md and
STRUCTURE_VERIFICATION.json for this edition.

Comprehensive release review, 3 October 2026: reproduced both stages from an
empty results directory, compared 62 CSVs and 3,960,000 bootstrap values, and
passed 54 behavioral tests. Fixed numeric binary alert evaluation and invalid
capacity-budget handling, without changing experiment results. Corrected the
shared nbumps comment and polished both papers; reviewed all 27 final pages.
See docs/audits/RELEASE_REVIEW.md and release_verification.json for this edition.

Final factual correction, 3 October 2026: corrected the stage-one nbumps
description in both body and appendix after independently confirming the two
unequal mirror rows. Added the cross-stage workflow and threshold-definition
link, stage-one and block-bootstrap references, and integer Figure 3 alert
annotations. Numerical tables, models, data and locked settings are retained.
See docs/audits/FINAL_FACTUAL_CORRECTIONS.md and final_factual_verification.json.

Editorial update, 3 October 2026: both papers now lead with their supported
findings and connect interpretation to warning decisions. Numerical tables,
the locked research design and measured evidence are unchanged. Updated
Word/PDF/manuscript outputs and verified current provenance. The actual
stage-two rerun reproduces all 18 CSVs and 3,960,000 bootstrap values exactly.
See docs/audits/PAPER_EDITORIAL_REVIEW.md and editorial_verification.json.
Earlier verification entries below describe the editions reviewed at those times.

Completed 3 October 2026. The original first-stage experiment code, report and
result files were retained. Their saved hashes were checked again after report
generation. No locked protocol amendments were made.

| Added file | Purpose |
| --- | --- |
| `plan.py`, `locked_plan.json` | Pre-execution settings, selection rules, timestamp and checksum |
| `decisions.py` | Canonical whole-tie thresholds, A/B/C, batch reference and metrics |
| `experiment.py` | Fitting/reference isolation and same-cutoff refitting workflow |
| `run.py` | All models/phases, row-level evidence and execution provenance |
| `analysis.py` | Prespecified paired block intervals and frozen prevalence scenarios |
| `tests.py` | Eight behavioral boundary, tie and leakage checks |
| `verify.py` | Independent counts, choices, loss, capacity, interval and model replay checks |
| `report.py`, `export_report.ps1` | Independent academic Word/manuscript and PDF export |
| `requirements-report.txt` | Reporting dependencies kept separate from experiment dependencies |
| `README.md`, `implementation_log.md`, `CHANGELOG.md` | Reproduction, conventions and implementation corrections |

The only existing-file edit is `.gitignore`, which now permits second-stage
CSV evidence in `results/phase2/` to be tracked. All second-stage outputs are
inside that independent directory.

Validation after full project review: 42 existing tests plus 10 second-stage
tests passed. Independent verification passed 63,862 checks, replaying all 15
fixed/refitted model pairs and every paired bootstrap replicate.
The current twelve-page report passed 584 document/result checks, and all twelve
rendered pages were inspected. It contains three figures, twelve main tables and
five supplementary tables. Full model/cost/budget combinations are the
saved electronic appendix, rather than selected favorable settings.

Actual evaluation files and hypothetical frozen-prevalence expectations are
separate. Undefined quantities are empty cells with documented meanings.
The run and report manifests retain checksums; neither scenario assumptions
nor synthetic unit-test fixtures are presented as measured experimental data.

The review strengthened failed-run invalidation, locked model-setting checks,
imported dependency hashes and paper provenance checks. The recorded-environment
fresh execution reproduced all 55 first/second-stage CSVs and all 3,960,000
phase-two bootstrap values. An additional environment comparison documents
floating-point sensitivity near ties. Full evidence and corrections are in
`results/phase2/PROJECT_REVIEW.md`, `full_reproduction_review.json` and
`cross_environment_review.json`.

The subsequent descriptive decision-accounting revision added seven derived
CSV files and a separate independent verifier (10,902 checks). It promoted
no-alarm value to the main results, explained all 40 XGBoost no-alarm settings
from reference decisions (28 cost optima, 12 capacity-induced changes), exposed
finite and extreme A/B/C refitting groups, paired capacity changes with
detection changes, normalized next-decision margins, and displayed frozen
prior-shift relative loss alongside expected workload. No model, parameter,
threshold, original prediction, bootstrap sample or locked rule changed.

Final contextual revision on 3 October 2026: Table 1 now pairs reference and
test prevalence; the discussion identifies the one-positive/207-record phase-2
reference as context without attributing transfer solely to prevalence shift.
Table 8 defines distinct A/B/C setting counts and limits its range comparison
to the observed finite settings. Positive C-B loss is an observed transfer
tradeoff, not a guaranteed capacity penalty. Table 9 is unchanged; the text
adds two existing r=10, budget-20% XGBoost C-A intervals. Table A5 pairs
scenario loss and workload for every budget at r=10, while Table 11 remains
the marginal-range overview. The abstract clarifies that all reference areas
contain positives. Models, rules and numerical experiment evidence are unchanged.

Current full audit: fresh execution reproduced 62 CSV files and 3,960,000
bootstrap values. Independent formula verification passed 8,220 checks.
Stage-one paper reproduction commands were corrected after reorganization;
actual phase-two execution refreshed the protected-paper provenance and
retained identical numerical results. Both final papers were visually reviewed.
See docs/audits/FINAL_PROJECT_REVIEW.md and final_integrity_review.json.
