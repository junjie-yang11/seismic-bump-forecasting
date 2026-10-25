"""Preserve run-time context while allowing separately verified paper revisions.

The original run manifest remains immutable. Only the explicitly named gap-summary authoring/checking entry points and the two older presentation
directories can use historical snapshots. Model inputs, fitted evidence and
all other protected files continue to be checked against their current bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


ARCHIVE = 'results/phase2/information/historical_context.zip'
MANIFEST = 'results/phase2/information/run_manifest.json'
ARCHIVED_MANIFEST = '_original_run_manifest.json'
DERIVED_CONTEXT = frozenset({
    'reports/README.md',
    'phase1/verify_additions.py',
    'phase1/run_research.py',
})
PRESENTATION_PREFIXES = ('reports/overall/', 'reports/ranking/')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def context_paths(manifest):
    """A bounded projection of the *original* protected-file inventory."""
    return {name for name in manifest['protected_sha256']
            if name in DERIVED_CONTEXT or name.startswith(PRESENTATION_PREFIXES)}


def create_archive(baseline_tar, destination):
    """Archive original bytes; reject a baseline inconsistent with its manifest.

    This is an authoring utility, never a way to regenerate a failed check's
    expected hashes from the current workspace. Existing snapshots are retained.
    """
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('Historical context archive already exists')
    with tarfile.open(baseline_tar, 'r') as source:
        manifest_bytes = source.extractfile(MANIFEST).read()
        manifest = json.loads(manifest_bytes)
        contents = {ARCHIVED_MANIFEST: manifest_bytes}
        for name in sorted(context_paths(manifest)):
            content = source.extractfile(name).read()
            if digest(content) != manifest['protected_sha256'][name]:
                raise ValueError('Baseline disagrees with original protected hash: ' + name)
            contents[name] = content
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ZipFile(destination, 'x', compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for name, content in sorted(contents.items()):
                entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.compress_type = ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, content, compresslevel=9)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return dict(files=len(contents) - 1, archive_sha256=digest(destination.read_bytes()))


def verify_protected(root, manifest, check):
    """Verify immutable computation live and explicitly mutable context at origin.

    An archive is eligible only for the exact original manifest it contains.
    A later independent experiment run is checked against all its live protected
    files, so an older presentation snapshot never exempts a newly protected file.
    """
    root = Path(root)
    snapshot = root / ARCHIVE
    expected_context = context_paths(manifest)
    archived = {}
    bound = False
    if snapshot.exists():
        with ZipFile(snapshot) as archive:
            names = archive.namelist()
            check(len(names) == len(set(names)), 'no duplicate historical archive members')
            original_bytes = archive.read(ARCHIVED_MANIFEST)
            original = json.loads(original_bytes)
            expected_members = context_paths(original) | {ARCHIVED_MANIFEST}
            check(set(names) == expected_members, 'exact bounded historical context inventory')
            for name in sorted(context_paths(original)):
                content = archive.read(name)
                check(digest(content) == original['protected_sha256'][name],
                      'historical original-byte hash ' + name)
                archived[name] = content
            bound = original_bytes == (root / MANIFEST).read_bytes()
    live_checked = 0
    changed = []
    for name, expected in manifest['protected_sha256'].items():
        if bound and name in expected_context:
            check(name in archived and digest(archived[name]) == expected,
                  'bound historical context ' + name)
            live = root / name
            if not live.is_file() or digest(live.read_bytes()) != expected:
                changed.append(name)
        else:
            check(digest((root / name).read_bytes()) == expected,
                  'unchanged live protected evidence ' + name)
            live_checked += 1
    return dict(
        archive_sha256=digest(snapshot.read_bytes()) if snapshot.exists() else None,
        archive_bound_to_current_run=bound,
        historical_context_files=len(expected_context) if bound else 0,
        live_protected_files=live_checked,
        changed_historical_context=sorted(changed),
        helper_sha256=digest(Path(__file__).read_bytes()),
        scope=('Original run-time context bytes verified from the bounded archive; '
               'current presentation and the separately added three-model gap output require their own checks. '
               'All other protected evidence, and all model inputs/code/outputs, remain live checks.')
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-tar', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    arguments = parser.parse_args()
    print(json.dumps(create_archive(arguments.baseline_tar, arguments.root / ARCHIVE), indent=2))
