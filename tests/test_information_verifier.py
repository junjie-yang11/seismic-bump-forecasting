"""Separate-path arithmetic and success-certificate lifecycle tests."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from phase2.information import verify as verifier


class InformationVerifierTests(unittest.TestCase):
    def test_changed_live_model_input_fails_before_historical_context_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'results/phase2/information';out.mkdir(parents=True)
            protocol=root/'phase2/information/protocol.json';protocol.parent.mkdir(parents=True)
            protocol.write_text('{}')
            data=root/'data.csv';data.write_text('original inputs')
            manifest=dict(status='complete',protocol_sha256=verifier.sha(protocol),
                          inputs_sha256={'data.csv':verifier.sha(data)},code_sha256={})
            (out/'run_manifest.json').write_text(json.dumps(manifest))
            data.write_text('changed inputs')
            with self.assertRaisesRegex(AssertionError,'unchanged inputs_sha256 data.csv'):
                verifier.verify(root)
            self.assertFalse(json.loads((out/'verification.json').read_text())['passed'])

    def test_prior_success_is_revoked_on_missing_current_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'results/phase2/information';out.mkdir(parents=True)
            certificate=out/'verification.json';certificate.write_text(json.dumps({'passed':True,'refit':True}))
            with self.assertRaises(FileNotFoundError):verifier.verify(root,True)
            record=json.loads(certificate.read_text());self.assertFalse(record['passed'])
            self.assertEqual(record['status'],'failed');self.assertEqual(record['error_type'],'FileNotFoundError')

    def test_interrupt_revokes_previous_refit_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(verifier,'checks',side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):verifier.verify(root,True)
            record=json.loads((root/'results/phase2/information/verification.json').read_text())
            self.assertFalse(record['passed']);self.assertEqual(record['error_type'],'KeyboardInterrupt')

    def test_weighted_expectation_matches_explicit_queue_for_boundary_ties(self):
        y=np.array([1.,0.,1.,0.]);g=np.array([1,0,0,0]);s=np.array([.1,.8,.8,.2])
        counts=np.array([[0,2,1,1],[2,0,2,0]])
        expected=verifier.weighted_expectations(y,g,s,counts,[.25,.5,1.])
        for row,weights in enumerate(counts):
            ix=np.repeat(np.arange(4),weights)
            for column,budget in enumerate([.25,.5,1.]):
                direct=verifier.tie_probabilities(g[ix],s[ix],budget)@y[ix]
                self.assertAlmostEqual(expected[row,column],direct)


if __name__=='__main__':unittest.main()
