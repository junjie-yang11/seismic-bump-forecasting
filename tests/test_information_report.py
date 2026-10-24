"""New supplemental documents must not inherit stale successful checks."""
import json
from pathlib import Path
import tempfile
import unittest
from reporting import information,verify_information


class InformationReportLifecycleTests(unittest.TestCase):
    def test_failed_build_removes_stale_pdf_and_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'reports/information';out.mkdir(parents=True)
            state=out/'verification.json';state.write_text(json.dumps({'passed':True}))
            pdf=out/(information.STEM+'.pdf');pdf.write_bytes(b'%PDF-stale')
            with self.assertRaises(FileNotFoundError):information.build(root)
            result=json.loads(state.read_text())
            self.assertFalse(result['passed']);self.assertEqual(result['status'],'failed')
            self.assertFalse(pdf.exists())

    def test_failed_check_replaces_stale_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'reports/information';out.mkdir(parents=True)
            state=out/'verification.json';state.write_text(json.dumps({'passed':True}))
            with self.assertRaises(FileNotFoundError):verify_information.verify(root)
            result=json.loads(state.read_text())
            self.assertFalse(result['passed']);self.assertEqual(result['status'],'failed')
            self.assertEqual(result['error_type'],'FileNotFoundError')


if __name__=='__main__':unittest.main()
