"""Behavioral regressions for leakage, future scores and missing test folds."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from evaluation import cross_validate_splits
from metrics import average_precision, prior_threshold, summarise, curve_points
from calibration import prior_correction, reliability_curve

class FakeModel:
    class_weight = True
    def fit(self, X, y):
        self.offset = float(y.mean())
        return self
    def predict_proba(self, X):
        return np.clip(X[:, 0] + self.offset / 10, .001, .999)

class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.X = np.linspace(.1, .8, 30).reshape(-1, 1)
        self.y = (np.arange(30) % 3 == 0).astype(float)
        self.splits = [(np.arange(20), np.arange(20, 30))]

    def evaluate(self, X=None, y=None):
        return cross_validate_splits(FakeModel, self.X if X is None else X,
            self.y if y is None else y, self.splits, return_details=True)

    def test_future_labels_cannot_affect_scores_threshold_or_prior(self):
        base = self.evaluate()
        y = self.y.copy(); y[20:] = 0
        altered = self.evaluate(y=y)
        for key in ('score', 'threshold', 'training_prior', 'calibrated'):
            np.testing.assert_allclose(base[key], altered[key], equal_nan=True)

    def test_future_features_cannot_affect_threshold_or_prior(self):
        base = self.evaluate()
        X = self.X.copy(); X[20:] = .01
        altered = self.evaluate(X=X)
        for key in ('threshold', 'training_prior'):
            np.testing.assert_allclose(base[key], altered[key], equal_nan=True)

    def test_all_negative_test_block_is_retained(self):
        y = self.y.copy(); y[20:] = 0
        result = self.evaluate(y=y)
        self.assertTrue(np.isfinite(result['score'][20:]).all())
        self.assertTrue(np.isnan(result['score'][:20]).all())

    def test_fold_correction_uses_training_prior(self):
        result = self.evaluate()
        np.testing.assert_allclose(result['calibrated'][20:],
            prior_correction(result['score'][20:], self.y[:20].mean(), .5))

    def test_unweighted_model_is_not_corrected(self):
        class Unweighted(FakeModel): class_weight = False
        result = cross_validate_splits(Unweighted, self.X, self.y, self.splits, return_details=True)
        np.testing.assert_allclose(result['calibrated'][20:], result['score'][20:])

    def test_overlapping_training_and_test_rejected(self):
        with self.assertRaises(ValueError):
            cross_validate_splits(FakeModel, self.X, self.y, [(np.arange(21), np.arange(20, 30))])

    def test_summary_requires_fixed_threshold(self):
        with self.assertRaises(ValueError): summarise(self.y, self.X[:, 0])

    def test_boundary_ties_do_not_exceed_reference_budget(self):
        for p in (np.zeros(10), np.array([.9, .8, .8, .8, .1])):
            threshold = prior_threshold(p, .3)
            self.assertLessEqual(int((p >= threshold).sum()), int(len(p) * .3))

    def test_ap_is_invariant_to_tie_order(self):
        y, p = np.array([1., 0., 1., 0.]), np.array([.8, .8, .2, .2])
        self.assertAlmostEqual(average_precision(y, p), .5)
        self.assertAlmostEqual(average_precision(y[::-1], p[::-1]), .5)

    def test_curve_endpoints(self):
        roc, pr = curve_points(self.y, self.X[:, 0])
        np.testing.assert_allclose(roc[[0, -1]], [[0, 0], [1, 1]])
        np.testing.assert_allclose(pr[0], [0, 1])

    def test_constant_calibration_bins_conserve_samples(self):
        for strategy in ('uniform', 'quantile'):
            rc = reliability_curve(np.array([1., 0., 0., 0.]), np.full(4, .5), strategy=strategy)
            self.assertEqual(rc['count'].sum(), 4)
            self.assertAlmostEqual(rc['obs_freq'][0], .25)

    def test_invalid_prior_rejected(self):
        for prior in (0, 1, -1, np.nan):
            with self.assertRaises(ValueError): prior_correction([.5], prior)

if __name__ == '__main__': unittest.main()
