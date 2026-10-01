"""Ensure generated-output corruption is rejected, using in-memory mutations."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verify_results import verify

@unittest.skipUnless((ROOT / 'results/predictions.csv').exists(), 'run experiments first')
class VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            verify()  # Establish a valid baseline before testing corruption.

    def rejected(self, name, column, value, message):
        original = pd.read_csv
        def read(path, *args, **kwargs):
            frame = original(path, *args, **kwargs)
            if Path(path).name == name:
                frame = frame.copy()
                if column == 'drop': frame = frame.iloc[1:]
                else: frame.loc[0, column] = value
            return frame
        with patch.object(pd, 'read_csv', read), self.assertRaisesRegex(AssertionError, message):
            verify()

    def test_missing_test_row(self):
        self.rejected('predictions.csv', 'drop', None, 'complete test coverage')

    def test_changed_prior(self):
        self.rejected('fold_audit.csv', 'training_prior', .5, 'audit training prior')

    def test_changed_threshold(self):
        self.rejected('predictions.csv', 'threshold', .123, 'per-row fixed threshold')

    def test_changed_calibration_metric(self):
        self.rejected('calibration.csv', 'ece', .9, 'recomputed calibration ece')

    def test_changed_random_mean(self):
        self.rejected('metrics_by_scheme.csv', 'recall', .999, 'five-seed mean recall')
