"""
verify_results.py — check this repository against its own published numbers.

Two independent kinds of check:

  A. Re-derive the dataset facts directly from data/seismic-bumps.csv, without
     trusting results/integrity.json. If the CSV changed, this fails.

  B. Compare every metric in results/*.csv against the values quoted in
     report/technical_note.md, within a tolerance.

Usage:
    python run_experiments.py     # produce results/
    python verify_results.py      # check them

Exit code 0 = everything matches. Exit code 1 = something does not.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
CSV = os.path.join(HERE, "data", "seismic-bumps.csv")

TOL = 0.005

# ---------------------------------------------------------------------------
# The numbers as published in report/technical_note.md
# ---------------------------------------------------------------------------
EXPECTED_DATA = {
    "records": 2578,
    "positives": 170,
    "prevalence": 0.0659,
    "constant_columns": ["nbumps6", "nbumps7", "nbumps89"],
    "bump_range_rank": 4,
    "quintile_prevalence": [0.1609, 0.0680, 0.0213, 0.0447, 0.0349],
    "trivial_accuracy": 0.9341,
}

EXPECTED_METRICS = {
    ("logistic", "random"): {"roc_auc": 0.755, "pr_auc": 0.195},
    ("logistic", "time"):   {"roc_auc": 0.668, "pr_auc": 0.084},
    ("cart", "random"):     {"roc_auc": 0.774, "pr_auc": 0.222},
    ("cart", "time"):       {"roc_auc": 0.640, "pr_auc": 0.078},
}

EXPECTED_PROBE = {
    ("logistic", "random"): {"roc_auc": 0.762, "pr_auc": 0.206},
    ("logistic", "time"):   {"roc_auc": 0.609, "pr_auc": 0.063},
    ("cart", "random"):     {"roc_auc": 0.804, "pr_auc": 0.281},
    ("cart", "time"):       {"roc_auc": 0.669, "pr_auc": 0.085},
}

EXPECTED_HOLDOUT = {
    "logistic": {"roc_auc": 0.568, "pr_auc": 0.090},
    "cart":     {"roc_auc": 0.612, "pr_auc": 0.087},
}

# ---------------------------------------------------------------------------
_failures = []
_n_pass = 0


def check(label, got, want, tol=TOL):
    global _n_pass
    try:
        ok = abs(float(got) - float(want)) <= tol
    except (TypeError, ValueError):
        ok = False
    if ok:
        _n_pass += 1
        print("  [ok]   %-46s %10.4f   expected %.4f" % (label, float(got), float(want)))
    else:
        _failures.append(label)
        print("  [FAIL] %-46s %10s   expected %.4f"
              % (label, got, float(want)))


def check_equal(label, got, want):
    global _n_pass
    if got == want:
        _n_pass += 1
        print("  [ok]   %-46s %s" % (label, got))
    else:
        _failures.append(label)
        print("  [FAIL] %-46s %s   expected %s" % (label, got, want))


def key_of(model_name, validation):
    m = "logistic" if "logistic" in model_name else "cart"
    v = "random" if "random" in validation else "time"
    return m, v


# ---------------------------------------------------------------------------
def part_a_data():
    print("\nA. Re-deriving dataset facts from the raw CSV")
    print("   (independent of results/integrity.json)")
    print("-" * 78)
    if not os.path.exists(CSV):
        _failures.append("data/seismic-bumps.csv missing")
        print("  [FAIL] data/seismic-bumps.csv not found — run run_experiments.py first")
        return
    df = pd.read_csv(CSV)

    check("records", len(df), EXPECTED_DATA["records"], 0)
    check("positives (class 1)", int((df["class"] == 1).sum()),
          EXPECTED_DATA["positives"], 0)
    check("prevalence", float((df["class"] == 1).mean()),
          EXPECTED_DATA["prevalence"])
    check("trivial 'always 0' accuracy", 1.0 - float(df["class"].mean()),
          EXPECTED_DATA["trivial_accuracy"])

    constant = sorted(c for c in df.columns if df[c].nunique() <= 1)
    check_equal("constant columns", constant, EXPECTED_DATA["constant_columns"])

    bump_cols = [c for c in df.columns if c.startswith("nbumps") and c != "nbumps"]
    check_equal("rank(nbumps2..nbumps89)",
                int(np.linalg.matrix_rank(df[bump_cols].to_numpy(float))),
                EXPECTED_DATA["bump_range_rank"])

    q = pd.qcut(np.arange(len(df)), 5, labels=False)
    prev = df.groupby(q)["class"].mean().to_list()
    for i, (got, want) in enumerate(zip(prev, EXPECTED_DATA["quintile_prevalence"])):
        check("prevalence, quintile %d of record order" % i, got, want)


def _read(name):
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path):
        _failures.append("%s missing" % name)
        print("  [FAIL] %s not found — run run_experiments.py first" % name)
        return None
    return pd.read_csv(path)


def part_b_metrics():
    print("\nB. Comparing generated metrics against the published values")
    print("-" * 78)

    print("  model x validation scheme  (results/metrics_by_scheme.csv)")
    m = _read("metrics_by_scheme.csv")
    if m is not None:
        for _, r in m.iterrows():
            exp = EXPECTED_METRICS[key_of(r["model"], r["validation"])]
            tag = "%s / %s" % (key_of(r["model"], r["validation"])[0],
                               key_of(r["model"], r["validation"])[1])
            check("%s  ROC-AUC" % tag, r["roc_auc"], exp["roc_auc"])
            check("%s  PR-AUC" % tag, r["pr_auc"], exp["pr_auc"])

    print("\n  leakage probe  (results/leakage_probe.csv)")
    p = _read("leakage_probe.csv")
    if p is not None:
        for _, r in p.iterrows():
            exp = EXPECTED_PROBE[key_of(r["model"], r["validation"])]
            tag = "probe %s / %s" % key_of(r["model"], r["validation"])
            check("%s  ROC-AUC" % tag, r["roc_auc"], exp["roc_auc"])
            check("%s  PR-AUC" % tag, r["pr_auc"], exp["pr_auc"])

    print("\n  chronological holdout  (results/holdout.csv)")
    h = _read("holdout.csv")
    if h is not None:
        for _, r in h.iterrows():
            exp = EXPECTED_HOLDOUT["logistic" if "logistic" in r["model"] else "cart"]
            tag = "holdout %s" % ("logistic" if "logistic" in r["model"] else "cart")
            check("%s  ROC-AUC" % tag, r["roc_auc"], exp["roc_auc"])
            check("%s  PR-AUC" % tag, r["pr_auc"], exp["pr_auc"])


def part_c_claim():
    """The one claim the whole study rests on: honest validation scores lower."""
    print("\nC. The central claim: time-ordered validation scores lower than random")
    print("-" * 78)
    m = _read("metrics_by_scheme.csv")
    if m is None:
        return
    for fam in ("logistic", "cart"):
        sub = m[m["model"].str.contains(fam, case=False)]
        rnd = sub[sub["validation"].str.contains("random", case=False)]
        tim = sub[sub["validation"].str.contains("time", case=False)]
        if rnd.empty or tim.empty:
            _failures.append("missing rows for %s" % fam)
            continue
        drop = float(rnd["pr_auc"].iloc[0]) - float(tim["pr_auc"].iloc[0])
        ok = drop > 0.05
        if ok:
            globals()["_n_pass"] += 1
        else:
            _failures.append("%s: gap too small" % fam)
        print("  [%s] %-30s PR-AUC gap = %.3f  (random %.3f -> time-ordered %.3f)"
              % ("ok" if ok else "FAIL", fam, drop,
                 float(rnd["pr_auc"].iloc[0]), float(tim["pr_auc"].iloc[0])))


def main():
    print("=" * 78)
    print("VERIFYING THIS REPOSITORY AGAINST ITS PUBLISHED NUMBERS")
    print("tolerance = %.3f" % TOL)
    print("=" * 78)
    part_a_data()
    part_b_metrics()
    part_c_claim()
    print("\n" + "=" * 78)
    if _failures:
        print("RESULT: %d passed, %d FAILED" % (_n_pass, len(_failures)))
        for f in _failures:
            print("   - %s" % f)
        print("\nDo NOT report numbers that fail this check.")
        return 1
    print("RESULT: all %d checks passed — the repository is self-consistent." % _n_pass)
    return 0


if __name__ == "__main__":
    sys.exit(main())
