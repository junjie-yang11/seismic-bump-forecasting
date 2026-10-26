"""Reconstruct every printable supplemental row along a separate CSV path."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
STEM='decision_comparison_supplement'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def checks(root,pdf=False):
    out=root/'reports/comparators';counter=0
    def check(condition,label):
        nonlocal counter
        counter+=1
        if not condition:raise AssertionError(label)
    manifest=json.loads((out/'metadata/appendix_manifest.json').read_text(encoding='utf-8'))
    check(sha(root/'reporting/appendix.py')==manifest['generator_sha256'],'current appendix generator')
    for name,digest in manifest['inputs'].items():check(sha(root/name)==digest,'current input '+name)
    for name,digest in manifest['outputs'].items():check(sha(out/name)==digest,'generated artifact '+name)
    read=lambda name:list(csv.DictReader((root/'results/phase2/comparators'/name).open(encoding='utf-8',newline='')))
    ev=read('evaluations.csv');ci=read('intervals.csv')
    check(len(ev)==720 and sum(r['comparison']=='ML-grade' for r in ci)==540,'complete frozen comparison inventory')
    md=(out/(STEM+'.md')).read_text(encoding='utf-8')
    old=(out/'comparator_appendix.md').read_text(encoding='utf-8')
    with ZipFile(out/(STEM+'.docx')) as package:body=ET.fromstring(package.read('word/document.xml')).find('w:body',NS)
    for p in body.findall('w:p',NS):
        text=''.join(p.itertext())
        if text.strip():check(text in md,'Word paragraph in Markdown')
    tables=body.findall('w:tbl',NS)
    check(len(tables)==len(manifest['tables'])==8,'eight complete cost/comparison tables')
    for index,(table,declared) in enumerate(zip(tables,manifest['tables'])):
        comparison='policy-none' if index<4 else 'ML-grade';cost=(5,10,20,50)[index%4]
        if comparison=='policy-none':
            part=[r for r in ev if int(r['cost'])==cost]
            part.sort(key=lambda r:(int(r['fold']) if int(r['fold'])>=0 else 4,r['method'],r['rule']))
        else:
            part=[r for r in ci if r['comparison']==comparison and int(r['cost'])==cost]
            part.sort(key=lambda r:(int(r['fold']) if int(r['fold'])>=0 else 4,r['right_method'],r['rule']))
        expected=[]
        for row in part:
            if comparison=='policy-none':
                matches=[r for r in ci if r['comparison']=='policy-none' and r['left_method']==row['method'] and all(r[k]==row[k] for k in ('rule','cost','fold'))]
                check(len(matches)==1,'one saved interval per policy decision');effect=matches[0]
            else:effect=row
            label='Pooled' if int(row['fold'])<0 else str(int(row['fold'])+1)
            value=f"{float(effect['loss_delta100']):.2f} [{float(effect['ci_low']):.2f}, {float(effect['ci_high']):.2f}]"
            cells=[label,row['method'] if comparison=='policy-none' else row['right_method'],row['rule'],value]
            if comparison=='policy-none':cells += [str(int(float(row[k]))) for k in ('tp','fn','fp','alerts')]+[str(int(float(row['excess']))) if row['excess'] else '-']
            expected.append(cells)
            check('| '+' | '.join(cells)+' |' in md,'complete Markdown supplemental setting')
            check('| '+' | '.join(cells)+' |' in old,'same setting retained in original machine-readable appendix')
        observed=[[''.join(cell.itertext()) for cell in r.findall('w:tc',NS)] for r in table.findall('w:tr',NS)]
        check(observed==[declared['headers']]+expected,'Word table independently reconstructed '+str(index+1))
        check(declared['rows']==expected,'manifest table independently reconstructed '+str(index+1))
    pages=None
    if pdf:
        from pypdf import PdfReader
        reader=PdfReader(out/(STEM+'.pdf'));pages=len(reader.pages)
        check(20<=pages<=70,'complete supplement page range')
        text='\n'.join(p.extract_text() or '' for p in reader.pages)
        for table in manifest['tables']:
            check(table['caption'] in text.replace('\n',' '),'PDF table caption '+table['id'])
            for row in table['rows']:
                check(row[2] in text and row[3].split()[0] in text,'PDF supplemental row identifiers and estimates')
        check(all(float(p.mediabox.width)>float(p.mediabox.height) for p in reader.pages),'landscape supplement')
        check('/Author' not in (reader.metadata or {}),'clean PDF metadata')
    return dict(checks=counter,tables=8,settings=1260,pages=pages,pdf_text_checked=pdf,manifest_sha256=sha(out/'metadata/appendix_manifest.json'),
        scope='All frozen supplemental rows reconstructed from saved CSVs; Word and Markdown compared; optional complete PDF text and orientation. No fitting, threshold selection or resampling.',
        outputs_sha256={name:sha(out/name) for name in (STEM+'.md',STEM+'.docx',STEM+'.pdf')})


def verify(root=ROOT,pdf=False):
    root=Path(root);record=root/'reports/comparators/metadata/appendix_verification.json';record.parent.mkdir(parents=True,exist_ok=True)
    record.write_text(json.dumps(dict(passed=False,status='running')),encoding='utf-8')
    try:
        result=checks(root,pdf);result.update(passed=True,status='passed',completed_at_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)))
        record.write_text(json.dumps(result,indent=2),encoding='utf-8');print('COMPLETE APPENDIX PASSED:',result['checks'],'checks;',result['settings'],'settings');return result
    except (Exception,KeyboardInterrupt) as error:
        record.write_text(json.dumps(dict(passed=False,status='failed',error_type=type(error).__name__,error=str(error))),encoding='utf-8');raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pdf',action='store_true');args=parser.parse_args();verify(pdf=args.pdf)
