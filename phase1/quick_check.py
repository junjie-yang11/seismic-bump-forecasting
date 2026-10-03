"""Check published evidence in a disposable copy without fitting research models.

The existing verifiers write their own records. Isolating those writes preserves
the checkout's full-replay provenance and the published papers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ('src', 'phase1', 'phase2', 'tests', 'results', 'reports')
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_navigation(root):
    guides = [root / 'README.md'] + list((root / 'docs').glob('*.md'))
    guides += [root / folder / 'README.md' for folder in FOLDERS if (root / folder / 'README.md').exists()]
    guides += list((root / 'reports').rglob('*.md')) + list((root / 'results').rglob('README.md'))
    count = 0
    for guide in guides:
        for target in re.findall(r'\]\(([^)]+)\)', guide.read_text(encoding='utf-8')):
            if '://' in target or target.startswith(('mailto:', '#')):
                continue
            path = target.split('#', 1)[0]
            if path and not (guide.parent / path).exists():
                raise AssertionError('Missing local link: %s -> %s' % (guide.relative_to(root), target))
            count += 1
    return count


def check_stage2_document(root):
    dest = root / 'reports/phase2'
    manifest = json.loads((dest / 'report_manifest.json').read_text(encoding='utf-8'))
    for name, digest in manifest['inputs'].items():
        if sha(root / 'results/phase2' / name) != digest:
            raise AssertionError('Stage 2 report input changed: ' + name)
    if sha(root / 'phase2/report.py') != manifest['generator_sha256']:
        raise AssertionError('Stage 2 paper generator changed after reporting')
    md = (dest / 'phase2_threshold_transfer_report.md').read_text(encoding='utf-8')
    with ZipFile(dest / 'phase2_threshold_transfer_report.docx') as package:
        body = ET.fromstring(package.read('word/document.xml')).find('w:body', NS)
    count = 0
    for paragraph in body.findall('w:p', NS):
        pieces = []
        for node in paragraph.iter():
            if node.tag == '{%s}t' % NS['w']:
                pieces.append(node.text or '')
            elif node.tag == '{%s}br' % NS['w']:
                pieces.append('\n')
        text = ''.join(pieces)
        if text and text not in md:
            raise AssertionError('Stage 2 Word paragraph differs from manuscript')
        count += 1
    for table in body.findall('w:tbl', NS):
        for row in table.findall('w:tr', NS):
            cells = []
            for cell in row.findall('w:tc', NS):
                pieces = []
                for node in cell.iter():
                    if node.tag == '{%s}t' % NS['w']:
                        pieces.append(node.text or '')
                    elif node.tag == '{%s}br' % NS['w']:
                        pieces.append('<br>')
                cells.append(''.join(pieces))
            if '| ' + ' | '.join(cells) + ' |' not in md:
                raise AssertionError('Stage 2 Word table differs from manuscript')
            count += 1
    for path in (root / 'reports').rglob('*.pdf'):
        with path.open('rb') as stream:
            header = stream.read(5)
        if header != b'%PDF-' or path.stat().st_size < 10000:
            raise AssertionError('Missing or invalid PDF export: ' + path.name)
    return count


def run(proxy=None):
    if sys.version_info < (3, 12):
        raise RuntimeError('Use Python 3.12 with requirements/requirements-research.txt')
    started = time.perf_counter()
    files = [p for folder in FOLDERS for p in (ROOT / folder).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    original = {p: sha(p) for p in files}
    steps = (
        ('Behavior tests', ['-m', 'unittest', 'discover', '-s', 'tests']),
        ('Decision tests', ['-m', 'unittest', 'phase2.tests']),
        ('Stage 1 evidence and Word agreement', ['-m', 'phase1.verify_results', '--reports']),
        ('Stage 2 saved decisions and block arithmetic', ['-m', 'phase2.verify']),
        ('Supplementary decision accounting', ['-m', 'phase2.verify_supplement']),
        ('Independent formula reconstruction', ['-m', 'phase1.verify_formulae']),
    )
    with tempfile.TemporaryDirectory(prefix='seismic-evidence-') as directory:
        snapshot = Path(directory)
        for folder in FOLDERS:
            shutil.copytree(ROOT / folder, snapshot / folder,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (snapshot / 'data').mkdir()
        mirror = ROOT / 'data/seismic-bumps.csv'
        if mirror.exists():
            shutil.copy2(mirror, snapshot / 'data/seismic-bumps.csv')
        env = os.environ.copy()
        env.pop('PYTHONPATH', None)
        env['PYTHONIOENCODING'] = 'utf-8'
        if proxy:
            env['HTTPS_PROXY'] = proxy
        for label, arguments in steps:
            mark = time.perf_counter()
            print('\nCHECK: ' + label, flush=True)
            subprocess.run([sys.executable, '-B', '-u'] + arguments,
                           cwd=snapshot, env=env, check=True)
            print('Completed in %.2f seconds' % (time.perf_counter() - mark), flush=True)
    navigation = check_navigation(ROOT)
    document = check_stage2_document(ROOT)
    if any(sha(path) != digest for path, digest in original.items()):
        raise AssertionError('A published source, result or report changed during quick checking')
    print('\nQUICK CHECK PASSED: %d links and %d Stage 2 Word items; %.2f seconds.' %
          (navigation, document, time.perf_counter() - started))
    print('Published sources/results/reports preserved. No full research-model replay or PDF layout check was performed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proxy', help='Optional HTTPS download proxy when the mirror cache is absent')
    try:
        run(**vars(parser.parse_args()))
    except (AssertionError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print('QUICK CHECK FAILED: ' + str(error), file=sys.stderr)
        sys.exit(1)
