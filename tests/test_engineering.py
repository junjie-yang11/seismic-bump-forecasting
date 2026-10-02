import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from engineering import GROUPS, feature_variants, evaluate_splits, warning_summary


class SignalModel:
    def fit(self, X, y):
        self.offset = float(y.mean()) / 10
        return self

    def predict_proba(self, X):
        return np.clip(X[:, 0] + self.offset, 0, 1)


class EngineeringTests(unittest.TestCase):
    def setUp(self):
        self.X = np.linspace(.01, .95, 100).reshape(-1, 1)
        self.y = (np.arange(100) % 7 == 0).astype(float)
        self.splits = [(np.arange(60), np.arange(60, 100))]

    def test_future_labels_do_not_change_any_budget_threshold(self):
        base = evaluate_splits(SignalModel, self.X, self.y, self.splits)
        y = self.y.copy(); y[60:] = 1 - y[60:]
        altered = evaluate_splits(SignalModel, self.X, y, self.splits)
        for key in ('score', 'threshold', 'training_prior', 'calibrated'):
            np.testing.assert_allclose(base[0][key], altered[0][key])
        np.testing.assert_allclose(base[2].threshold, altered[2].threshold)

    def test_future_features_do_not_change_reference_or_thresholds(self):
        base = evaluate_splits(SignalModel, self.X, self.y, self.splits)
        X = self.X.copy(); X[60:] = 0
        changed = evaluate_splits(SignalModel, X, self.y, self.splits)
        np.testing.assert_allclose(base[1].score, changed[1].score)
        np.testing.assert_allclose(base[2].threshold, changed[2].threshold)

    def test_boundary_ties_respect_every_reference_budget(self):
        X = np.full_like(self.X, .5)
        p, ref, audit = evaluate_splits(SignalModel, X, self.y, self.splits)
        for _, row in audit.iterrows():
            self.assertLessEqual(row.reference_alerts, int(np.floor(row.budget * row.reference_n)))
        self.assertTrue((audit.reference_alerts == 0).all())
        # The outer refit may shift constant scores; the cap applies to the
        # reference population, not to future scores from a different fit.

    def test_larger_budgets_produce_nested_alerts(self):
        p, _, audit = evaluate_splits(SignalModel, self.X, self.y, self.splits)
        thresholds = audit[audit.policy == 'budget'].sort_values('budget').threshold.to_numpy()
        self.assertTrue((thresholds[:-1] >= thresholds[1:]).all())
        counts = [s['alerts'] for s in warning_summary(p, audit)]
        self.assertEqual(counts, sorted(counts))

    def test_groups_partition_design_and_removal_excludes_group(self):
        names = [n for group in GROUPS.values() for n in group]
        variants = feature_variants(names)
        self.assertEqual(len(variants), 9)
        for group, members in GROUPS.items():
            self.assertFalse(set(members) & {names[i] for i in variants['without_' + group]})
            self.assertEqual(set(members), {names[i] for i in variants[group + '_only']})
        with self.assertRaises(ValueError):
            feature_variants(names + ['unexpected'])

    def test_invalid_budget_or_overlapping_tests_rejected(self):
        for budgets in ((.1, .1), (0,), (1,), (float('nan'),)):
            with self.assertRaises(ValueError):
                evaluate_splits(SignalModel, self.X, self.y, self.splits, budgets)
        with self.assertRaises(ValueError):
            evaluate_splits(SignalModel, self.X, self.y, self.splits * 2)


if __name__ == '__main__':
    unittest.main()
