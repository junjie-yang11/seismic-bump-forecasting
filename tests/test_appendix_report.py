"""Complete supplement failures cannot inherit an old success certificate."""
import json
from pathlib import Path
import tempfile
import unittest
from reporting import appendix,verify_appendix


class AppendixLifecycleTests(unittest.TestCase):
    def test_missing_inputs_revoke_old_build_and_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'reports/overall';out.mkdir(parents=True)
            record=out/'appendix_verification.json';record.write_text(json.dumps({'passed':True}))
            pdf=out/(appendix.STEM+'.pdf');pdf.write_bytes(b'%PDF-old')
            with self.assertRaises(FileNotFoundError):appendix.build(root)
            self.assertFalse(json.loads(record.read_text())['passed']);self.assertFalse(pdf.exists())

    def test_missing_manifest_revokes_old_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'reports/overall';out.mkdir(parents=True)
            record=out/'appendix_verification.json';record.write_text(json.dumps({'passed':True}))
            with self.assertRaises(FileNotFoundError):verify_appendix.verify(root)
            self.assertFalse(json.loads(record.read_text())['passed'])


if __name__=='__main__':unittest.main()
