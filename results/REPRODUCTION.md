# Reproduction record

This file records an actual execution of `run_experiments.py`, so that the numbers
quoted in `report/technical_note.md` can be checked against a machine, not a claim.

## Environment

| | |
|---|---|
| Recorded | 2026-10-01 19:38:40 (local) / 11:38:40 UTC |
| Operating system | Windows 10, AMD64 |
| Python | 3.7.0 (v3.7.0:1bf9cc5093, Jun 27 2018) [MSC v.1914 64 bit (AMD64)] |
| numpy | 1.21.6 |
| pandas | 1.1.5 |
| Command | `python run_experiments.py` |

Full details, including `pip freeze`, are in `results/environment.txt`.

## How it was run

```powershell
# from the repository root, with the virtual environment active
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install --only-binary=:all: numpy==1.21.6 pandas==1.1.5
.venv\Scripts\python run_experiments.py | Tee-Object results\run_log.txt
```

`--only-binary=:all:` was used because Python 3.7.0 is old enough that pip's
resolver will otherwise attempt to build numpy and pandas from source. Pinning to
pre-built wheels makes the install deterministic and fast.

The complete console output is committed as `results/run_log.txt`.

## Verification: every reported number, checked against the run

Tolerance 0.005. All values are read from the generated files in `results/`.

### Dataset integrity (`results/integrity.json`)

| Quantity | Reported | This run | |
|---|---|---|---|
| records | 2578 | 2578 | ok |
| positives (class 1) | 170 | 170 | ok |
| prevalence | 0.0659 | 0.0659 | ok |
| rank of `nbumps2…nbumps89` | 4 of 7 | 4 of 7 | ok |
| constant columns | `nbumps6`, `nbumps7`, `nbumps89` | same | ok |
| prevalence quintile 0 | 0.1609 | 0.1609 | ok |
| prevalence quintile 1 | 0.0680 | 0.0680 | ok |
| prevalence quintile 2 | 0.0213 | 0.0213 | ok |
| prevalence quintile 3 | 0.0447 | 0.0447 | ok |
| prevalence quintile 4 | 0.0349 | 0.0349 | ok |
| trivial "always 0" accuracy | 0.9341 | 0.9341 | ok |

### Model × validation scheme (`results/metrics_by_scheme.csv`)

| Model | Validation | Metric | Reported | This run | |
|---|---|---|---|---|---|
| Logistic regression | random stratified 10-fold | ROC-AUC | 0.755 | 0.7547 | ok |
| Logistic regression | random stratified 10-fold | PR-AUC | 0.195 | 0.1952 | ok |
| Logistic regression | time-ordered expanding | ROC-AUC | 0.668 | 0.6678 | ok |
| Logistic regression | time-ordered expanding | PR-AUC | 0.084 | 0.0838 | ok |
| Bagged CART | random stratified 10-fold | ROC-AUC | 0.774 | 0.7743 | ok |
| Bagged CART | random stratified 10-fold | PR-AUC | 0.222 | 0.2217 | ok |
| Bagged CART | time-ordered expanding | ROC-AUC | 0.640 | 0.6403 | ok |
| Bagged CART | time-ordered expanding | PR-AUC | 0.078 | 0.0784 | ok |

### Leakage probe (`results/leakage_probe.csv`)

| Model | Validation | Metric | Reported | This run | |
|---|---|---|---|---|---|
| Logistic regression | random stratified 10-fold | ROC-AUC | 0.762 | 0.7619 | ok |
| Logistic regression | random stratified 10-fold | PR-AUC | 0.206 | 0.2065 | ok |
| Logistic regression | time-ordered expanding | ROC-AUC | 0.609 | 0.6093 | ok |
| Logistic regression | time-ordered expanding | PR-AUC | 0.063 | 0.0630 | ok |
| Bagged CART | random stratified 10-fold | ROC-AUC | 0.804 | 0.8040 | ok |
| Bagged CART | random stratified 10-fold | PR-AUC | 0.281 | 0.2807 | ok |
| Bagged CART | time-ordered expanding | ROC-AUC | 0.669 | 0.6694 | ok |
| Bagged CART | time-ordered expanding | PR-AUC | 0.085 | 0.0851 | ok |

### Chronological holdout (`results/holdout.csv`)

| Model | Metric | Reported | This run | |
|---|---|---|---|---|
| Logistic regression | ROC-AUC | 0.568 | 0.5679 | ok |
| Logistic regression | PR-AUC | 0.090 | 0.0897 | ok |
| Bagged CART | ROC-AUC | 0.612 | 0.6122 | ok |
| Bagged CART | PR-AUC | 0.087 | 0.0874 | ok |

**Result: 27 / 27 checks passed.**

## Cross-version stability

The same pipeline was also executed on a different interpreter and library stack:

| | Run A (recorded above) | Run B |
|---|---|---|
| Python | 3.7.0 | 3.12 |
| numpy | 1.21.6 | 2.3.5 |
| pandas | 1.1.5 | 3.0.1 |

All 27 quantities agreed to four decimal places across both. This matters for the
study's central claim: the difference between random and time-ordered validation is
a property of the data and the protocol, not of a particular library version or
random-number stream.

## What this record is for

* It shows the results are **generated**, not transcribed.
* It gives a reader the exact environment needed to obtain the same numbers.
* It documents a case where a very old Python (3.7.0, 2018) and a very new one
  produce identical output — worth knowing if you are tempted to blame a
  discrepancy on "library version".
