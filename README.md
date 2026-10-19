# Seismic Hazard Forecasting and Warning Decisions

**A retrospective mining study of how forecast evidence translates into warning loss, detections and inspection workload.**

The project uses the audited UCI Seismic Bumps mirror: 2,578 shift records and 170 hazardous-shift labels. It follows the evidence from monitoring inputs to predictions, calibration, historical threshold selection and later inspection workload.

## Start here

Start with the research overview for the questions, findings and study scope. Read the integrated report for the complete argument, then use the technical reports and workflow guide to inspect methods, code and evidence.

| Reading level | Entry | What it provides |
| --- | --- | --- |
| Quick introduction | [Research overview](docs/PROJECT_OVERVIEW.md) | Research questions, main findings, contribution and study boundaries |
| Complete argument | [Integrated report: PDF](reports/overall/integrated_research_report.pdf) · [Word](reports/overall/integrated_research_report.docx) · [Online manuscript](reports/overall/integrated_research_report.md) | Methods, results, discussion and the evidence chain |
| Technical detail and reproduction | [Technical reports and supplements](reports/README.md) · [Workflow](#follow-the-research-workflow) · [Reproduction guide](docs/REPRODUCING.md) | Stage-specific protocols, supplementary studies, code and verification |

The integrated report connects comparable-cohort forecast evidence to warning loss, coverage, capacity and model updating. The two technical reports below retain stage-specific methods and full results; they use overlapping records and are not independent validation studies.

| Study | Question | Final paper | Editable paper | Code and steps |
| --- | --- | --- | --- | --- |
| **Stage 1 · Forecast evaluation** | How do comparable test cohorts, probability calibration and model explanations change the interpretation of performance? | [PDF](reports/phase1/technical_report.pdf) | [Word](reports/phase1/technical_report.docx) | [Stage 1 guide](phase1/README.md) |
| **Stage 2 · Locked warning experiment** | How do historical thresholds transfer under assumed missed-event costs and inspection capacity? | [Locked-study PDF](reports/phase2/phase2_threshold_transfer_report.pdf) | [Word](reports/phase2/phase2_threshold_transfer_report.docx) | [Stage 2 guide](phase2/README.md) · [Added grade/interval analysis](phase2/comparators/README.md) |

Use Stage 1 for predictive detail and Stage 2 for decision detail. [Report navigation and generation](reports/README.md) distinguish the integrated paper from its supporting technical reports.

The **latest complete forecasting/decision analysis**, including direct grades and no-alarm intervals, is in the integrated report above and its [full comparison appendix](reports/overall/comparator_appendix.md). The original Stage 2 PDF retains the locked-experiment edition. A separate [within-grade ranking pilot](phase2/ranking/README.md) asks a new equal-capacity batch question; its [short report](reports/ranking/within_grade_ranking_pilot.pdf) does not replace the main study.

## Three findings

1. **Who is tested changes the apparent validation gap.** On common test records, the original random-versus-record-order AP gap shrinks by 89.7% for LR and 86.9% for CART; residual differences are 0.0114 and 0.0188. This recalculation shows cohort sensitivity, not a causal decomposition of leakage or drift. [Matched results](results/phase1/shared_test_comparison.csv) · [Gap calculation](results/phase1/gap_attenuation.csv).
2. **Pooled loss point estimates and interval evidence answer different questions.** At `r=10`, pooled fixed XGBoost cost-plus-capacity rule C has point differences of **0.00 to +0.82 relative loss units per 100 shifts** versus no alarms. The nonzero pooled conditional intervals still include loss improvement and increase. Phase 1 C at 5% and 10% has no detections and entirely positive loss-difference intervals. These findings apply to the assumed cost and observed records. [Point comparisons](results/phase2/decision_value_pooled.csv) · [Phase and pooled intervals](results/phase2/comparators/intervals.csv).
3. **Historical capacity feasibility does not guarantee future feasibility.** Budget rule A exceeds later capacity in **13/16 phase–budget settings**; C does so in **2/64 phase–budget–cost settings**. These are different, dependent setting counts, not directly comparable independent violation rates. Refitting can also change alerts at the same finite numerical cutoff. [Capacity and detection](results/phase2/capacity_tradeoffs.csv) · [Refitting](results/phase2/refit_transfer.csv).

## Read the decision tradeoff

<!-- BEGIN GENERATED DECISION TABLE -->
**Fixed XGBoost · rule C · r=10 · four later blocks pooled (2,063 shifts; 88 hazardous labels).**

| Historical budget | Δ loss / 100 vs no alarms | TP | FN | Alerts |
| --- | --- | --- | --- | --- |
| 1% | 0.00 | 0 | 88 | 0 |
| 5% | +0.68 | 1 | 87 | 25 |
| 10% | +0.82 | 1 | 87 | 28 |
| 20% | +0.58 | 2 | 86 | 34 |

**Negative differences mean lower assumed loss; positive differences mean higher loss.** False-alert cost is 1 and missed hazardous-shift cost is 10. Budgets constrain historical selection, not later workload. TP counts hazardous shifts flagged, not inspections completed or accidents prevented.

Generated from [saved pooled results](results/phase2/decision_value_pooled.csv) by [the table updater](phase2/update_readme.py); Δ loss is independently reconstructed as `100(FP − 10TP)/N`.
<!-- END GENERATED DECISION TABLE -->

The [full loss-contrast figure](reports/phase2/loss_contrasts.png) retains C−A and C−B comparisons by phase, budget and cost. Negative differences favor C; panels use separate color scales. The compact table above uses the separate no-alarm baseline. [Cost equality for frozen policies](results/phase2/frozen_policy_cost_boundaries.csv) distinguishes historical selection cost from evaluation cost. [Frozen prevalence scenarios](results/phase2/prevalence_decision_value.csv) also report expected precision alongside loss and workload; neither extension reselects a threshold.

The [frozen-policy supplement](phase2/comparators/README.md) adds no-alarm loss intervals and direct rules for each of three hazard-grade fields. At `r=10`, the nonzero pooled C comparisons versus no alarms or the grade rules have intervals spanning zero. These conditional comparisons do not establish ML loss superiority or equivalence. [All phase/cost combinations](reports/overall/comparator_appendix.md) · [Saved evidence and independent replay](results/phase2/comparators/README.md).

At `r=10`, the three grade B rules make identical decisions: all records in phase 1 are flagged and none later. Their common result is 36 detections, 480 false alerts and 516 alerts; XGBoost B gives 35, 379 and 414. Its lower loss against that common rule reflects 101 fewer false alerts at the cost of one fewer detection, not three distinct confirmations.

## Contribution and study scope

The project contributes an audited data transformation, comparable-cohort evaluation, training-local probability and threshold handling, and joint accounting of transferred loss, detection, capacity and refitting. Established model and decision methods support these empirical findings. [Author contributions and AI assistance](CONTRIBUTIONS.md) · [Related work and method origins](docs/RELATED_WORK.md) · [Study boundaries and next questions](docs/PROJECT_OVERVIEW.md#study-boundaries-and-next-questions).

Recorded order is a temporal proxy, costs are hypothetical, and the labels describe hazardous shifts. These studies do not demonstrate prevented accidents or an operationally optimal warning system.

## Quick verification

With Python 3.12 and the [research dependencies](requirements/requirements-research.txt), run from the repository root:

```text
python -B -m phase1.quick_check
```

This checks saved evidence and formulas in a disposable copy, preserves published verification records and ends with `QUICK CHECK PASSED` if all checks succeed. It downloads the mirror only when the local cache is absent. These are project-run checks through separate calculation paths, not a claim of external third-party replication. [Verification types](docs/QUICK_CHECK.md#verification-scope) · [Setup and measured runtime](docs/QUICK_CHECK.md) · [Full model reproduction](docs/REPRODUCING.md).

## Follow the research workflow

| Step | What it does | Code | Evidence |
| --- | --- | --- | --- |
| 1 | Audit the official dataset and the mirror transformation | [Source audit](phase1/audit_source.py), [data loading](src/data.py) | `results/phase1/source_*` |
| 2 | Fit LR/CART under random and expanding record-order validation | [Baseline experiment](phase1/run_experiments.py), [shared validation](src/evaluation.py) | `results/phase1/predictions.csv`, `fold_audit.csv` |
| 3 | Compare the same test rows and assess probabilities | [Paired analysis](phase1/refresh_analysis.py), [metrics](src/metrics.py), [calibration](src/calibration.py) | `shared_test_*`, `paired_uncertainty.csv`, `calibration*` |
| 4 | Evaluate engineering feature groups and XGBoost explanations | [Feature study](phase1/run_engineering.py), [XGBoost study](phase1/run_research.py), [explanation analysis](phase1/research_analysis.py) | `results/phase1/feature_ablation*`, `shap_*`, `warning_budgets*` |
| 5 | Lock Stage 2 settings and separate fitting/reference/test areas | [Locked protocol](phase2/locked_plan.json), [fold fitting](phase2/experiment.py) | `results/phase2/fold_manifest.json`, `references.csv`, `tuning*` |
| 6 | Select budget, cost and cost-plus-capacity rules; transfer fixed cutoffs | [Decision rules](phase2/decisions.py), [experiment](phase2/run.py) | `candidates.csv`, `audits.csv`, `decisions.csv`, `evaluations.csv` |
| 7 | Compare loss, inspection demand and refitting; evaluate frozen prevalence scenarios | [Paired analysis](phase2/analysis.py), [decision accounting](phase2/supplement.py) | `comparisons.csv`, `capacity_tradeoffs.csv`, `refit_transfer.csv`, `prevalence_decision_value.csv` |
| 7a · Supplement | Compare frozen ML rules with no alarms and direct hazard grades | [Separate protocol](phase2/comparators/protocol.json), [runner](phase2/comparators/run.py), [independent verifier](phase2/comparators/verify.py) | [All saved comparisons](results/phase2/comparators/README.md) |
| 7b · Pilot | Test extra detections within the same grade and exact inspection allocation | [Ranking protocol](phase2/ranking/protocol.json), [runner](phase2/ranking/run.py), [independent replay](phase2/ranking/verify.py) | [Pilot evidence](results/phase2/ranking/README.md), [short report](reports/ranking/within_grade_ranking_pilot.pdf) |
| 8 | Verify saved evidence and generate the papers | [Stage 1 checks](phase1/verify_results.py), [Stage 2 replay](phase2/verify.py), [equation checks](phase1/verify_formulae.py), [paper generators](reports/README.md) | [Final reports](reports/README.md), [verification guide](docs/REPRODUCING.md) |

The filenames in Steps 3–4 belong to `results/phase1/`; those in Steps 5–7 belong to `results/phase2/`. [Result-file guides](results/README.md) explain their roles.

## Repository structure

```text
phase1/              Stage 1 experiments, analysis, verification and paper generator
phase2/              Stage 2 locked protocol, decisions, transfer study and paper generator
reports/
  overall/           Main integrated paper, conceptual overview and report provenance
  phase1/            Final Stage 1 Word, PDF and manuscript
  phase2/            Final Stage 2 Word, PDF, manuscript and report figures
  ranking/           Separate exploratory within-grade ranking short report
results/
  phase1/            Stage 1 predictions, metrics, explanations and diagnostic figures
  phase2/            Stage 2 references, thresholds, decisions and verification evidence
src/                 Shared data, models, metrics, calibration and validation
reporting/           Cross-stage paper generator, Word export and independent checks
tests/               Shared and Stage 1 behavioral tests; Stage 2 tests live in phase2/
data/                Data-source guide and ignored local download cache
requirements/        Separate baseline, research and reporting environments
docs/                Reproduction guide and dated audit history
```

## Reproduce or inspect

- [Current execution manifest](results/phase2/run_manifest.json) · [Model and decision replay](results/phase2/verification.json) · [Formula checks](results/phase2/formula_verification.json) · [Report checks](reports/phase2/report_verification.json)
- [Stable-version checks and environment support](docs/audits/2026-10-07-stable-release/RELEASE.md)
- [Complete execution sequence and environment requirements](docs/REPRODUCING.md)
- [Research overview](docs/PROJECT_OVERVIEW.md) · [Related work and contribution](docs/RELATED_WORK.md)
- [Quick verification of saved evidence](docs/QUICK_CHECK.md)
- [Stage 1 commands](phase1/README.md) · [Stage 2 protocol and commands](phase2/README.md)
- [Saved evidence](results/README.md) · [Final reports](reports/README.md)
- [Code and structure cleanup record](docs/audits/STRUCTURE_CLEANUP.json)
- [Structure and verification review](docs/audits/STRUCTURE_REVIEW.md)
- [Research presentation release review](docs/audits/RESEARCH_PRESENTATION_REVIEW.md)
- [Manuscript review and verification](docs/audits/SKILL_EDITORIAL_REVIEW.md)
- [Complete code, workflow and fresh-reproduction review](docs/audits/2026-10-07-full-review/REVIEW.md)

Run commands from the repository root. Stage 1 uses `python -m phase1.<command>`; Stage 2 uses `python -m phase2.<command>`. Dated audit records describe their original editions and retain the paths used then. The current manifests and verification records above identify the inputs and verifier versions checked for this checkout.

## Data and license

[Data provenance](data/README.md) identifies the official source and mirror. Raw data are downloaded to the ignored local cache. Code uses the [MIT license](LICENSE).
