# Reproduce the two-stage workflow

Run commands from the repository root. Results are separated by stage and final papers are under `reports/`. The [home-page workflow](../README.md) maps every step to code; [Stage 1](../phase1/README.md) and [Stage 2](../phase2/README.md) explain the modules.

For inspection before fitting, use the [quick verification entry](QUICK_CHECK.md): `python -B -m phase1.quick_check`. It checks saved evidence in a disposable copy and preserves the published replay records. The sequence below performs complete model reproduction and writes fresh experiment and verification outputs.

## Environments

Keep three environments separate. Install from `requirements/requirements.txt` in the recorded baseline Python 3.7 environment, `requirements/requirements-research.txt` in Python 3.12 for XGBoost and complete checks, and `requirements/requirements-report.txt` for document authoring. The baseline environment record is `results/phase1/environment.txt`; the extended and Stage 2 manifests record their actual runtime versions. PDF export uses installed Microsoft Word on Windows.

The supported and actually exercised release environment is Windows x64, Python 3.12.14, NumPy 2.3.5, pandas 3.0.1, SciPy 1.18.1 and XGBoost 3.1.3, with the recorded baseline environment for Stage 1 LR/CART fitting. Word export uses PowerShell 7. Complete installed packages, numerical-library configuration, XGBoost build information and locked run settings are captured by the [separate threshold replay](audits/2026-10-07-stable-release/check_threshold_replay.py). Dependency versions alone do not establish identical compiled numerical backends.

Linux/macOS model replay and PDF export are not certified by this release. The Linux feedback came from a separate AI inspection environment; its dependency/build details and replay logs are not retained in this checkout. The local WSL query failed because WSL was not installed. Consequently this review does not establish the cause or magnitude of any external Linux difference. Retain the external replay record and compare its build information, inputs and settings with the Windows record before attributing differences to a platform. Do not change the locked threshold or relax score tolerances to obtain a pass.

For an available second environment, run the existing replay and the separate score/decision audit:

```text
python -B -m phase2.verify --replay
python -B docs/audits/2026-10-07-stable-release/check_threshold_replay.py --root . --output threshold-replay.json
```

The audit refits all 15 model pairs, compares reference and test scores using the existing verifier's criterion, and compares transferred A/B/C alerts by exact Boolean equality. It preserves failed output, reports maximum score differences separately from changed alerts, and never reselects a threshold from test scores. The supported-environment result and remaining checks are recorded in the [stable release review](audits/2026-10-07-stable-release/RELEASE.md).

## 1 · Audit and fit Stage 1

In the baseline environment:

```powershell
python -m phase1.audit_source
python -m phase1.run_experiments
python -m phase1.run_engineering
```

`audit_source --source PATH_TO_ARFF` uses an existing official file; `--proxy URL` explicitly supplies a download proxy. Data loading downloads the mirror when the local cache is absent. No cached source file is committed.

In the research environment:

```powershell
python -m phase1.run_research
python -m phase1.verify_research --replay
python -B -m unittest discover -s tests -v
```

These commands save row-level scores, training priors, engineering comparisons, SHAP contributions and conditional uncertainty. Baseline fitting refreshes matched-cohort summaries; the research run updates review supplements. Do not rebuild the final extended paper before the extension finishes.

## 2 · Finish the Stage 1 paper

In the reporting environment, then the research environment for verification:

```powershell
python -m phase1.generate_report --docx
pwsh -NoProfile -ExecutionPolicy Bypass -File phase1/export_report.ps1
python -m phase1.verify_results --reports
```

The generator reads saved evidence; it does not fit models. Word and Markdown share the result-driven manuscript. Stage 2 records Stage 1 evidence hashes, so complete any Stage 1 changes before running Stage 2.

## 3 · Fit and verify Stage 2

In the research environment:

```powershell
python -B -m unittest phase2.tests -v
python -B -m phase2.run
python -B -m phase2.verify --replay
python -B -m phase2.supplement
python -B -m phase2.verify_supplement
python -B -m phase1.verify_formulae
```

The locked protocol is checked before fitting. Historical reference data select thresholds; test labels enter evaluation. Refitting retains parameters and the same numerical cutoff. `verify --replay` independently reconstructs all fitted model pairs and the paired resampling. The supplement accounts for no-alarm value, selection reasons, refitting and frozen scenarios without choosing another policy.

Main and supplementary verifiers invalidate any previous certificate when an invocation starts, and retain a failed status if it raises an error. The Stage 2 report also requires the current verifier identity. After changing verification code, rerun verification and replay before rebuilding the report; an older successful record does not certify the new code.

`verify_formulae` independently reconstructs ranking metrics, prior correction, probability references, calibration, SHAP additivity, decision loss, capacity excess and prevalence expectations from actual saved evidence.

## 4 · Finish the Stage 2 paper

In the reporting environment:

```powershell
python -B -m phase2.report
pwsh -NoProfile -ExecutionPolicy Bypass -File phase2/export_report.ps1
python -B -m phase2.update_readme
python -B -m phase2.update_readme --check
python -B -m phase2.verify_report --root . --baseline PATH_TO_PREVIOUS_EDITION --output reports/phase2/report_verification.json
```

The report requires a completed verified experiment, full replay and verified supplementary accounting. Its saved manifest identifies all CSV inputs and its generator. Inspect the exported pages for layout as well as numeric agreement.

The homepage updater reads the saved pooled fixed-XGBoost C results at r=10, independently reconstructs relative loss from TP/FP counts, and replaces only the marked table. It does not fit models or modify results. The Stage 2 report-table implementation is `phase2/verify_report.py`; the dated `docs/audits/2026-10-07-full-review/check_report_tables.py` command delegates to it for compatibility. It invalidates a previous success before reading inputs and saves an error on failure; its regression corrupts the current manifest after a saved success. The previous-edition path is a preserved checkout used to confirm that the interval overview (Table 9) is unchanged; it supplies no replacement results.

## Reading the records

Current experiment manifests belong to `results/phase1/` and `results/phase2/`. Final manuscript provenance accompanies the paper. Dated review editions are kept in `docs/audits/`; historical paths and hashes describe their original editions. The final reports retain the study boundaries: record order is a temporal proxy, holdout results are supplementary, costs and capacity are hypothetical, and intervals condition on fixed predictions or fitted rules.

The [complete October 7 review](audits/2026-10-07-full-review/REVIEW.md) records fresh fitting, replay, result comparison, report checks and failed platform attempts. Run full reproduction in a separate clone or worktree with its own output folders: the experiment commands overwrite that checkout's `results/` and `reports/`. Complete Stage 1, including its PDF export, before fitting Stage 2 so its source snapshot includes the finished paper. On Windows use the `pwsh` command shown above; the review's Windows PowerShell export stalled, while PowerShell 7 completed.
