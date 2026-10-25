"""Historical presentation snapshots never exempt live computational evidence."""
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from phase2.information import provenance


class HistoricalContextTests(unittest.TestCase):
    def check(self, condition, message):
        if not condition:
            raise AssertionError(message)

    def fixture(self, root):
        files = {
            'reports/overall/paper.md': b'Original paper',
            'phase1/run_research.py': b'Original analysis authoring',
            'results/phase1/gap_attenuation.csv': b'Original two-model summary',
            'src/boosting.py': b'Actual model implementation',
            'results/phase2/predictions.csv': b'Actual predictions',
        }
        manifest = {'protected_sha256': {p: provenance.digest(b) for p, b in files.items()}}
        files[provenance.MANIFEST] = json.dumps(manifest, indent=2).encode()
        baseline = root / 'baseline.tar'
        with tarfile.open(baseline, 'w') as archive:
            for name, data in files.items():
                info = tarfile.TarInfo(name); info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        provenance.create_archive(baseline, root / provenance.ARCHIVE)
        return manifest

    def test_changed_paper_is_checked_at_origin_and_reported_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); manifest = self.fixture(root)
            original_manifest = (root / provenance.MANIFEST).read_bytes()
            (root / 'reports/overall/paper.md').write_bytes(b'Revised paper')
            result = provenance.verify_protected(root, manifest, self.check)
            self.assertTrue(result['archive_bound_to_current_run'])
            self.assertEqual(result['changed_historical_context'], ['reports/overall/paper.md'])
            self.assertEqual(result['historical_context_files'], 2)
            self.assertEqual(result['live_protected_files'], 3)
            self.assertEqual((root / provenance.MANIFEST).read_bytes(), original_manifest)

    def test_unlisted_changed_model_implementation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); manifest = self.fixture(root)
            (root / 'src/boosting.py').write_bytes(b'Changed computation')
            with self.assertRaisesRegex(AssertionError, 'live protected evidence src/boosting.py'):
                provenance.verify_protected(root, manifest, self.check)

    def test_original_gap_summary_remains_live_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);manifest=self.fixture(root)
            (root/'results/phase1/gap_attenuation.csv').write_bytes(b'Changed locked summary')
            with self.assertRaisesRegex(AssertionError,'live protected evidence results/phase1/gap_attenuation.csv'):
                provenance.verify_protected(root,manifest,self.check)

    def test_changed_predictions_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); manifest = self.fixture(root)
            (root / 'results/phase2/predictions.csv').write_bytes(b'Replaced evidence')
            with self.assertRaisesRegex(AssertionError, 'live protected evidence results/phase2/predictions.csv'):
                provenance.verify_protected(root, manifest, self.check)

    def test_corrupt_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); manifest = self.fixture(root); path = root / provenance.ARCHIVE
            with ZipFile(path) as archive:
                contents = {name: archive.read(name) for name in archive.namelist()}
            contents['reports/overall/paper.md'] = b'Fabricated historical paper'
            with ZipFile(path, 'w', compression=ZIP_DEFLATED) as archive:
                for name, data in contents.items(): archive.writestr(name, data)
            with self.assertRaisesRegex(AssertionError, 'historical original-byte hash'):
                provenance.verify_protected(root, manifest, self.check)

    def test_arbitrary_computational_member_cannot_enter_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); manifest = self.fixture(root)
            with ZipFile(root / provenance.ARCHIVE, 'a') as archive:
                archive.writestr('src/boosting.py', b'Actual model implementation')
            with self.assertRaisesRegex(AssertionError, 'bounded historical context inventory'):
                provenance.verify_protected(root, manifest, self.check)

    def test_new_experiment_manifest_receives_live_strict_checking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); manifest = self.fixture(root)
            manifest['new_run'] = True
            (root / provenance.MANIFEST).write_text(json.dumps(manifest))
            (root / 'reports/overall/paper.md').write_bytes(b'Changed after new run')
            with self.assertRaisesRegex(AssertionError, 'live protected evidence reports/overall/paper.md'):
                provenance.verify_protected(root, manifest, self.check)

    def test_archive_creation_rejects_baseline_with_wrong_recorded_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            baseline = root / 'inconsistent.tar'
            content = b'Changed paper'
            manifest = {'protected_sha256': {'reports/overall/paper.md': provenance.digest(b'Original')}}
            with tarfile.open(baseline, 'w') as archive:
                for name, data in [(provenance.MANIFEST, json.dumps(manifest).encode()), ('reports/overall/paper.md', content)]:
                    info = tarfile.TarInfo(name); info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
            with self.assertRaisesRegex(ValueError, 'Baseline disagrees'):
                provenance.create_archive(baseline, root / 'rejected.zip')
            self.assertFalse((root / 'rejected.zip').exists())


if __name__ == '__main__':
    unittest.main()
