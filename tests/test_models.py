"""Bootstrap boundary fixtures; these are not research observations."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from models import BaggedForest


class BootstrapTests(unittest.TestCase):
    def test_rare_positive_draws_are_not_conditioned_or_discarded(self):
        X = np.arange(4., dtype=float).reshape(-1, 1)
        y = np.array([1., 0., 0., 0.])
        model = BaggedForest(n_trees=24, max_depth=0, seed=7).fit(X, y)
        rng = np.random.default_rng(7)
        rates = [y[rng.integers(0, len(y), len(y))].mean() for _ in range(24)]
        self.assertEqual(len(model.trees), 24)
        self.assertIn(0., rates)
        self.assertIn(.25, rates)
        np.testing.assert_allclose(model.predict_proba(X), np.mean(rates))

    def test_all_negative_training_creates_constant_leaf_trees(self):
        X = np.arange(4., dtype=float).reshape(-1, 1)
        model = BaggedForest(n_trees=6, seed=7).fit(X, np.zeros(4))
        self.assertEqual(len(model.trees), 6)
        np.testing.assert_array_equal(model.predict_proba(X), np.zeros(4))


if __name__ == '__main__':
    unittest.main()
