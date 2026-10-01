# Seismic-bump forecasting: does random cross-validation overstate model skill?

A small, fully reproducible study on the [UCI Seismic Bumps dataset](https://archive.ics.uci.edu/ml/datasets/seismic-bumps) —
2,578 shift records from a Polish coal mine, where the task is to predict whether a
hazardous seismic event (energy > 10⁴ J) will occur during the **next** shift.

**Headline result.** The same model scores ROC-AUC 0.755 under the stratified 10-fold
cross-validation usually applied to this dataset, but only 0.668 under time-ordered
validation — and its PR-AUC falls from 0.195 to 0.084, a 57 % relative loss. On a
genuine chronological holdout the model is barely better than chance (ROC-AUC 0.57).
Adding the record index as a feature — pure noise, physically — *improves* the random-CV
score and *degrades* the honest one, which is the signature of temporal leakage.

**Probability calibration.** Class weights are what make these models usable at 6.6 %
positives, but they push the output probabilities onto the wrong scale. The logistic
regression's mean predicted probability is **0.333** against an observed rate of **0.0427**
— it over-states risk by roughly eight times. A single log-odds prior correction reduces the
expected calibration error from **0.290** to **0.014**. The same correction *over-corrects*
the bagged tree ensemble, which is already close to calibrated (mean predicted 0.066).
Ranking metrics such as ROC-AUC and PR-AUC are blind to all of this.

## Why this matters

Seismic-bump forecasting is early warning for a rare, dangerous event. On this dataset
6.59 % of shifts are hazardous, so a model that always predicts "no hazard" already
achieves 93.4 % accuracy. Reported performance therefore depends almost entirely on the
validation protocol, not on the model.

## Repository layout

```
seismic-bump-forecasting/
├── run_experiments.py      # runs everything, writes results/
├── requirements.txt        # numpy + pandas only
├── src/
│   ├── data.py             # loading, encoding, integrity checks
│   ├── metrics.py          # ROC-AUC, PR-AUC, confusion, curves
│   ├── models.py           # logistic regression (IRLS), CART, bagging, permutation importance
│   ├── calibration.py      # reliability curves, Brier score, ECE, prior correction
│   ├── figures.py          # Pillow-based figure rendering (no matplotlib)
│   └── evaluation.py       # stratified random CV, time-ordered CV, chronological holdout
├── data/                   # downloaded on first run (not committed)
├── report/technical_note.md
└── results/                # generated: metrics, figures, summary
```

## Quick start

```bash
git clone <this repo>
cd seismic-bump-forecasting

python -m venv .venv                  # isolated environment, inside the project
# Windows:
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run_experiments.py
# macOS / Linux:
# .venv/bin/python -m pip install -r requirements.txt
# .venv/bin/python run_experiments.py
```

Runtime under five minutes on a laptop CPU. No GPU. Outputs land in `results/`.
The dataset is downloaded automatically on first run into `data/` (~125 KB), which
is why `data/` is not committed.

**Then check the results against the numbers published in the report:**

```bash
python verify_results.py
```

This re-derives the dataset facts from the raw CSV and compares all 33 quantities
against `report/technical_note.md`. It exits 0 only if everything matches. It is not
a rubber stamp: changing a single label in the CSV makes it fail.

Optional — record the exact environment into `results/environment.txt`:

```bash
python record_environment.py
```

### Notes for old Python versions

Verified on Python 3.7.0, where `pip` will otherwise try to compile numpy and pandas
from source. Pin to pre-built wheels instead:

```bash
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install --only-binary=:all: numpy==1.21.6 pandas==1.1.5
```

## Reproducibility

`results/REPRODUCTION.md` records a full execution and checks **all 27 reported
quantities** against the generated output files — all pass within 0.005.

The same pipeline was run on two very different stacks:

| | Python | numpy | pandas |
|---|---|---|---|
| Run A | 3.7.0 | 1.21.6 | 1.1.5 |
| Run B | 3.12 | 2.3.5 | 3.0.1 |

Both produced identical values to four decimal places. The gap between random and
time-ordered validation is therefore a property of the data and the protocol, not of
a library version or a random-number stream. The raw console output is committed as
`results/run_log.txt`.

## Design decisions

* **Everything is implemented in NumPy.** No scikit-learn. Each metric and each model is
  written out so that any number in the report can be traced to a formula.
* **Two model families.** A linear model and a bagged tree ensemble, so that the
  conclusion cannot be dismissed as an artefact of one model class. The effect is
  larger for the non-linear model.
* **Scaling inside the fold.** Standardisation is fitted on training data only. Scaling
  before cross-validation is a second, subtler leak.
* **Metrics chosen for imbalance.** ROC-AUC, PR-AUC and balanced accuracy, plus
  recall/precision at the base-rate threshold. Accuracy is reported only to show how
  misleading it is.
* **No hyper-parameter tuning.** Tuning is skipped so that the comparison between
  validation schemes is not confounded by model selection.

## Key numbers

| model | validation | ROC-AUC | PR-AUC |
|---|---|---|---|
| Logistic regression | random stratified 10-fold | 0.755 | 0.195 |
| Logistic regression | time-ordered expanding | 0.668 | 0.084 |
| Bagged CART | random stratified 10-fold | 0.774 | 0.222 |
| Bagged CART | time-ordered expanding | 0.640 | 0.078 |

Chronological holdout (first 70 % → last 30 %, n = 774): ROC-AUC 0.568 (LR) / 0.612 (CART).

Record index alone as a score: **ROC-AUC 0.670** — as discriminative as the full
17-feature model under honest temporal validation, because prevalence drifts from
16.1 % to 2.1 % across the record.

Data integrity: `nbumps6`, `nbumps7` and `nbumps89` are constant; `nbumps2…nbumps89`
have rank 4 of 7. These three exact dependencies explain the
"(3 not defined because of singularities)" warning produced by a full logistic
regression on all 18 original features.

## Limitations

* No explicit timestamp: row order is taken as chronological, following the source
  documentation. If rows are instead grouped by longwall, the same independence
  argument applies with "group" substituted for "time" — the conclusion is unchanged,
  though the magnitude may differ.
* The two longwalls cannot be separated (no wall identifier).
* Published baselines report accuracy and balanced accuracy only, so comparison is
  qualitative.

## References

* Sikora & Wrobel (2010), *Archives of Mining Sciences* 55(1), 91–114 — source dataset.
* Bergmeir & Benítez (2012), *Information Sciences* 191, 192–213 — cross-validation for
  time-series predictor evaluation.
* Roberts et al. (2017), *Ecography* 40, 913–929 — cross-validation for temporally and
  spatially structured data.

See `report/technical_note.md` for the full write-up.

## License

MIT — see `LICENSE`.
