"""A failed source check must not retain a previous matched-source claim."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phase1 import audit_source


class SourceAuditTests(unittest.TestCase):
    def test_corrupt_current_source_invalidates_previous_match(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            (root / 'data/seismic-bumps.csv').write_text('class\n0\n', encoding='utf-8')
            output = root / 'results/phase1/source_audit.json'
            output.parent.mkdir(parents=True)
            output.write_text(json.dumps({'order_preserving_dedup_matches': True}), encoding='utf-8')
            source = root / 'invalid.arff'
            source.write_text('invalid source fixture', encoding='utf-8')
            with patch.object(audit_source, 'ROOT', root):
                with self.assertRaises(Exception):
                    audit_source.audit(source)
            result = json.loads(output.read_text(encoding='utf-8'))
            self.assertFalse(result['order_preserving_dedup_matches'])
            self.assertEqual(result['status'], 'failed')
            self.assertIn('error_type', result)


if __name__ == '__main__':
    unittest.main()
