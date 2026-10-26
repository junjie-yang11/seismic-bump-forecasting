# Project directory map

Start with the [research overview](PROJECT_OVERVIEW.md), read the [integrated paper](../reports/overall/integrated_research_report.pdf) for the full argument, then use the [report catalogue](../reports/README.md) and the study map below to inspect technical detail. The two research stages use overlapping records; the supplements do not add independent validation cohorts.

## Studies and their evidence

| Study | Protocol and code | Saved calculations | Report |
| --- | --- | --- | --- |
| Stage 1: forecast reliability and explainability | [Stage 1 workflow](../phase1/README.md) | [Stage 1 evidence](../results/phase1/README.md) | [Technical report](../reports/phase1/technical_report.pdf) |
| Stage 2: historical warning-threshold transfer | [Locked protocol and workflow](../phase2/README.md) | [Reference scores, thresholds and transferred decisions](../results/phase2/README.md) | [Original locked-study technical report](../reports/phase2/phase2_threshold_transfer_report.pdf) |
| Stage 2 supplement: no-alarm and direct-grade comparisons | [Comparator protocol and code](../phase2/comparators/README.md) | [Comparison evidence](../results/phase2/comparators/README.md) | [Integrated paper](../reports/overall/integrated_research_report.pdf) and [complete comparison supplement](../reports/comparators/decision_comparison_supplement.pdf) |
| Stage 2 exploratory pilot: within-grade ranking | [Ranking protocol and code](../phase2/ranking/README.md) | [Ranking evidence](../results/phase2/ranking/README.md) | [Ranking short report](../reports/ranking/within_grade_ranking_pilot.pdf) |
| Stage 2 exploratory supplement: matched monitoring information | [Information protocol and code](../phase2/information/README.md) | [Information evidence](../results/phase2/information/README.md) | [Information short report](../reports/information/monitoring_information_increment.pdf); the core finding is also in the integrated paper |

## Research workflow

| Step | What it does | Code | Evidence |
| --- | --- | --- | --- |
| 1 | Audit the official dataset and the mirror transformation | [Source audit](../phase1/audit_source.py), [data loading](../src/data.py) | `results/phase1/source_*` |
| 2 | Fit LR/CART under random and expanding record-order validation | [Baseline experiment](../phase1/run_experiments.py), [shared validation](../src/evaluation.py) | `results/phase1/predictions.csv`, `fold_audit.csv` |
| 3 | Compare the same test rows and assess probabilities | [Paired analysis](../phase1/refresh_analysis.py), [gap calculation](../phase1/gap_summary.py), [metrics](../src/metrics.py), [calibration](../src/calibration.py) | `shared_test_*`, `paired_uncertainty.csv`, `calibration*`, [three-model gaps and shrinkage](../results/phase1/gap_attenuation_all_models.csv) |
| 4 | Evaluate engineering feature groups and XGBoost explanations | [Feature study](../phase1/run_engineering.py), [XGBoost study](../phase1/run_research.py), [explanation analysis](../phase1/research_analysis.py) | `results/phase1/feature_ablation*`, `shap_*`, `warning_budgets*` |
| 5 | Lock Stage 2 settings and separate fitting/reference/test areas | [Locked protocol](../phase2/locked_plan.json), [fold fitting](../phase2/experiment.py) | `results/phase2/fold_manifest.json`, `references.csv`, `tuning*` |
| 6 | Select budget, cost and cost-plus-capacity rules; transfer fixed cutoffs | [Decision rules](../phase2/decisions.py), [experiment](../phase2/run.py) | `candidates.csv`, `audits.csv`, `decisions.csv`, `evaluations.csv` |
| 7 | Compare loss, inspection demand and refitting; evaluate frozen prevalence scenarios | [Paired analysis](../phase2/analysis.py), [decision accounting](../phase2/supplement.py) | `comparisons.csv`, `capacity_tradeoffs.csv`, `refit_transfer.csv`, `prevalence_decision_value.csv` |
| 7a · Supplement | Compare frozen ML rules with no alarms and direct hazard grades | [Separate protocol](../phase2/comparators/protocol.json), [runner](../phase2/comparators/run.py), [independent verifier](../phase2/comparators/verify.py) | [All saved comparisons](../results/phase2/comparators/README.md) |
| 7b · Pilot | Test extra detections within the same grade and exact inspection allocation | [Ranking protocol](../phase2/ranking/protocol.json), [runner](../phase2/ranking/run.py), [independent replay](../phase2/ranking/verify.py) | [Pilot evidence](../results/phase2/ranking/README.md), [short report](../reports/ranking/within_grade_ranking_pilot.pdf) |
| 7c · Matched-information study | Compare monitoring information beyond grades and shift at identical record-block slots | [Protocol](../phase2/information/protocol.json) → [fit and rank](../phase2/information/run.py) → [numerical and refit verification](../phase2/information/verify.py) | [Saved results](../results/phase2/information/README.md) → [short report](../reports/information/monitoring_information_increment.pdf) |
| 8 | Verify saved evidence and generate the papers | [Stage 1 checks](../phase1/verify_results.py), [Stage 2 replay](../phase2/verify.py), [equation checks](../phase1/verify_formulae.py), [paper generators](../reports/README.md) | [Final reports](../reports/README.md), [verification guide](../docs/REPRODUCING.md) |

