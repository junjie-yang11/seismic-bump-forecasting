"""Independent equation checks on measured outputs and frozen scenarios.

Run from the repository root: python -B -m phase1.verify_formulae.
Mathematical definitions and hypothetical costs/prevalences are distinguished
from measured monitoring rows. No model, threshold or scenario is optimized.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def verify():
    checks = 0
    sources = {}
    def read(name):
        path = ROOT / 'results' / ((name if name.startswith('phase2/') else 'phase1/' + name) + '.csv')
        sources[str(path.relative_to(ROOT)).replace('\\', '/')] = hashlib.sha256(path.read_bytes()).hexdigest()
        return pd.read_csv(path)
    def check(value, name):
        nonlocal checks
        if not value: raise AssertionError(name)
        checks += 1
    def close(a, b, name, atol=1e-10):
        check(np.allclose(a, b, rtol=1e-9, atol=atol, equal_nan=True), name)

    # Pairwise ROC definition and threshold-group AP avoid calling metric code.
    predictions = read('predictions')
    metrics = read('metrics_by_scheme')
    for model, part in predictions.query("validation=='time'").groupby('model'):
        y, score = part.y.to_numpy(), part.score.to_numpy()
        positive, negative = score[y == 1], score[y == 0]
        auc = np.mean((positive[:, None] > negative) + .5 * (positive[:, None] == negative))
        ap, previous = 0., 0
        for threshold in np.unique(score)[::-1]:
            chosen = score >= threshold
            tp = int(y[chosen].sum())
            ap += (tp - previous) / y.sum() * tp / chosen.sum()
            previous = tp
        recorded = metrics[(metrics.model == model) & (metrics.validation == 'time-ordered expanding window')].iloc[0]
        close(recorded.roc_auc, auc, 'pairwise ROC-AUC')
        close(recorded.pr_auc, ap, 'whole-group stepwise AP')

    engineering = read('engineering_predictions')
    lr = engineering[engineering.model == 'LR']
    p, prior = lr.score.to_numpy(), lr.training_prior.to_numpy()
    # Direct Bayes-odds formula for balanced-weight prior correction.
    p = np.clip(p, 1e-12, 1 - 1e-12)
    expected = p * prior / (p * prior + (1 - p) * (1 - prior))
    close(lr.calibrated, expected, 'balanced-prior correction by direct odds', atol=1e-10)
    unweighted = engineering[engineering.model != 'LR']
    close(unweighted.score, unweighted.calibrated, 'unweighted models uncorrected')
    probability_refs = read('probability_reference_comparison')
    for _, row in probability_refs.iterrows():
        part = engineering[(engineering.model == row.model) & (engineering.validation == row.validation) & (engineering.variant == 'full')]
        if row.fold >= 0: part = part[part.fold == row.fold]
        y = part.y.to_numpy()
        brier = np.square(part.calibrated.to_numpy() - y).sum() / len(y)
        historical = np.square(part.training_prior.to_numpy() - y).sum() / len(y)
        oracle = np.square(y.mean() - y).sum() / len(y)
        close([row.model_brier, row.historical_brier, row.oracle_brier], [brier, historical, oracle], 'Brier definitions')
        close([row.historical_skill, row.oracle_skill], [1 - brier / historical, 1 - brier / oracle], 'Brier skill with explicit references')
    calibration = read('calibration'); bins = read('calibration_bins')
    for label, variant, correction in [('LR', 'As fitted', False), ('LR', 'Fold-prior corrected', True)]:
        part = predictions[(predictions.model.str.contains('logistic')) & (predictions.validation == 'time')]
        score = part.calibrated.to_numpy() if correction else part.score.to_numpy()
        y = part.y.to_numpy()
        edges = np.unique(np.quantile(score, np.arange(11) / 10))
        if len(edges) == 1: edges = np.r_[edges, edges + 1e-12]
        group = np.searchsorted(edges[1:-1], score, side='right')
        weighted_gap, maximum_gap, counts = 0., 0., []
        for i in range(len(edges) - 1):
            mask = group == i
            if not mask.any(): continue
            gap = abs(y[mask].mean() - score[mask].mean())
            weighted_gap += mask.sum() * gap / len(y)
            maximum_gap = max(maximum_gap, gap); counts.append(int(mask.sum()))
        record = calibration[(calibration.model == label) & (calibration.variant.str.startswith('after' if correction else 'as'))].iloc[0]
        close([record.ece, record.mce], [weighted_gap, maximum_gap], 'ECE/MCE quantile definitions')
        stored_bins = bins[(bins.model == label) & (bins.variant == variant)]
        check(list(stored_bins['count']) == counts, 'all calibration observations conserved')

    shap = read('shap_predictions')
    margin = shap[[c for c in shap if c.startswith('shap__')]].sum(axis=1) + shap.bias
    # XGBoost margins/contributions are accumulated in float32; CSV summation
    # uses float64. Preserve and quantify this rounding difference explicitly.
    shap_margin_error = float(np.abs(margin - shap.margin).max())
    shap_probability_error = float(np.abs(1 / (1 + np.exp(-margin)) - shap.score).max())
    close(margin, shap.margin, 'TreeSHAP additive log-odds identity', atol=5e-6)
    close(1 / (1 + np.exp(-margin)), shap.score, 'TreeSHAP logistic probability identity', atol=5e-7)

    # Recover decisions and truths independently, then apply count formulae.
    phase_predictions = read('phase2/predictions'); decisions = read('phase2/decisions')
    evaluations = read('phase2/evaluations')
    truth = {(m, s, int(f)): q.sort_values('row') for (m, s, f), q in phase_predictions.groupby(['model', 'scheme', 'fold'])}
    alerts = {(m, s, int(f), w): q.sort_values('row') for (m, s, f, w), q in decisions.groupby(['model', 'scheme', 'fold', 'workflow'])}
    for _, row in evaluations.iterrows():
        cohort = truth[(row.model, row.scheme, int(row.fold))]
        decision = alerts[(row.model, row.scheme, int(row.fold), row.workflow)]
        check(np.array_equal(cohort.row, decision.row), 'decision rows paired')
        y = cohort.y.to_numpy(); alarm = decision[row.rule].to_numpy(dtype=bool)
        tp = int(np.sum(alarm & (y == 1))); fp = int(np.sum(alarm & (y == 0)))
        fn = int(np.sum(~alarm & (y == 1))); tn = int(np.sum(~alarm & (y == 0)))
        n = len(y); loss = row.cost * fn + fp
        close([row.tp, row.fp, row.fn, row.tn, row.alerts], [tp, fp, fn, tn, tp + fp], 'confusion counts')
        close([row.loss, row.loss100, row.loss_delta_no_alarm100], [loss, 100 * loss / n, 100 * (fp - row.cost * tp) / n], 'loss and no-alarm identities')
        close([row.recall, row.precision, row.alert_rate], [tp / (tp + fn) if tp + fn else np.nan, tp / (tp + fp) if tp + fp else 0, (tp + fp) / n], 'recall precision workload')
        if np.isfinite(row.budget):
            slots = int(np.floor(row.budget * n))
            close([row.slots, row.excess], [slots, max(0, tp + fp - slots)], 'floor capacity and excess')
    scenarios = read('phase2/prevalence_scenarios'); scenario_value = read('phase2/prevalence_decision_value')
    expected_loss = 100 * (scenarios.cost * scenarios.scenario_prevalence * scenarios.empirical_fnr + (1 - scenarios.scenario_prevalence) * scenarios.empirical_fpr)
    expected_alerts = scenarios.scenario_prevalence * (1 - scenarios.empirical_fnr) + (1 - scenarios.scenario_prevalence) * scenarios.empirical_fpr
    close(scenarios.expected_loss100, expected_loss, 'frozen prevalence scenario expectation')
    close(scenarios.expected_alert_rate, expected_alerts, 'frozen prevalence workload expectation')
    close(scenario_value.delta_loss_vs_no_alarm_100, expected_loss - 100 * scenarios.cost * scenarios.scenario_prevalence, 'scenario no-alarm difference')
    check(np.all((expected_alerts >= 0) & (expected_alerts <= 1)), 'scenario workload probability bounds')
    enriched = read('phase2/threshold_audit_enriched')
    close(enriched.loss_gap_100, 100 * enriched.loss_gap / enriched.reference_n, 'normalized next-decision margin')
    close(enriched.reference_prevalence, enriched.reference_positives / enriched.reference_n, 'historical prevalence')
    record = dict(passed=True, checks=checks, completed_at_utc=datetime.now(timezone.utc).isoformat(),
        sources=sources, verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        shap_float32_rounding=dict(maximum_margin_error=shap_margin_error,maximum_probability_error=shap_probability_error,
                                  margin_absolute_tolerance=5e-6,probability_absolute_tolerance=5e-7),
        scope='Independent formula reconstruction from saved row-level evidence; not an independent field validation.',
        distinctions=dict(measured='Monitoring features, binary outcomes, fitted scores, decisions and derived evaluations.',
            assumptions='Record order as a time proxy, hypothetical relative costs, inspection budgets and frozen prevalence scenarios.',
            undefined='Empty cells denote undefined metrics or aggregate vector thresholds; infinities encode empty/full alert rules.'))
    (ROOT / 'results/phase2/formula_verification.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print('RESULT: %d independent formula checks passed.' % checks)
    return checks


if __name__ == '__main__':
    record_path = ROOT / 'results/phase2/formula_verification.json'
    record_path.write_text(json.dumps(dict(passed=False, status='running')), encoding='utf-8')
    try:
        verify()
    except Exception as error:
        record_path.write_text(json.dumps(dict(passed=False, status='failed',
            error_type=type(error).__name__, error=str(error)), indent=2), encoding='utf-8')
        raise
