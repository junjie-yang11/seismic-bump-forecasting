"""Fit strictly before the policy reference; refit without retuning."""
import sys
import numpy as np
from .plan import ROOT, PLAN
sys.path.insert(0, str(ROOT / 'src'))
from models import LogisticRegressionIRLS, BaggedForest
from boosting import BoostedModel, select_parameters, CANDIDATES, PARAMETERS

def validate_model_settings():
    """Imported first-stage settings must still match the locked protocol."""
    settings=PLAN['model_settings']['XGBoost']
    if [list(pair) for pair in CANDIDATES] != settings['candidates']:
        raise ValueError('Imported XGBoost grid differs from the locked protocol')
    for key in ('eta','min_child_weight','reg_lambda','nthread','seed',
                'subsample','colsample_bytree','scale_pos_weight'):
        if PARAMETERS[key] != settings[key]:
            raise ValueError('Imported XGBoost setting differs from locked protocol: '+key)
from input_checks import supervised_arrays, split_indices

def fit_fold(model, X, y, train, test, names):
    validate_model_settings()
    X, y = supervised_arrays(X,y)
    train, test = split_indices(train,test,len(y),temporal=True)
    split = int(PLAN['fit_fraction']*len(train))
    fitting, reference = train[:split], train[split:]
    if not len(reference) or len(np.unique(y[fitting])) != 2:
        raise ValueError('Insufficient model-fitting classes or policy-reference rows')
    tuning, tuning_scores = [], []
    manifest = dict(fit_rows=fitting.tolist(), reference_rows=reference.tolist(),
                    outer_train_rows=train.tolist(), test_rows=test.tolist(), model=model)
    if model == 'XGBoost':
        choice, tuning, inner_fit, inner_ref, tuning_scores = select_parameters(X[fitting],y[fitting],names,True)
        manifest.update(depth=choice[0], rounds=choice[1],
            tuning_fit_rows=fitting[inner_fit].tolist(), tuning_reference_rows=fitting[inner_ref].tolist())
        factory = lambda: BoostedModel(*choice,names=names)
    elif model == 'LR':
        settings=PLAN['model_settings']['LR']
        factory = lambda: LogisticRegressionIRLS(**settings)
    elif model == 'CART':
        settings=PLAN['model_settings']['CART']
        factory = lambda: BaggedForest(settings['n_trees'],settings['max_depth'],
                                       settings['min_samples_leaf'],None,seed=settings['seed'])
    else: raise ValueError('Unknown model')
    fixed = factory().fit(X[fitting],y[fitting])
    fixed_score = fixed.predict_proba(X[test])
    reference_score = fixed.predict_proba(X[reference])
    refitted = factory().fit(X[train],y[train])
    refitted_score = refitted.predict_proba(X[test])
    return dict(manifest=manifest, tuning=tuning, tuning_scores=tuning_scores,
                fixed_score=fixed_score, refitted_score=refitted_score,
                reference_score=reference_score)
