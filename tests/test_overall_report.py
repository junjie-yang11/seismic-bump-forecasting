"""Failed report operations must not retain a previous success certificate."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from reporting import overall, verify_overall


class OverallCertificateTests(unittest.TestCase):
    def test_native_equations_do_not_exempt_adjacent_ordinary_text(self):
        import xml.etree.ElementTree as ET
        p=ET.fromstring('<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:r><w:t>Ordinary text still checked</w:t></w:r><m:oMath><m:r><m:t>math checked separately</m:t></m:r></m:oMath></w:p>')
        self.assertEqual(verify_overall.ordinary_paragraph_text(p),'Ordinary text still checked')

    def test_equal_counts_do_not_merge_different_alarm_decisions(self):
        records=[dict(method='XGBoost',fold='0',row='1',y='1',C_b01_r10='True',C_b05_r10='False'),
                 dict(method='XGBoost',fold='0',row='2',y='1',C_b01_r10='False',C_b05_r10='True')]
        self.assertNotEqual(overall.decision_signature(records,0,('XGBoost',),(.01,)),
                            overall.decision_signature(records,0,('XGBoost',),(.05,)))

    def test_grouped_contrast_requires_all_comparator_decisions_to_match(self):
        records=[dict(method='XGBoost',fold='0',row='1',y='1',C_b01_r10='False',C_b05_r10='False'),
                 dict(method='ghazard',fold='0',row='1',y='1',C_b01_r10='False',C_b05_r10='True')]
        self.assertEqual(overall.decision_signature(records,0,('XGBoost',),(.01,)),
                         overall.decision_signature(records,0,('XGBoost',),(.05,)))
        self.assertNotEqual(overall.decision_signature(records,0,('XGBoost','ghazard'),(.01,)),
                            overall.decision_signature(records,0,('XGBoost','ghazard'),(.05,)))

    def test_signature_aligns_rows_and_keeps_record_blocks_separate(self):
        records=[dict(method='XGBoost',fold='0',row='1',y='1',C_b01_r10='False'),
                 dict(method='XGBoost',fold='1',row='2',y='0',C_b01_r10='False')]
        self.assertEqual(overall.decision_signature(records,0,('XGBoost',),(.01,)),
                         overall.decision_signature(list(reversed(records)),0,('XGBoost',),(.01,)))
        self.assertNotEqual(overall.decision_signature(records,0,('XGBoost',),(.01,)),
                            overall.decision_signature(records,1,('XGBoost',),(.01,)))

    def test_missing_current_inputs_revoke_previous_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);dest=root/'reports/overall';dest.mkdir(parents=True)
            record=dest/'metadata/verification.json';record.parent.mkdir(parents=True,exist_ok=True);record.write_text(json.dumps({'passed':True}))
            with self.assertRaises(FileNotFoundError):verify_overall.verify(root)
            state=json.loads(record.read_text())
            self.assertFalse(state['passed']);self.assertEqual(state['status'],'failed')
            self.assertEqual(state['error_type'],'FileNotFoundError')

    def test_interrupted_build_revokes_previous_success(self):
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory);record=dest/'metadata/verification.json';record.parent.mkdir(parents=True,exist_ok=True)
            record.write_text(json.dumps({'passed':True}))
            stale_pdf=dest/(overall.STEM+'.pdf');stale_pdf.write_bytes(b'%PDF-stale')
            with patch.object(overall,'DEST',dest),patch.object(overall,'overview_figure',side_effect=RuntimeError('interrupted render')):
                with self.assertRaisesRegex(RuntimeError,'interrupted render'):overall.build()
            state=json.loads(record.read_text())
            self.assertFalse(state['passed']);self.assertEqual(state['status'],'failed')
            self.assertEqual(state['error'],'interrupted render')
            self.assertFalse(stale_pdf.exists())


if __name__=='__main__':unittest.main()
