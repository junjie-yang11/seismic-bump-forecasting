"""Compare refitted scores and frozen A/B/C decisions separately; do not select new rules."""
import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys


def verify(root, output):
    root, output = Path(root).resolve(), Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    record = dict(passed=False, status='running', started_at_utc=datetime.now(timezone.utc).isoformat(),
                  scope='Independent model refits: separate score and frozen A/B/C decision comparisons; no threshold reselection.',
                  verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  score_comparison=dict(rtol=1e-9, atol=1e-10, origin='Existing phase2.verify.close criterion'),
                  decision_comparison='Exact Boolean equality', score_comparisons=[], decision_comparisons=[])
    output.write_text(json.dumps(record, indent=2), encoding='utf-8')
    try:
        sys.path[:0] = [str(root), str(root/'src')]
        import numpy as np
        import pandas as pd
        import scipy
        import xgboost as xgb
        from data import load
        from phase2.experiment import fit_fold
        from phase2.plan import PLAN
        from boosting import PARAMETERS
        config = io.StringIO()
        with redirect_stdout(config):
            np.show_config()
            scipy.show_config()
        freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True)
        record['environment'] = dict(python=platform.python_version(), system=platform.system(),
            platform=platform.platform(), machine=platform.machine(), numpy=np.__version__,
            pandas=pd.__version__, scipy=scipy.__version__, xgboost=xgb.__version__,
            xgboost_build=xgb.build_info(), numerical_libraries=config.getvalue(),
            pip_freeze=freeze.stdout.splitlines(), xgboost_parameters=PARAMETERS, locked_models=PLAN['model_settings'])
        out = root/'results/phase2'
        paths = [out/name for name in ('predictions.csv','references.csv','audits.csv','decisions.csv','fold_manifest.json','run_manifest.json')]
        paths += [root/'phase2'/name for name in ('experiment.py','plan.py','locked_plan.json')]
        paths += list((root/'src').glob('*.py'))
        record['input_sha256'] = {str(path.relative_to(root)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        predictions, references, audits, decisions = [pd.read_csv(out/(name+'.csv')) for name in ('predictions','references','audits','decisions')]
        manifests = json.loads((out/'fold_manifest.json').read_text())
        X, y, names, _ = load()
        for manifest in manifests:
            model, scheme, fold = (manifest[key] for key in ('model','scheme','fold'))
            pick = lambda frame: frame[(frame.model==model)&(frame.scheme==scheme)&(frame.fold==fold)].sort_values('row')
            fitted = fit_fold(model, X, y, np.array(manifest['outer_train_rows']), np.array(manifest['test_rows']), names)
            if model == 'XGBoost' and any(fitted['manifest'][key] != manifest[key] for key in ('depth','rounds')):
                raise AssertionError('Training-only parameter selection changed')
            saved, reference = pick(predictions), pick(references)
            if saved.row.tolist() != manifest['test_rows'] or reference.row.tolist() != manifest['reference_rows']:
                raise AssertionError('Replay row alignment changed')
            for kind, actual, expected in [('reference', fitted['reference_score'], reference.score.to_numpy()),
                    ('fixed', fitted['fixed_score'], saved.fixed_score.to_numpy()),
                    ('refitted', fitted['refitted_score'], saved.refitted_score.to_numpy())]:
                record['score_comparisons'].append(dict(model=model, scheme=scheme, fold=int(fold), kind=kind,
                    n=len(actual), max_absolute_difference=float(np.max(np.abs(actual-expected))),
                    bitwise_equal=bool(np.array_equal(actual, expected)),
                    passed=bool(np.allclose(actual, expected, rtol=1e-9, atol=1e-10, equal_nan=False))))
            policies = audits[(audits.model==model)&(audits.scheme==scheme)&(audits.fold==fold)]
            for workflow in ('fixed','refitted'):
                wide = pick(decisions[decisions.workflow==workflow])
                if wide.row.tolist() != manifest['test_rows']:
                    raise AssertionError('Decision replay row alignment changed')
                for _, policy in policies.iterrows():
                    actual = fitted[workflow+'_score'] >= policy.threshold
                    expected = wide[policy.rule].to_numpy(dtype=bool)
                    record['decision_comparisons'].append(dict(model=model, scheme=scheme, fold=int(fold),
                        workflow=workflow, rule=policy.rule, changed_alerts=int(np.count_nonzero(actual!=expected)),
                        passed=bool(np.array_equal(actual, expected))))
        record['score_checks_passed'] = all(row['passed'] for row in record['score_comparisons'])
        record['decision_checks_passed'] = all(row['passed'] for row in record['decision_comparisons'])
        record['passed'] = record['score_checks_passed'] and record['decision_checks_passed'] and len(manifests)==15
        record['status'] = 'passed' if record['passed'] else 'failed'
        if not record['passed']:
            record['error'] = 'Replay scores or exact frozen alert decisions differ; see individual comparisons.'
        record['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
        output.write_text(json.dumps(record, indent=2), encoding='utf-8')
        if not record['passed']:
            raise AssertionError(record['error'])
        print('Threshold replay passed:', len(record['score_comparisons']), 'score arrays;',
              len(record['decision_comparisons']), 'exact frozen decisions;',
              sum(row['changed_alerts'] for row in record['decision_comparisons']), 'changed alerts.')
        return record
    except (Exception, KeyboardInterrupt) as error:
        record.update(passed=False, status='failed', error_type=type(error).__name__, error=str(error),
                      failed_at_utc=datetime.now(timezone.utc).isoformat())
        output.write_text(json.dumps(record, indent=2), encoding='utf-8')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.root, args.output)
