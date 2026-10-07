"""A failed verification must not inherit a prior successful certificate."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phase2 import verify as core
from phase2 import verify_supplement as supplementary


class VerificationLifecycleTests(unittest.TestCase):
    def test_core_failure_invalidates_previous_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            certificate = out / 'verification.json'
            certificate.write_text(json.dumps({'passed': True, 'replay': True}))
            with patch.object(core, 'OUT', out), patch.object(core, 'load', side_effect=RuntimeError('test source failure')):
                with self.assertRaisesRegex(RuntimeError, 'test source failure'):
                    core.verify(replay=True)
            record = json.loads(certificate.read_text())
            self.assertFalse(record['passed'])
            self.assertFalse(record['replay'])
            self.assertEqual(record['status'], 'failed')

    def test_supplement_failure_invalidates_previous_certificate(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            certificate = out / 'supplement_verification.json'
            certificate.write_text(json.dumps({'passed': True}))
            source = supplementary.ROOT / 'phase2/supplement.py'
            manifest = {'inputs': {}, 'outputs': {}, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
            (out / 'supplement_manifest.json').write_text(json.dumps(manifest))
            with patch.object(supplementary, 'OUT', out), patch.object(supplementary.pd, 'read_csv', side_effect=RuntimeError('test evidence failure')):
                with self.assertRaisesRegex(RuntimeError, 'test evidence failure'):
                    supplementary.verify()
            record = json.loads(certificate.read_text())
            self.assertFalse(record['passed'])
            self.assertEqual(record['status'], 'failed')
