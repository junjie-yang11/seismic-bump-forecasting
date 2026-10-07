"""A malformed current report input must revoke an earlier success."""
import json
from pathlib import Path
import tempfile
import unittest

from phase2 import verify_report as verifier


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
