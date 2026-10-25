# Project directory map

Start with the [research overview](PROJECT_OVERVIEW.md), read the [integrated paper](../reports/overall/integrated_research_report.pdf) for the full argument, then use the [report catalogue](../reports/README.md) and the study map below to inspect technical detail. The two research stages use overlapping records; the supplements do not add independent validation cohorts.

## Studies and their evidence

| Study | Protocol and code | Saved calculations | Report |
| --- | --- | --- | --- |
| Stage 1: forecast reliability and explainability | [Stage 1 workflow](../phase1/README.md) | [Stage 1 evidence](../results/phase1/README.md) | [Technical report](../reports/phase1/technical_report.pdf) |
| Stage 2: historical warning-threshold transfer | [Locked protocol and workflow](../phase2/README.md) | [Reference scores, thresholds and transferred decisions](../results/phase2/README.md) | [Original locked-study technical report](../reports/phase2/phase2_threshold_transfer_report.pdf) |
| Stage 2 supplement: no-alarm and direct-grade comparisons | [Comparator protocol and code](../phase2/comparators/README.md) | [Comparison evidence](../results/phase2/comparators/README.md) | [Integrated paper](../reports/overall/integrated_research_report.pdf) and [complete comparison supplement](../reports/overall/decision_comparison_supplement.pdf) |
| Stage 2 exploratory pilot: within-grade ranking | [Ranking protocol and code](../phase2/ranking/README.md) | [Ranking evidence](../results/phase2/ranking/README.md) | [Ranking short report](../reports/ranking/within_grade_ranking_pilot.pdf) |
| Stage 2 exploratory supplement: matched monitoring information | [Information protocol and code](../phase2/information/README.md) | [Information evidence](../results/phase2/information/README.md) | [Information short report](../reports/information/monitoring_information_increment.pdf); the core finding is also in the integrated paper |

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

## Local environments and temporary work

Local virtual environments and historical review copies are excluded from Git. They are not experimental results or paper deliverables. On the author's workstation, the old review-work directory has been archived outside the checkout with its original bytes, a file inventory and restoration instructions. Environment directories retain their original paths and are hidden in the normal Windows folder view; they remain available for execution.

Future temporary reviews should use an output directory outside the checkout. Saved research evidence under results and historical published records under docs/audits stay in the repository. Current report figures and verification records remain beside their reports because the generators and checkers bind those paths.

## Execution order

Use [Quick Check](QUICK_CHECK.md) to inspect retained evidence. For fresh experiments, follow [complete reproduction](REPRODUCING.md): audit the data, complete Stage 1, run locked Stage 2, then run the separately specified supplements as documented. Use the [reporting guide](../reporting/README.md) to generate and verify papers from the resulting evidence. Reproduce in a separate checkout or output area to preserve the published results.