The filenames in Steps 3–4 belong to `results/phase1/`; those in Steps 5–7 belong to `results/phase2/`. [Result-file guides](../results/README.md) explain their roles.

## What belongs in each directory

| Directory | Contents |
| --- | --- |
| [phase1](../phase1/) | Stage 1 experiment entries, analyses, checks and technical-paper generator |
| [phase2](../phase2/) | Locked Stage 2 protocol, fitting, policy selection, evaluation, checks and the three distinct supplement modules |
| [src](../src/) | Shared data loading, models, metrics, calibration, validation and uncertainty calculations |
| [results](../results/README.md) | Saved computational evidence, including row-level predictions, decisions, candidate audits and version-specific verification |
| [reports](../reports/README.md) | Integrated paper, original technical reports, exploratory short reports, figures and report-generation records |
| [reporting](../reporting/README.md) | Integrated and supplementary paper generators, Word export and separate calculation checks |
| [tests](../tests/) | Shared behavior tests; Stage 2 decision tests also reside in phase2/tests.py |
| [requirements](../requirements/) | Separate baseline, research and reporting dependency lists |
| [data](../data/README.md) | Source documentation and an ignored local download cache |
| [docs](../docs/) | Overview, literature positioning, reproduction instructions and this map |
| [docs/audits](audits/README.md) | Historical reviews and execution records, each limited to its recorded edition |

The root README provides the public entry. [Author contributions](../CONTRIBUTIONS.md), [the licence](../LICENSE) and Git configuration remain at the root.

## Report files and provenance

The main paper's [figures and plotting tables](../reports/overall/figures/) are separate from its [generation and verification records](../reports/overall/metadata/). The [complete comparison supplement](../reports/comparators/README.md) has its own report directory and [records](../reports/comparators/metadata/). The original stage reports and exploratory short reports retain their catalogue entries. The small legacy appendix entry under reports/overall links to its current location.

Use the [current execution manifest](../results/phase2/run_manifest.json), [model and decision replay](../results/phase2/verification.json) and [formula checks](../results/phase2/formula_verification.json) to inspect saved computational evidence. The [dated audit index](audits/README.md) identifies historical reviews; each applies to its recorded edition.

## Execution order

Use [Quick Check](QUICK_CHECK.md) to inspect retained evidence. For fresh experiments, follow [complete reproduction](REPRODUCING.md): audit the data, complete Stage 1, run locked Stage 2, then run the separately specified supplements as documented. Use the [reporting guide](../reporting/README.md) to generate and verify papers from the resulting evidence. Reproduce in a separate checkout or output area to preserve the published results.
