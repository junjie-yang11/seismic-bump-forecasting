"""A failed source check must not retain a previous matched-source claim."""
import json
import io
import hashlib
from contextlib import redirect_stdout
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

from phase1 import audit_source


class SourceAuditTests(unittest.TestCase):
    # Synthetic unit fixtures only; these are not research data or report results.
    ARFF = (b'@relation audit_fixture\n@attribute seismic {a,b}\n'
            b'@attribute seismoacoustic {a,b}\n@attribute shift {W,N}\n'
            b'@attribute ghazard {a,b}\n@attribute class {0,1}\n'
            b'@data\na,a,W,a,0\nb,b,N,b,1\na,a,W,a,0\n')

    def seed_previous_audit(self, root):
        (root / 'data').mkdir()
        (root / 'data/seismic-bumps.csv').write_text(
            'seismic,seismoacoustic,shift,ghazard,class\na,a,W,a,0\nb,b,N,b,1\n', encoding='utf-8')
        output = root / 'results/phase1/source_audit.json'
        output.parent.mkdir(parents=True)
        output.write_text(json.dumps(dict(status='passed', order_preserving_dedup_matches=True)), encoding='utf-8')
        mapping = output.parent / 'source_row_mapping.csv'
        mapping.write_text('mirror_row_0based,uci_row_1based\n0,1\n1,2\n', encoding='utf-8')
        return output, mapping

    def zip_payload(self, name='seismic-bumps.arff'):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, 'w') as archive:
            archive.writestr(name, self.ARFF)
        return payload.getvalue()

    def assert_acquisition_failure(self, mode, error_type):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);output, mapping = self.seed_previous_audit(root)
            previous_mapping = mapping.read_bytes();opener = Mock()
            if mode in ('network', 'interrupt'):
                def fail(*args, **kwargs):
                    running = json.loads(output.read_text(encoding='utf-8'))
                    self.assertEqual(running['status'], 'running')
                    self.assertFalse(running['order_preserving_dedup_matches'])
                    raise error_type('simulated acquisition failure')
                opener.open.side_effect = fail
            else:
                payload = (b'not a ZIP' if mode == 'zip' else
                           self.zip_payload('wrong-member.arff') if mode == 'member' else self.zip_payload())
                opener.open.return_value = io.BytesIO(payload)
            with patch.object(audit_source, 'ROOT', root), patch.object(audit_source.urllib.request, 'build_opener', return_value=opener):
                if mode == 'cache':
                    with patch.object(Path, 'write_bytes', side_effect=PermissionError('simulated cache write failure')):
                        with self.assertRaises(error_type):audit_source.main([])
                else:
                    with self.assertRaises(error_type):audit_source.main([])
            result = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(result['status'], 'failed')
            self.assertFalse(result['order_preserving_dedup_matches'])
            self.assertEqual(result['error_type'], error_type.__name__)
            self.assertTrue(result['error'])
            self.assertEqual(mapping.read_bytes(), previous_mapping)

    def test_download_failure_revokes_previous_success(self):
        self.assert_acquisition_failure('network', OSError)

    def test_bad_zip_revokes_previous_success(self):
        self.assert_acquisition_failure('zip', zipfile.BadZipFile)

    def test_missing_archive_member_revokes_previous_success(self):
        self.assert_acquisition_failure('member', KeyError)

    def test_cache_write_failure_revokes_previous_success(self):
        self.assert_acquisition_failure('cache', PermissionError)

    def test_interrupted_download_revokes_previous_success(self):
        self.assert_acquisition_failure('interrupt', KeyboardInterrupt)

    def test_downloaded_and_supplied_source_produce_identical_success_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);output, _ = self.seed_previous_audit(root)
            source = root / 'provided.arff';source.write_bytes(self.ARFF)
            with patch.object(audit_source, 'ROOT', root), redirect_stdout(io.StringIO()):
                audit_source.main(['--source', str(source)])
                names = ('source_audit.json', 'source_row_mapping.csv', 'source_duplicates.csv')
                supplied = {name:(output.parent / name).read_bytes() for name in names}
                opener = Mock();opener.open.return_value = io.BytesIO(self.zip_payload())
                with patch.object(audit_source.urllib.request, 'build_opener', return_value=opener):
                    audit_source.main([])
                downloaded = {name:(output.parent / name).read_bytes() for name in names}
            self.assertEqual(downloaded, supplied)
            result = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual((result['original_rows'], result['mirror_rows'], result['removed_rows']), (3, 2, 1))
            self.assertEqual(result['arff_sha256'], hashlib.sha256(self.ARFF).hexdigest())
            self.assertEqual(result['status'], 'passed')

    def test_explicit_proxy_is_used_for_source_download(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);self.seed_previous_audit(root)
            opener = Mock();opener.open.return_value = io.BytesIO(self.zip_payload())
            with patch.object(audit_source, 'ROOT', root), redirect_stdout(io.StringIO()), \
                 patch.object(audit_source.urllib.request, 'build_opener', return_value=opener) as build:
                audit_source.main(['--proxy', 'http://127.0.0.1:9999'])
            self.assertEqual(build.call_args.args[0].proxies, {'https':'http://127.0.0.1:9999'})

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
