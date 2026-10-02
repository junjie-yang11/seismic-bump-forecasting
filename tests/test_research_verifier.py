"""Prove the extended verifier rejects altered evidence without disk edits."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verify_research import main


@unittest.skipUnless((ROOT / 'results/research_config.json').exists(), 'run extended experiments first')
class ResearchVerifierTests(unittest.TestCase):
    def reject(self, name, column, value, message):
        original = pd.read_csv
        def read(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if Path(path).name == name:
                result = result.copy(); result.loc[0, column] = value
            return result
        with patch.object(pd, 'read_csv', read), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(AssertionError, message):
                main()

    def test_shap_corruption_rejected(self):
        self.reject('shap_predictions.csv', 'shap__energy', 99, 'SHAP additivity')

    def test_reference_threshold_corruption_rejected(self):
        self.reject('engineering_fold_audit.csv', 'threshold', .123, 'reference-derived budget threshold')

    def test_inner_selection_corruption_rejected(self):
        self.reject('xgboost_tuning.csv', 'value', 99, 'training-only selection value')

    def test_stability_sensitivity_corruption_rejected(self):
        self.reject('shap_stability_sensitivity.csv', 'rank_spearman', -.99, 'recomputed sensitivity Spearman')

    def test_historical_reference_corruption_rejected(self):
        self.reject('probability_reference_comparison.csv', 'historical_brier', .9, 'historical')

    def test_phase_contrast_corruption_rejected(self):
        self.reject('feature_ablation_phase_contrasts.csv', 'without_seismic_minus_full', .9, 'without_seismic_minus_full')


if __name__ == '__main__':
    unittest.main()
