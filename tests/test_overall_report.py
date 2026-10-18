"""Failed report operations must not retain a previous success certificate."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from reporting import overall, verify_overall


class OverallCertificateTests(unittest.TestCase):
    def test_missing_current_inputs_revoke_previous_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);dest=root/'reports/overall';dest.mkdir(parents=True)
            record=dest/'verification.json';record.write_text(json.dumps({'passed':True}))
            with self.assertRaises(FileNotFoundError):verify_overall.verify(root)
            state=json.loads(record.read_text())
            self.assertFalse(state['passed']);self.assertEqual(state['status'],'failed')
            self.assertEqual(state['error_type'],'FileNotFoundError')

    def test_interrupted_build_revokes_previous_success(self):
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory);record=dest/'verification.json'
            record.write_text(json.dumps({'passed':True}))
            stale_pdf=dest/(overall.STEM+'.pdf');stale_pdf.write_bytes(b'%PDF-stale')
            with patch.object(overall,'DEST',dest),patch.object(overall,'overview_figure',side_effect=RuntimeError('interrupted render')):
                with self.assertRaisesRegex(RuntimeError,'interrupted render'):overall.build()
            state=json.loads(record.read_text())
            self.assertFalse(state['passed']);self.assertEqual(state['status'],'failed')
            self.assertEqual(state['error'],'interrupted render')
            self.assertFalse(stale_pdf.exists())


if __name__=='__main__':unittest.main()
