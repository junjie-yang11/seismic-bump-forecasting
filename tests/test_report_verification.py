"""A malformed current report input must revoke an earlier success."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from phase2 import verify_report as verifier


class ReportTableEditions(unittest.TestCase):
    def table(self, rows):
        return SimpleNamespace(rows=[SimpleNamespace(cells=[SimpleNamespace(text=value)
                                   for value in row]) for row in rows])

    def setUp(self):
        self.overview = self.table([
            ['Contrast', 'Phase', 'Point range', 'CI below 0', 'CI above 0', 'CI contains 0'],
            ['C-A', '1', '-36.50 to 0.00', '8', '0', '8']])
        self.other = self.table([['Rule', 'Finite', '+inf', '-inf'], ['A', '16', '0', '0']])
        self.assumptions = self.table([['Item', 'Definition and evaluation scope'],
                                      ['Alert', 'One flagged shift record']])

    def test_interval_comparison_accepts_both_table_editions(self):
        old = SimpleNamespace(tables=[self.other]*8+[self.overview])
        current = SimpleNamespace(tables=[self.other]*2+[self.assumptions]+[self.other]*6+[self.overview])
        self.assertEqual(verifier._interval_overview_rows(old),
                         verifier._interval_overview_rows(current))
        self.assertEqual(verifier._interval_overview_rows(current)[1][0], 'C-A')

    def test_interval_comparison_retains_changed_values(self):
        changed = self.table([[cell.text for cell in row.cells] for row in self.overview.rows])
        changed.rows[1].cells[3].text = '7'
        self.assertNotEqual(verifier._interval_overview_rows(SimpleNamespace(tables=[self.overview])),
                            verifier._interval_overview_rows(SimpleNamespace(tables=[changed])))

    def test_missing_or_duplicate_interval_overview_is_rejected(self):
        for tables in ([self.other, self.assumptions], [self.overview, self.assumptions, self.overview]):
            with self.subTest(table_count=len(tables)):
                with self.assertRaisesRegex(AssertionError, 'exactly one'):
                    verifier._interval_overview_rows(SimpleNamespace(tables=tables))


class ReportVerificationLifecycle(unittest.TestCase):
    def test_old_success_is_revoked_when_current_manifest_is_corrupt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dest = root/'reports/phase2'
            dest.mkdir(parents=True)
            (dest/'report_manifest.json').write_text('{broken current input', encoding='utf-8')
            certificate = root/'report_check.json'
            certificate.write_text(json.dumps(dict(passed=True, checks=999)), encoding='utf-8')
            with self.assertRaises(json.JSONDecodeError):
                verifier.verify_report(root, root, certificate)
            current = json.loads(certificate.read_text(encoding='utf-8'))
            self.assertFalse(current['passed'])
            self.assertEqual(current['status'], 'failed')
            self.assertEqual(current['error_type'], 'JSONDecodeError')
            self.assertTrue(current['error'])
            self.assertNotIn('checks', current)
            self.assertIn('verifier_sha256', current)


if __name__ == '__main__':
    unittest.main()
