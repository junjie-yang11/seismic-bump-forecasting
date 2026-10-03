"""Immutable protocol declaration; written before any phase-two experiment."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'phase2'
PLAN = dict(version=1,
    title='Cost- and Capacity-Sensitive Seismic Warning: A Retrospective Study of Threshold Transfer',
    nature='Exploratory retrospective study; previously inspected data; record order is a temporal proxy',
    models=['XGBoost', 'LR', 'CART'], features='All 17 existing design columns',
    outer_blocks=5, fit_fraction=.8, holdout_fraction=.7,
    budgets=[.01, .05, .10, .20], costs=[5, 10, 20, 50],
    scenarios=[.02, .05, .10, .15],
    model_settings=dict(LR=dict(lam=1., class_weight=True, max_iter=60),
        CART=dict(n_trees=60, max_depth=6, min_samples_leaf=20, seed=7),
        XGBoost=dict(candidates=[[2,80],[2,160],[3,80],[3,160]], eta=.05,
                    min_child_weight=10, reg_lambda=5, nthread=2, seed=7,
                    subsample=1., colsample_bytree=1., scale_pos_weight=1)),
    tuning='XGBoost temporal 80/20 split INSIDE model-fitting area; max AP, negative Brier if no positives; first grid entry on exact ties',
    refit='Same selected parameters; all outer historical rows; no retuning; same numeric threshold',
    score_scale='Raw model scores for selection and application; no additional probability correction',
    candidates='Whole score groups; >=; +inf empty, -inf all; otherwise minimum included reference score',
    A='Maximum feasible reference alerts; no labels used in selection',
    B='Minimum reference r*FN+FP; among equal loss choose fewer alerts',
    C='Minimum reference r*FN+FP subject to floor(budget*Nref); ties choose fewer alerts',
    second_best='Second distinct feasible decision by loss, including ties; gap zero if multiple optima; undefined for A or one feasible decision',
    capacity_binding='Unconstrained B decision is infeasible under the stated reference budget',
    topk='Retrospective batch ranking only; whole ties, maximum feasible test alerts, no test labels; may underfill budget',
    no_alarm='Always zero alerts', primary_comparisons=['C-A','C-B','Refitted-Fixed'],
    secondary_comparison='B-A', primary_evidence='Four per-phase results; pooled counts supplementary',
    bootstrap=dict(replicates=2000, block_length=32, seed=20261003,
        scope='Paired loss differences; moving blocks within phases; fixed fitted models and selected policies; time cohort only'),
    scenario_assumption='Class-conditional score distributions fixed; prevalence changes; no threshold reselection',
    no_reference_positives='B and C select no alarms; A remains budget-only; no fabricated targets',
    zero_slots='A and C select +inf; whole tied groups are never split',
    no_fit_class_variation='Raise explicit insufficient-model-fitting-classes error; do not invent predictions')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def lock_plan():
    path = ROOT / 'phase2' / 'locked_plan.json'
    digest = hashlib.sha256(canonical(PLAN)).hexdigest()
    if path.exists():
        saved = json.loads(path.read_text(encoding='utf-8'))
        if saved['plan'] != PLAN or saved['plan_sha256'] != digest:
            raise RuntimeError('Protocol changed: record a versioned amendment before running')
        return saved
    saved = dict(locked_at_utc=datetime.now(timezone.utc).isoformat(), plan_sha256=digest,
                 plan=PLAN, amendments=[])
    path.write_text(json.dumps(saved, indent=2) + '\n', encoding='utf-8')
    return saved

if __name__ == '__main__':
    print(json.dumps(lock_plan(), indent=2))
