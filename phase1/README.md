# Stage 1 · Forecast reliability and explainability

**Question:** how do comparable evaluation cohorts, probability calibration and model explanations change the interpretation of seismic hazard forecasting?

Read the [paper](../reports/phase1/technical_report.pdf) or [editable Word version](../reports/phase1/technical_report.docx). All measured outputs belong to `results/phase1/`; shared models and metric implementations live in `src/`.

## Execution order

Run from the repository root. Baseline and engineering fits use the recorded Python 3.7 environment; the XGBoost extension and complete tests use the research environment. [Environment details](../docs/REPRODUCING.md) describe the separate installations.

| Order | Command | Code responsibility |
| --- | --- | --- |
| 1 | `python -m phase1.audit_source` | Official-to-mirror mapping, duplicate audit and source hashes |
| 2 | `python -m phase1.run_experiments` | LR/CART random, record-order and holdout fits; calibration and matched-cohort analysis |
| 3 | `python -m phase1.run_engineering` | Nine prespecified engineering feature sets and frozen warning budgets |
| 4 | `python -m phase1.run_research` | Training-only XGBoost tuning, native TreeSHAP and common-cohort comparisons |
| 5 | `python -m phase1.verify_research --replay` | Independent fitted-model and explanation reproduction |
| 6 | `python -m phase1.generate_report --docx` | Result-driven Markdown and Word authoring |
| 7 | `pwsh -NoProfile -ExecutionPolicy Bypass -File phase1/export_report.ps1` | Microsoft Word PDF export on Windows |
| 8 | `python -m phase1.verify_results --reports` | Result, coverage, provenance and report consistency |

The baseline run already refreshes paired analyses; the research run refreshes review supplements. `refresh_analysis` and `review_analysis` are available when rebuilding summaries from existing evidence, without repeating fits. `refresh_analysis --rebuild` explicitly refits random predictions.

## Code map

| Module | Purpose |
| --- | --- |
| `audit_source.py` | Original data, mirror transformation and row mapping |
| `run_experiments.py` | Baseline experiment entry point |
| `refresh_analysis.py` | Common-cohort curves, paired intervals and operating diagnostics |
| `run_engineering.py`, `engineering_figures.py` | Engineering-group comparisons and charts |
| `run_research.py`, `research_analysis.py`, `research_figures.py` | XGBoost, SHAP, feature comparisons and research figures |
| `review_analysis.py` | Probability-reference and constant-feature stability summaries |
| `verify_results.py`, `verify_research.py`, `verify_additions.py`, `verify_review.py` | Independent evidence checks |
| `verify_formulae.py` | Cross-stage equation audit; run after Stage 2 finishes |
| `quick_check.py` | Cross-stage saved-evidence checks in a disposable copy; preserves published records |
| `generate_report.py`, `paper_content.py`, `research_paper.py` | Shared package cleanup, baseline and extended paper content |
| `record_environment.py` | Record the exact baseline execution environment |

The baseline manuscript is needed when reproducing Stage 1 before the XGBoost extension exists. It is retained as part of the executable sequence rather than as a second final paper. Shared, Stage 1 and repository regression tests live under `tests/`; they also check verification-record failure handling, result-driven report text and the homepage evidence table. Stage 2 decision tests live in `phase2/tests.py`.

[Stage 1 results](../results/phase1/README.md) · [Stage 2](../phase2/README.md) · [Project home](../README.md)
