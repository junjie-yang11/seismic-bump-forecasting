"""
Run every experiment in the study and write results/phase1/ plus figures/.

Usage:
    python -m phase1.run_experiments            # uses data/ (downloads if missing)
    python -m phase1.run_experiments --refresh  # forces re-download

Outputs (results/phase1/):
    integrity.json          dataset checks
    metrics_by_scheme.csv   model x validation -> metrics
    holdout.csv             single chronological train/test split
    importance.csv          permutation importance
    leakage_probe.csv       chronological index added as a feature
    summary.md              all tables in one place
    figures/*.png           ROC/PR curves and AUC comparison
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "src"))

from data import load, integrity_report, REDUNDANT
from metrics import roc_auc, average_precision, summarise             # noqa: E402
from models import (LogisticRegressionIRLS, BaggedForest,             # noqa: E402
                    permutation_importance)
from evaluation import (stratified_random_folds, time_ordered_folds,  # noqa: E402
                        cross_validate, cross_validate_splits,
                        chronological_holdout, select_training_threshold)

RESULTS = os.path.join(HERE, "results/phase1")
FIGURES = os.path.join(RESULTS, "figures")
os.makedirs(FIGURES, exist_ok=True)

MODELS = {
    "logistic regression (L2, class-weighted)": lambda: LogisticRegressionIRLS(lam=1.0),
    "bagged CART (60 trees, depth 6)": lambda: BaggedForest(60, 6, 20, None, seed=7),
}
RANDOM_SEEDS = (0, 1, 2, 3, 4)


def main(refresh: bool = False):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)
    X, y, features, df = load(refresh)
    rep = integrity_report(df)
    with open(os.path.join(RESULTS, "integrity.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)

    print("=" * 104)
    print("1. DATASET INTEGRITY")
    print("=" * 104)
    print(f"  records              : {rep['n_rows']}")
    print(f"  features used        : {len(features)}  (excluded from the design: {REDUNDANT})")
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
    print("  high accuracy alone does not demonstrate hazard detection; inspect ranking and warning metrics.")

    # ---------------- main experiment ----------------
    print("\n" + "=" * 104)
    print("3. MODEL x VALIDATION SCHEME")
    print("=" * 104)
    rows, oof_store, detail_store = [], {}, {}
    seed_rows, shared_rows, fold_rows, prediction_rows = [], [], [], []
    random_prediction_rows = []

    def record_details(model, scheme, details):
        for record in details['records']:
            fold_rows.append(dict(model=model, validation=scheme, **record))
        mask = details['fold'] >= 0
        prediction_rows.append(pd.DataFrame(dict(model=model, validation=scheme,
            row=np.flatnonzero(mask), y=y[mask], score=details['score'][mask],
            calibrated=details['calibrated'][mask], threshold=details['threshold'][mask],
            training_prior=details['training_prior'][mask], fold=details['fold'][mask])))

    for mname, mfac in MODELS.items():
        # random CV averaged over seeds (report mean and spread)
        random_details, random_summaries = [], []
        for sd in RANDOM_SEEDS:
            print('  fitting %s: random CV seed %d' % (mname, sd), flush=True)
            fold = stratified_random_folds(y, k=10, seed=sd)
            details = cross_validate(mfac, X, y, fold, return_details=True)
            p = details['score']
            m = ~np.isnan(p)
            s = summarise(y[m], p[m], threshold=details['threshold'][m])
            random_details.append(details)
            random_prediction_rows.append(pd.DataFrame(dict(model=mname,seed=sd,
                row=np.arange(len(y)),y=y,score=p)))
            random_summaries.append(s)
            seed_rows.append(dict(model=mname, seed=sd, **s))
        pooled = random_details[0]['score']
        oof_store[(mname, "random")] = pooled
        detail_store[(mname, 'random')] = random_details[0]
        record_details(mname, 'random', random_details[0])
        s = {key: float(np.mean([r[key] for r in random_summaries]))
             for key in ('accuracy', 'balanced_accuracy', 'recall', 'precision', 'f1', 'alert_rate')}
        rows.append(dict(model=mname, validation="random stratified 10-fold",
                         roc_auc=float(np.mean([r['roc_auc'] for r in random_summaries])),
                         roc_auc_sd=float(np.std([r['roc_auc'] for r in random_summaries])),
                         pr_auc=float(np.mean([r['pr_auc'] for r in random_summaries])),
                         pr_auc_sd=float(np.std([r['pr_auc'] for r in random_summaries])),
                         accuracy=s["accuracy"], balanced_accuracy=s["balanced_accuracy"],
                         recall=s["recall"], precision=s["precision"], f1=s["f1"],
                         alert_rate=s['alert_rate']))
        # time-ordered (deterministic -> no seed spread)
        details = cross_validate_splits(mfac, X, y, time_ordered_folds(len(y), k=5), return_details=True)
        p = details['score']
        detail_store[(mname, 'time')] = details
        record_details(mname, 'time', details)
        oof_store[(mname, "time")] = p
        m = ~np.isnan(p)
        s = summarise(y[m], p[m], threshold=details['threshold'][m])
        rows.append(dict(model=mname, validation="time-ordered expanding window",
                         roc_auc=roc_auc(y[m], p[m]), roc_auc_sd=0.0,
                         pr_auc=average_precision(y[m], p[m]), pr_auc_sd=0.0,
                         accuracy=s["accuracy"], balanced_accuracy=s["balanced_accuracy"],
                         recall=s["recall"], precision=s["precision"], f1=s["f1"],
                         alert_rate=s['alert_rate']))
        for sd, rnd in zip(RANDOM_SEEDS, random_details):
            common = m & np.isfinite(rnd['score'])
            shared_rows.append(dict(model=mname, seed=sd, n=int(common.sum()),
                prevalence=float(y[common].mean()),
                random_roc_auc=roc_auc(y[common], rnd['score'][common]),
                random_pr_auc=average_precision(y[common], rnd['score'][common]),
                time_roc_auc=roc_auc(y[common], p[common]),
                time_pr_auc=average_precision(y[common], p[common])))
    met = pd.DataFrame(rows)
    met.to_csv(os.path.join(RESULTS, "metrics_by_scheme.csv"), index=False)
    pd.DataFrame(seed_rows).to_csv(os.path.join(RESULTS, 'random_metrics_by_seed.csv'), index=False)
    pd.concat(random_prediction_rows,ignore_index=True).to_csv(
        os.path.join(RESULTS,'random_predictions_by_seed.csv'),index=False)
    shared = pd.DataFrame(shared_rows)
    shared.to_csv(os.path.join(RESULTS, 'shared_test_by_seed.csv'), index=False)
    shared_mean = shared.drop(columns='seed').groupby('model', sort=False).mean().reset_index()
    shared_mean.to_csv(os.path.join(RESULTS, 'shared_test_comparison.csv'), index=False)
    print(met.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    # ---------------- leakage probe ----------------
    print("\n" + "=" * 104)
    print("4. DESCRIPTIVE INDEX PROBE: add record position as a feature")
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
    print("  This full-cohort index association is descriptive; it does not "
          "confirm calendar time or isolate leakage.")

    # ---------------- chronological holdout ----------------
    print("\n" + "=" * 104)
    print("5. CHRONOLOGICAL HOLDOUT (train on first 70 %, test on last 30 %)")
    print("=" * 104)
    hold = []
    (Xtr, ytr), (Xte, yte) = chronological_holdout(X, y, 0.7)
    for mname, mfac in MODELS.items():
        mdl = mfac().fit(Xtr, ytr)
        threshold, threshold_info = select_training_threshold(mfac, Xtr, ytr, temporal=True)
        scores = mdl.predict_proba(Xte)
        s = summarise(yte, scores, threshold=threshold)
        weighted = bool(getattr(mdl, 'class_weight', False))
        from calibration import prior_correction
        pc = prior_correction(scores, float(ytr.mean()), .5) if weighted else scores
        cut = len(ytr)
        hold_details = dict(score=np.r_[np.full(cut, np.nan), scores],
            calibrated=np.r_[np.full(cut, np.nan), pc],
            threshold=np.r_[np.full(cut, np.nan), np.full(len(yte), threshold)],
            training_prior=np.r_[np.full(cut, np.nan), np.full(len(yte), ytr.mean())],
            fold=np.r_[np.full(cut, -1), np.zeros(len(yte), dtype=int)],
            records=[dict(fold=0, n_train=cut, n_test=len(yte), train_end=cut-1,
                test_start=cut, test_end=len(y)-1, training_prior=float(ytr.mean()),
                threshold=threshold, class_weighted=weighted, **threshold_info)])
        record_details(mname, 'holdout', hold_details)
        hold.append(dict(model=mname, n_test=s["n"], roc_auc=s["roc_auc"],
                         pr_auc=s["pr_auc"], accuracy=s["accuracy"],
                         balanced_accuracy=s["balanced_accuracy"],
                         recall=s["recall"], precision=s["precision"], f1=s['f1'],
                         alert_rate=s['alert_rate'], threshold=threshold))
    hold_df = pd.DataFrame(hold)
    hold_df.to_csv(os.path.join(RESULTS, "holdout.csv"), index=False)
    pd.DataFrame(fold_rows).to_csv(os.path.join(RESULTS, 'fold_audit.csv'), index=False)
    pd.concat(prediction_rows, ignore_index=True).to_csv(os.path.join(RESULTS, 'predictions.csv'), index=False)
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

    # ---------------- calibration ----------------
    print("\n" + "=" * 104)
    print("7. PROBABILITY CALIBRATION")
    print("=" * 104)
    from calibration import (prior_correction, calibration_summary,
                             reliability_curve)
    cal_rows, cal_panels = [], []
    families = [("logistic regression (L2, class-weighted)", "LR", True),
                ("bagged CART (60 trees, depth 6)", "CART", False)]
    print("  The logistic model uses balanced class weights, so its output")
    print("  probabilities need a prior correction estimated from historical data.")
    print("  CART is unweighted and is reported as fitted.")
    for ci, (mname, short, weighted) in enumerate(families):
        p = oof_store[(mname, "time")]          # the honest scheme
        m = ~np.isnan(p)
        yt, pt = y[m], p[m]
        variants = [("as fitted (class-weighted)", pt),
                    ("after fold-local prior correction", detail_store[(mname, 'time')]['calibrated'][m])] \
            if weighted else [("as fitted (unweighted CART)", pt)]
        for tag, pp in variants:
            s = calibration_summary(yt, pp, short)
            s.update(model=short, variant=tag)
            cal_rows.append(s)
        for tag, pp in variants:
            rc = reliability_curve(yt, pp, n_bins=10)
            cal_panels.append(("%s \u2014 %s" % (short, tag),
                               rc["mean_pred"], rc["obs_freq"], rc["count"]))
    cal = pd.DataFrame(cal_rows)[["model", "variant", "brier", "brier_skill",
                                  "ece", "mce", "mean_predicted", "observed_rate"]]
    cal.to_csv(os.path.join(RESULTS, "calibration.csv"), index=False)
    print("  Calibration priors come exclusively from each fold's training labels.")
    print(cal.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    # ---------------- figures ----------------
    print("\n" + "=" * 104)
    print("8. FIGURES")
    print("=" * 104)
    from metrics import curve_points
    from figures import save_curves_png, save_bars_png, save_reliability_png

    roc_curves, pr_curves = [], []
    for ci, (mname, short, _) in enumerate(families):
        for scheme, dashed in [("random", False), ("time", True)]:
            p = oof_store[(mname, scheme)]
            m = ~np.isnan(p)
            roc, pr = curve_points(y[m], p[m], 160)
            tag = "random CV" if scheme == "random" else "time-ordered"
            roc_curves.append((f"{short}, {tag}", roc, ci, dashed))
            pr_curves.append((f"{short}, {tag}", pr, ci, dashed))

    labels, vals = [], []
    for _, r in met.iterrows():
        labels.append(("LR" if "logistic" in r["model"] else "CART") +
                      (" random CV" if "random" in r["validation"] else " time-ordered"))
        vals.append(r["pr_auc"])

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
    save_reliability_png(os.path.join(FIGURES, "reliability.png"), cal_panels,
                         "Probability calibration, before and after prior correction")
    # the logistic-regression pair carries the story most clearly in print
    save_reliability_png(os.path.join(FIGURES, "reliability_lr.png"),
                         cal_panels[:2],
                         "Logistic regression: probability calibration")

    print("  wrote figures/roc_curves.png, figures/pr_curves.png, "
          "figures/pr_auc_by_scheme.png, figures/prevalence_drift.png, "
          "figures/reliability.png (report)")

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
        f.write("All random-CV metrics are means across five seeds. Thresholds are selected "
                "on inner training validation, then fixed for each outer test fold. Boundary "
                "ties are excluded; future alert rates can differ from the training budget.\n\n")
        f.write("## Same test sample comparison\n\n" + md(shared_mean) + "\n\n")
        f.write("This comparison uses the same test rows but does not control training size "
                "or training periods; differences cannot be attributed solely to leakage.\n\n")
        f.write("## 3. Leakage probe (record index added as a feature)\n\n"
                + md(probe_df) + "\n\n")
        f.write("## 4. Chronological holdout (70 / 30)\n\n" + md(hold_df) + "\n\n")
        f.write("## 5. Permutation importance (bagged CART, in-sample)\n\n"
                + md(imp.head(12)) + "\n\n")
        f.write("## 6. Probability calibration\n\n")
        f.write("The logistic model uses balanced class weights; its `prior correction` "
                "uses each fold's training prevalence. CART is unweighted and is shown "
                "as fitted. The Brier skill reference uses evaluation prevalence retrospectively, "
                "as an oracle constant baseline, not as a deployed forecasting rule.\n\n")
        f.write(md(cal) + "\n")
    print("  wrote results/phase1/summary.md")
    from phase1.refresh_analysis import refresh
    refresh()
    if os.path.exists(os.path.join(RESULTS, 'research_config.json')):
        print('  extended paper retained; rerun engineering and research stages before regenerating it')
    elif os.path.exists(os.path.join(RESULTS, 'source_audit.json')):
        from phase1.generate_report import write_markdown_report
        write_markdown_report()
        print('  wrote reports/phase1/technical_note.md from the generated results')
    else:
        print('  paper generation deferred: run audit_source.py, then generate_report.py')
    print("\ndone.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true",
                    help="re-download the dataset")
    main(**vars(ap.parse_args()))
