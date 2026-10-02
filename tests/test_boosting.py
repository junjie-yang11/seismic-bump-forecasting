"""Optional native XGBoost behavior tests in the research environment."""
import importlib.util
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


@unittest.skipUnless(importlib.util.find_spec('xgboost'), 'install requirements-research.txt')
class BoostingTests(unittest.TestCase):
    def test_native_contributions_reconstruct_margin_and_probability(self):
        from boosting import BoostedModel
        rng = np.random.default_rng(31)
        X = rng.normal(size=(180, 2)); y = (X[:, 0] + X[:, 1] > .8).astype(float)
        model = BoostedModel(2, 80, ['a', 'b']).fit(X[:140], y[:140])
        contribution = model.contributions(X[140:]); margin = model.margin(X[140:])
        np.testing.assert_allclose(contribution.sum(axis=1), margin, atol=1e-5)
        np.testing.assert_allclose(1 / (1 + np.exp(-margin)), model.predict_proba(X[140:]), atol=1e-7)

    def test_zero_positive_reference_uses_defined_fallback(self):
        from boosting import select_parameters
        X = np.arange(100, dtype=float).reshape(-1, 1)
        y = (np.arange(100) % 5 == 0).astype(float); y[80:] = 0
        choice, candidates, fit, reference, scores = select_parameters(X, y, ['a'])
        self.assertTrue(all(r['selection_metric'] == 'negative Brier' for r in candidates))
        for row, score in zip(candidates, scores):
            self.assertAlmostEqual(row['value'], -float(np.mean(score ** 2)))
        self.assertEqual(sum(r['selected'] for r in candidates), 1)

    def test_future_labels_cannot_change_nested_parameters_or_cutoffs(self):
        from boosting import BoostedModel, select_parameters
        from engineering import evaluate_splits
        X = np.linspace(0, 1, 120).reshape(-1, 1)
        y = (np.arange(120) % 5 == 0).astype(float)
        splits = [(np.arange(90), np.arange(90, 120))]
        selected = []
        def evaluate(labels):
            choices = []
            def factory(fold, train, fit):
                inside = select_parameters(X[fit], labels[fit], ['a'])[0]
                outside = select_parameters(X[train], labels[train], ['a'])[0]
                choices.extend([inside, outside])
                return lambda: BoostedModel(*inside, names=['a']), lambda: BoostedModel(*outside, names=['a'])
            result = evaluate_splits(None, X, labels, splits, fold_factory=factory)
            selected.append(choices)
            return result
        base = evaluate(y)
        altered = y.copy(); altered[90:] = 1 - altered[90:]
        changed = evaluate(altered)
        self.assertEqual(selected[0], selected[1])
        np.testing.assert_allclose(base[0].score, changed[0].score)
        np.testing.assert_allclose(base[2].threshold, changed[2].threshold)


if __name__ == '__main__':
    unittest.main()
