"""
Run every experiment in the study and write results/ plus figures/.

Usage:
    python run_experiments.py            # uses data/ (downloads if missing)
    python run_experiments.py --refresh  # forces re-download

Outputs (results/):
    integrity.json          dataset checks
    metrics_by_scheme.csv   model x validation -> metrics
    holdout.csv             single chronological train/test split
    importance.csv          permutation importance
    leakage_probe.csv       chronological index added as a feature
    summary.md              all tables in one place
    figures/*.svg           ROC/PR curves and AUC comparison
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

from data import load, integrity_report, REDUNDANT, CATEGORICAL      # noqa: E402
from metrics import roc_auc, average_precision, summarise             # noqa: E402
from models import (LogisticRegressionIRLS, BaggedForest,             # noqa: E402
                    permutation_importance)
from evaluation import (stratified_random_folds, time_ordered_folds,  # noqa: E402
                        cross_validate, cross_validate_splits,
                        chronological_holdout)

RESULTS = os.path.join(HERE, "results")
FIGURES = os.path.join(RESULTS, "figures")
os.makedirs(FIGURES, exist_ok=True)

MODELS = {
    "logistic regression (L2, class-weighted)": lambda: LogisticRegressionIRLS(lam=1.0),
    "bagged CART (60 trees, depth 6)": lambda: BaggedForest(60, 6, 20, None, seed=7),
}
RANDOM_SEEDS = (0, 1, 2, 3, 4)


# --------------------------------------------------------------------------- #
# tiny SVG helpers (no matplotlib dependency)
# --------------------------------------------------------------------------- #
def _svg_header(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="Helvetica,Arial,sans-serif">'
            f'<rect width="{w}" height="{h}" fill="white"/>')


def svg_curves(paths, out):
    """paths: list of (label, Nx2 array, colour, dashed)."""
    W, H, M = 560, 460, 62
    s = [_svg_header(W, H)]
    s.append(f'<text x="{M}" y="26" font-size="15" font-weight="bold">'
             f'ROC and precision-recall curves (out-of-fold)</text>')
    panel_w, panel_h = 200, 200
    for pi, (title, xlab) in enumerate([("ROC", "false positive rate"),
                                        ("Precision-recall", "recall")]):
        ox, oy = M + pi * (panel_w + 60), 60
        s.append(f'<rect x="{ox}" y="{oy}" width="{panel_w}" height="{panel_h}" '
                 f'fill="none" stroke="#999"/>')
        s.append(f'<text x="{ox}" y="{oy - 8}" font-size="12" font-weight="bold">'
                 f'{title}</text>')
        s.append(f'<text x="{ox + panel_w/2}" y="{oy + panel_h + 30}" font-size="10" '
                 f'text-anchor="middle">{xlab}</text>')
        for i in range(1, 4):
            s.append(f'<line x1="{ox + i*panel_w/4}" y1="{oy}" x2="{ox + i*panel_w/4}" '
                     f'y2="{oy + panel_h}" stroke="#eee"/>')
            s.append(f'<line x1="{ox}" y1="{oy + i*panel_h/4}" x2="{ox + panel_w}" '
                     f'y2="{oy + i*panel_h/4}" stroke="#eee"/>')
        s.append(f'<text x="{ox - 6}" y="{oy + 4}" font-size="9" text-anchor="end">1.0</text>')
        s.append(f'<text x="{ox - 6}" y="{oy + panel_h}" font-size="9" text-anchor="end">0.0</text>')
    for label, arr, colour, dash in paths:
        panel = 0 if arr.shape[1] == 2 and label.endswith("ROC") else 1
        ox, oy = M + panel * (panel_w + 60), 60
        pts = " ".join(f"{ox + x*panel_w:.1f},{oy + panel_h - y*panel_h:.1f}"
                       for x, y in arr)
        d = ' stroke-dasharray="5,4"' if dash else ''
        s.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" '
                 f'stroke-width="1.8"{d}/>')
    # legend
    ly = 320
    for label, _, colour, dash in paths:
        d = ' stroke-dasharray="5,4"' if dash else ''
        s.append(f'<line x1="{M}" y1="{ly}" x2="{M+26}" y2="{ly}" stroke="{colour}" '
                 f'stroke-width="2.4"{d}/>')
        s.append(f'<text x="{M+34}" y="{ly+4}" font-size="11">{label}</text>')
        ly += 20
    s.append('</svg>')
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(s))


def svg_bars(labels, values, out, title, ymax=1.0):
    W, H, M = 620, 380, 200
    n = len(values)
    bh = 26
    s = [_svg_header(W, H)]
    s.append(f'<text x="24" y="28" font-size="15" font-weight="bold">{title}</text>')
    plot_w = W - M - 60
    for i, (lab, v) in enumerate(zip(labels, values)):
        y = 60 + i * (bh + 16)
        w = max(1, v / ymax * plot_w)
        colour = "#c0392b" if i % 2 else "#2c6fbb"
        s.append(f'<rect x="{M}" y="{y}" width="{w:.1f}" height="{bh}" fill="{colour}"/>')
        s.append(f'<text x="{M-8}" y="{y+bh*0.7:.0f}" font-size="11" '
                 f'text-anchor="end">{lab}</text>')
        s.append(f'<text x="{M+w+6:.0f}" y="{y+bh*0.7:.0f}" font-size="11">{v:.3f}</text>')
    s.append('</svg>')
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(s))


# --------------------------------------------------------------------------- #
def main(refresh: bool = False):
    X, y, features, df = load(refresh)
    rep = integrity_report(df)
    with open(os.path.join(RESULTS, "integrity.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)

    print("=" * 104)
    print("1. DATASET INTEGRITY")
    print("=" * 104)
    print(f"  records              : {rep['n_rows']}")
    print(f"  features used        : {len(features)}  (dropped as redundant: {REDUNDANT})")
    print(f"  positive (class 1)   : {rep['n_positive']}   prevalence {rep['prevalence']:.4f}")
    print(f"  duplicate rows       : {rep['duplicate_rows']}")
    print(f"  constant columns     : {rep['constant_columns']}  <- zero information")
    print(f"  rank(nbumps2..89)    : {rep['nbumps_range_rank']} of "
          f"{rep['nbumps_range_ncols']}  <- exact linear dependencies")
    print(f"  prevalence by quintile of record order: {rep['prevalence_by_quintile']}")

    # ---------------- null model ----------------
    print("\n" + "=" * 104)
    print("2. WHY ACCURACY IS THE WRONG METRIC HERE")
    print("=" * 104)
    null_acc = 1.0 - y.mean()
    print(f"  accuracy of 'always predict 0' : {null_acc:.4f}")
    print("  any model must beat this before its accuracy means anything.")

    # ---------------- main experiment ----------------
    print("\n" + "=" * 104)
    print("3. MODEL x VALIDATION SCHEME")
    print("=" * 104)
    rows, oof_store = [], {}
    for mname, mfac in MODELS.items():
        # random CV averaged over seeds (report mean and spread)
        aucs, prs, pooled = [], [], None
        for sd in RANDOM_SEEDS:
            fold = stratified_random_folds(y, k=10, seed=sd)
            p = cross_validate(mfac, X, y, fold)
            m = ~np.isnan(p)
            aucs.append(roc_auc(y[m], p[m]))
            prs.append(average_precision(y[m], p[m]))
            if sd == RANDOM_SEEDS[0]:
                pooled = p
        oof_store[(mname, "random")] = pooled
        s = summarise(y[~np.isnan(pooled)], pooled[~np.isnan(pooled)])
        rows.append(dict(model=mname, validation="random stratified 10-fold",
                         roc_auc=float(np.mean(aucs)), roc_auc_sd=float(np.std(aucs)),
                         pr_auc=float(np.mean(prs)), pr_auc_sd=float(np.std(prs)),
                         accuracy=s["accuracy"], balanced_accuracy=s["balanced_accuracy"],
                         recall=s["recall"], precision=s["precision"], f1=s["f1"]))
        # time-ordered (deterministic -> no seed spread)
        p = cross_validate_splits(mfac, X, y, time_ordered_folds(len(y), k=5))
        oof_store[(mname, "time")] = p
        m = ~np.isnan(p)
        s = summarise(y[m], p[m])
        rows.append(dict(model=mname, validation="time-ordered expanding window",
                         roc_auc=roc_auc(y[m], p[m]), roc_auc_sd=0.0,
                         pr_auc=average_precision(y[m], p[m]), pr_auc_sd=0.0,
                         accuracy=s["accuracy"], balanced_accuracy=s["balanced_accuracy"],
                         recall=s["recall"], precision=s["precision"], f1=s["f1"]))
    met = pd.DataFrame(rows)
    met.to_csv(os.path.join(RESULTS, "metrics_by_scheme.csv"), index=False)
    print(met.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    # ---------------- leakage probe ----------------
    print("\n" + "=" * 104)
    print("4. LEAKAGE PROBE: add the record index (a pure time proxy) as a feature")
    print("=" * 104)
    Xidx = np.hstack([X, (np.arange(len(y)) / len(y)).reshape(-1, 1)])
    probe = []
    for mname, mfac in MODELS.items():
        for vname, get in [("random stratified 10-fold",
                            lambda: cross_validate(mfac, Xidx, y,
                                                   stratified_random_folds(y, 10, 0))),
                           ("time-ordered expanding window",
                            lambda: cross_validate_splits(mfac, Xidx, y,
                                                          time_ordered_folds(len(y), 5)))]:
            p = get()
            m = ~np.isnan(p)
            probe.append(dict(model=mname, validation=vname,
                              roc_auc=roc_auc(y[m], p[m]),
                              pr_auc=average_precision(y[m], p[m])))
    probe_df = pd.DataFrame(probe)
    probe_df.to_csv(os.path.join(RESULTS, "leakage_probe.csv"), index=False)
    print(probe_df.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(f"\n  univariate signal of the record index alone: "
          f"ROC-AUC = {roc_auc(y, -np.arange(len(y), dtype=float)):.3f} "
          f"(using -index, since risk falls over the record)")
    print("  -> the record position alone is as discriminative as the full "
          "17-feature model under honest temporal validation.")

    # ---------------- chronological holdout ----------------
    print("\n" + "=" * 104)
    print("5. CHRONOLOGICAL HOLDOUT (train on first 70 %, test on last 30 %)")
    print("=" * 104)
    hold = []
    (Xtr, ytr), (Xte, yte) = chronological_holdout(X, y, 0.7)
    for mname, mfac in MODELS.items():
        mdl = mfac().fit(Xtr, ytr)
        s = summarise(yte, mdl.predict_proba(Xte))
        hold.append(dict(model=mname, n_test=s["n"], roc_auc=s["roc_auc"],
                         pr_auc=s["pr_auc"], accuracy=s["accuracy"],
                         balanced_accuracy=s["balanced_accuracy"],
                         recall=s["recall"], precision=s["precision"]))
    hold_df = pd.DataFrame(hold)
    hold_df.to_csv(os.path.join(RESULTS, "holdout.csv"), index=False)
    print(hold_df.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    # ---------------- importance ----------------
    print("\n" + "=" * 104)
    print("6. PERMUTATION IMPORTANCE (drop in ROC-AUC when a column is shuffled)")
    print("=" * 104)
    mdl = BaggedForest(60, 6, 20, None, seed=7).fit(X, y)
    base, mean, sd = permutation_importance(mdl, X, y, roc_auc, n_repeats=5, seed=0)
    imp = (pd.DataFrame({"feature": features, "auc_drop": mean, "sd": sd})
           .sort_values("auc_drop", ascending=False))
    imp.to_csv(os.path.join(RESULTS, "importance.csv"), index=False)
    print(f"  in-sample ROC-AUC of the fitted forest: {base:.3f}")
    print(imp.head(10).to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    # ---------------- figures ----------------
    print("\n" + "=" * 104)
    print("7. FIGURES")
    print("=" * 104)
    from metrics import curve_points
    from figures import save_curves_png, save_bars_png

    families = [("logistic regression (L2, class-weighted)", "LR"),
                ("bagged CART (60 trees, depth 6)", "CART")]
    combined, roc_curves, pr_curves = [], [], []
    for ci, (mname, short) in enumerate(families):
        for scheme, dashed in [("random", False), ("time", True)]:
            p = oof_store[(mname, scheme)]
            m = ~np.isnan(p)
            roc, pr = curve_points(y[m], p[m], 160)
            tag = "random CV" if scheme == "random" else "time-ordered"
            combined.append((f"{short} {tag} ROC", roc, ci, dashed))
            combined.append((f"{short} {tag} PR", pr, ci, dashed))
            roc_curves.append((f"{short}, {tag}", roc, ci, dashed))
            pr_curves.append((f"{short}, {tag}", pr, ci, dashed))

    # SVG for the web / README
    svg_curves(combined, os.path.join(FIGURES, "roc_pr.svg"))
    labels, vals = [], []
    for _, r in met.iterrows():
        labels.append(("LR" if "logistic" in r["model"] else "CART") +
                      (" random CV" if "random" in r["validation"] else " time-ordered"))
        vals.append(r["pr_auc"])
    svg_bars(labels, vals, os.path.join(FIGURES, "pr_auc_by_scheme.svg"),
             "PR-AUC by model and validation scheme")

    # PNG for embedding in the report
    save_curves_png(os.path.join(FIGURES, "roc_curves.png"), roc_curves,
                    "ROC curves (out-of-fold predictions)",
                    "false positive rate", "true positive rate", diagonal=True)
    save_curves_png(os.path.join(FIGURES, "pr_curves.png"), pr_curves,
                    "Precision-recall curves (out-of-fold predictions)",
                    "recall", "precision")
    save_bars_png(os.path.join(FIGURES, "pr_auc_by_scheme.png"),
                  labels, vals, "PR-AUC by model and validation scheme")
    q_order = sorted(rep["prevalence_by_quintile"].keys())
    q_labels = ["block %d" % (int(k) + 1) for k in q_order]
    q_vals = [rep["prevalence_by_quintile"][k] for k in q_order]
    save_bars_png(os.path.join(FIGURES, "prevalence_drift.png"), q_labels, q_vals,
                  "Hazard prevalence across the record sequence (5 equal blocks)",
                  ymax=0.18, fmt="%.4f", highlight=0)

    print("  wrote figures/roc_pr.svg, figures/pr_auc_by_scheme.svg (web)")
    print("  wrote figures/roc_curves.png, figures/pr_curves.png, "
          "figures/pr_auc_by_scheme.png, figures/prevalence_drift.png (report)")

    # ---------------- summary.md ----------------
    def md(dframe):
        cols = list(dframe.columns)
        out = ["| " + " | ".join(cols) + " |",
               "|" + "|".join(["---"] * len(cols)) + "|"]
        for _, r in dframe.iterrows():
            out.append("| " + " | ".join(
                f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c]) for c in cols) + " |")
        return "\n".join(out)

    with open(os.path.join(RESULTS, "summary.md"), "w", encoding="utf-8") as f:
        f.write("# Results summary\n\nGenerated by `run_experiments.py`.\n\n")
        f.write("## 1. Dataset integrity\n\n```json\n")
        f.write(json.dumps(rep, indent=2, ensure_ascii=False))
        f.write("\n```\n\n")
        f.write(f"Accuracy of the trivial 'always predict 0' model: **{null_acc:.4f}**\n\n")
        f.write("## 2. Model x validation scheme\n\n" + md(met) + "\n\n")
        f.write("## 3. Leakage probe (record index added as a feature)\n\n"
                + md(probe_df) + "\n\n")
        f.write("## 4. Chronological holdout (70 / 30)\n\n" + md(hold_df) + "\n\n")
        f.write("## 5. Permutation importance (bagged CART, in-sample)\n\n"
                + md(imp.head(12)) + "\n")
    print("  wrote results/summary.md")
    print("\ndone.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true",
                    help="re-download the dataset")
    main(**vars(ap.parse_args()))
