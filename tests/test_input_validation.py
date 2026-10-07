import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from metrics import average_precision, roc_auc, summarise, threshold_metrics
from calibration import brier_score, brier_skill_score
from evaluation import cross_validate, cross_validate_splits, stratified_random_folds, time_ordered_folds
from engineering import evaluate_splits


class InputValidationTests(unittest.TestCase):
    def test_fold_assignments_cannot_silently_omit_rows(self):
        X, y = np.ones((10, 1)), np.arange(10) % 2
        def forbidden_factory():
            self.fail('invalid fold assignment reached a model fit')
        for fold in (np.array([0, 0, 1, 1]), np.arange(10).reshape(5, 2),
                     np.arange(10, dtype=float), np.array([0, 1] * 4 + [-1, -1]),
                     np.zeros(10, dtype=int)):
            with self.subTest(shape=fold.shape, dtype=fold.dtype):
                with self.assertRaises(ValueError):
                    cross_validate(forbidden_factory, X, y, fold)

    def test_scores_cannot_broadcast_across_labels(self):
        y = np.array([0., 1.])
        for function in (average_precision, roc_auc, brier_score, brier_skill_score):
            for score in (np.array([[.2], [.8]]), np.array([.2]), np.array([.2, np.nan])):
                with self.subTest(function=function.__name__, shape=score.shape):
                    with self.assertRaises(ValueError): function(y, score)

    def test_invalid_labels_and_empty_inputs_are_rejected(self):
        for function in (average_precision, roc_auc, brier_score):
            for y, score in [([], []), ([0, 2], [.1, .9]), ([0, np.nan], [.1, .9])]:
                with self.assertRaises(ValueError): function(y, score)

    def test_threshold_vectors_cannot_broadcast(self):
        y, score = np.array([0, 1]), np.array([.2, .8])
        for threshold in (np.array([[.5], [.5]]), np.array([.5]), np.nan):
            with self.assertRaises(ValueError): threshold_metrics(y, score, threshold)
            with self.assertRaises(ValueError): summarise(y, score, threshold=threshold)

    def test_probability_metrics_reject_out_of_range_values(self):
        for function in (brier_score, brier_skill_score):
            with self.assertRaises(ValueError): function([0, 1], [-.1, 1.1])
        # Ranking measures also support finite decision margins.
        self.assertEqual(average_precision([0, 1], [-2., 3.]), 1.)

    def test_invalid_temporal_indices_rejected_before_model_fit(self):
        X, y = np.ones((10, 1)), np.arange(10) % 2
        malformed = [([-1, 0, 1], [8, 9]), ([0, 1, 1], [8, 9]),
                     ([2, 0, 1], [8, 9]), ([0, 1, 2], [9, 8]),
                     ([0., 1., 2.], [8, 9]), ([0, 1, 2], [9, 10])]
        def forbidden_factory():
            self.fail('invalid indices reached a model fit')
        for train, test in malformed:
            with self.subTest(train=train, test=test):
                with self.assertRaises(ValueError):
                    cross_validate_splits(forbidden_factory, X, y, [(train, test)])
                with self.assertRaises(ValueError):
                    evaluate_splits(forbidden_factory, X, y, [(train, test)])

    def test_fold_builders_reject_invalid_classes_or_counts(self):
        for y in ([0, 2], [0, np.nan], []):
            with self.assertRaises(ValueError): stratified_random_folds(y, k=2)
        for count in (0, 1, 11, 2.5, True):
            with self.assertRaises(ValueError): time_ordered_folds(10, count)


if __name__ == '__main__':
    unittest.main()
