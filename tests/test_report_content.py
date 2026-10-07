"""Intermediate paper prose must use the same measured rates as its tables."""
import csv
import unittest
from pathlib import Path
from phase1.paper_content import build_cohort_paper

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless((ROOT / 'results/phase1/operating_points.csv').exists(), 'run baseline experiments first')
class CohortPaperTests(unittest.TestCase):
    def test_alert_transfer_sentence_uses_computed_rates(self):
        with (ROOT / 'results/phase1/operating_points.csv').open(encoding='utf-8', newline='') as stream:
            records = list(csv.DictReader(stream))
        holdout = next(row for row in records if row['model'] == 'LR' and row['validation'] == 'holdout')
        temporal = [row for row in records if row['model'] == 'LR' and row['validation'] == 'time']
        rate = sum(int(row['tp']) + int(row['fp']) for row in temporal) / sum(int(row['n']) for row in temporal)
        prevalence = sum(int(row['positives']) for row in temporal) / sum(int(row['n']) for row in temporal)
        expected = 'The holdout produces an LR alert rate of %.4f, whereas pooled record-order testing produces %.4f at prevalence %.4f.' % (float(holdout['alert_rate']), rate, prevalence)
        self.assertIn(expected, build_cohort_paper(ROOT))
