"""Saved-score cohort gaps preserve seed means, ties and source-row identity."""
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch
import numpy as np
import pandas as pd
from phase1 import gap_summary


class GapSummaryTests(unittest.TestCase):
    def setUp(self):
        self.labels = np.array([1., 0., 1., 0.])
        self.random = pd.DataFrame([
            dict(seed=seed, row=row, y=self.labels[row], score=.5)
            for seed in range(5) for row in range(4)])
        self.ordered = pd.DataFrame([
            dict(row=row, y=self.labels[row], score=score)
            for row, score in [(0, .9), (1, .7), (2, .6)]])

    def test_tied_scores_are_one_ap_group(self):
        result = gap_summary.design_gap(self.random, self.ordered, self.labels, 'example')
        self.assertAlmostEqual(result['original_gap'], .5 - 5/6)
        self.assertAlmostEqual(result['same_test_gap'], 2/3 - 5/6)
        self.assertAlmostEqual(result['gap_reduction_fraction'], .5)

    def test_mean_seed_ap_is_not_ap_of_pooled_seed_rows(self):
        scores = [[.9, .2, .8, .1], [.1, .9, .2, .8],
                  [.9, .2, .8, .1], [.1, .9, .2, .8], [.9, .2, .8, .1]]
        for seed in range(5):
            self.random.loc[self.random.seed == seed, 'score'] = scores[seed]
        result = gap_summary.design_gap(self.random, self.ordered, self.labels, 'example')
        expected = (3 + 2 * (5/12)) / 5
        self.assertAlmostEqual(result['original_gap'] + 5/6, expected)
        pooled = gap_summary.average_precision(self.random.y.to_numpy(), self.random.score.to_numpy())
        self.assertNotAlmostEqual(expected, pooled)

    def test_shuffled_input_rows_do_not_change_gaps(self):
        result = gap_summary.design_gap(self.random, self.ordered, self.labels, 'example')
        shuffled = gap_summary.design_gap(self.random.sample(frac=1, random_state=5),
                                         self.ordered.iloc[::-1], self.labels, 'example')
        self.assertEqual(result, shuffled)

    def test_source_label_mismatch_is_rejected(self):
        self.random.loc[0, 'y'] = 0
        with self.assertRaisesRegex(ValueError, 'source rows'):
            gap_summary.design_gap(self.random, self.ordered, self.labels, 'example')

    def test_missing_or_duplicate_seed_rows_are_rejected(self):
        for bad in (self.random.iloc[1:], pd.concat([self.random, self.random.iloc[:1]])):
            with self.subTest(size=len(bad)), self.assertRaises(ValueError):
                gap_summary.design_gap(bad, self.ordered, self.labels, 'example')

    def test_missing_or_unexpected_seeds_are_rejected(self):
        for bad in (self.random[self.random.seed != 4], self.random.assign(seed=self.random.seed + 1)):
            with self.assertRaisesRegex(ValueError, 'seeds'):
                gap_summary.design_gap(bad, self.ordered, self.labels, 'example')

    def test_duplicate_and_fractional_time_indices_are_rejected(self):
        bad_fractional = self.ordered.copy(); bad_fractional['row'] = bad_fractional.row.astype(float)
        bad_fractional.loc[0, 'row'] = .5
        for bad in (pd.concat([self.ordered, self.ordered.iloc[:1]]), bad_fractional):
            with self.assertRaises(ValueError):
                gap_summary.design_gap(self.random, bad, self.labels, 'example')

    def test_invalid_prediction_scores_are_rejected(self):
        for score in (float('nan'), float('inf'), -.1, 1.1):
            bad = self.random.copy(); bad.loc[0, 'score'] = score
            with self.subTest(score=score), self.assertRaises(ValueError):
                gap_summary.design_gap(bad, self.ordered, self.labels, 'example')

    def test_failed_computation_does_not_replace_existing_table(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root/'results/phase1'; out.mkdir(parents=True)
            path = out/'gap_attenuation_all_models.csv'; path.write_bytes(b'existing evidence')
            with patch.object(gap_summary, 'compute_gap_rows', side_effect=ValueError('broken input')):
                with self.assertRaisesRegex(ValueError, 'broken input'):
                    gap_summary.write_gap_summary(root)
            self.assertEqual(path.read_bytes(), b'existing evidence')


if __name__ == '__main__':
    unittest.main()
