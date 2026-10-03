# Reproduce the two-stage workflow

Run commands from the repository root. Results are separated by stage and final papers are under `reports/`. The [home-page workflow](../README.md) maps every step to code; [Stage 1](../phase1/README.md) and [Stage 2](../phase2/README.md) explain the modules.

## Environments

Keep three environments separate. Install from `requirements/requirements.txt` in the recorded baseline Python 3.7 environment, `requirements/requirements-research.txt` in Python 3.12 for XGBoost and complete checks, and `requirements/requirements-report.txt` for document authoring. The baseline environment record is `results/phase1/environment.txt`; the extended and Stage 2 manifests record their actual runtime versions. PDF export uses installed Microsoft Word on Windows.

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

`verify_formulae` independently reconstructs ranking metrics, prior correction, probability references, calibration, SHAP additivity, decision loss, capacity excess and prevalence expectations from actual saved evidence.

## 4 · Finish the Stage 2 paper

In the reporting environment:

```powershell
python -B -m phase2.report
pwsh -NoProfile -ExecutionPolicy Bypass -File phase2/export_report.ps1
```

The report requires a completed verified experiment, full replay and verified supplementary accounting. Its saved manifest identifies all CSV inputs and its generator. Inspect the exported pages for layout as well as numeric agreement.

## Reading the records

Current experiment manifests belong to `results/phase1/` and `results/phase2/`. Final manuscript provenance accompanies the paper. Dated review editions are kept in `docs/audits/`; historical paths and hashes describe their original editions. The final reports retain the study boundaries: record order is a temporal proxy, holdout results are supplementary, costs and capacity are hypothetical, and intervals condition on fixed predictions or fitted rules.
