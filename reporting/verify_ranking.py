"""Check the short ranking report against saved computations and document content."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
from datetime import datetime,timezone
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
STEM='within_grade_ranking_pilot'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def checks(root,pdf_text):
    out=root/'reports/ranking';count=0
    def check(condition,message):
        nonlocal count
        count+=1
        if not condition:raise AssertionError(message)
    manifest=json.loads((out/'report_manifest.json').read_text(encoding='utf-8'))
    check(sha(root/'reporting/ranking.py')==manifest['generator_sha256'],'current pilot report generator')
    check(sha(root/'reporting/overall.py')==manifest['writer_sha256'],'current shared Word writer')
    for path,digest in manifest['inputs'].items():check(sha(root/path)==digest,'source '+path)
    for path,digest in manifest['outputs'].items():check(sha(out/path)==digest,'output '+path)
    md=(out/(STEM+'.md')).read_text(encoding='utf-8')
    with ZipFile(out/(STEM+'.docx')) as package:
        body=ET.fromstring(package.read('word/document.xml')).find('w:body',NS)
        relationships=ET.fromstring(package.read('word/_rels/document.xml.rels'))
        core=ET.fromstring(package.read('docProps/core.xml'))
        for node in core:
            if node.tag.rsplit('}',1)[-1] in ('creator','lastModifiedBy'):check(not node.text,'clean author metadata')
    for p in body.findall('w:p',NS):
        text=''.join(p.itertext())
        if text.strip():check(text in md,'Word paragraph equals manuscript')
    word_tables=[[[''.join(c.itertext()) for c in row.findall('w:tc',NS)] for row in t.findall('w:tr',NS)] for t in body.findall('w:tbl',NS)]
    check(len(word_tables)==len(manifest['tables'])==2,'two complete pilot tables')
    for actual,table in zip(word_tables,manifest['tables']):
        check(actual==[table['headers']]+table['rows'],'Word table equals declared content')
        lines=['| '+' | '.join(table['headers'])+' |','| '+' | '.join(['---']*len(table['headers']))+' |']
        lines += ['| '+' | '.join(row)+' |' for row in table['rows']]
        check('\n'.join(lines) in md,'GitHub table block')
    def read(name):return list(csv.DictReader((root/'results/phase2/ranking'/name).open(encoding='utf-8',newline='')))
    ev=read('evaluations.csv');ci=read('intervals.csv')
    def one(rows,**query):
        part=[r for r in rows if all(float(r[k])==v if isinstance(v,(int,float)) else r[k]==v for k,v in query.items())]
        check(len(part)==1,'unique ranking evidence row');return part[0]
    def num(x):return f'{float(x):.2f}'
    def effect(r):return num(r['extra_tp'])+' ['+num(r['ci_low'])+', '+num(r['ci_high'])+']'
    expected=[]
    for fold in (0,1,2,3,-1):
        for budget in (.01,.05,.1,.2):
            e=one(ev,fold=fold,budget=budget);r=one(ci,fold=fold,budget=budget,method='grade_ml')
            expected.append(['Pooled' if fold<0 else str(fold+1),f'{100*budget:.0f}%',e['k'],num(e['expected_random_tp']),e['grade_ml_tp'],effect(r)])
    check(manifest['tables'][0]['rows']==expected,'all primary record block/cohort rows')
    expected=[]
    for budget in (.01,.05,.1,.2):
        e=one(ev,fold=-1,budget=budget);r=one(ci,fold=-1,budget=budget,method='global_ml')
        expected.append([f'{100*budget:.0f}%',e['k'],e['grade_ml_tp'],e['global_ml_tp'],effect(r)])
    check(manifest['tables'][1]['rows']==expected,'auxiliary global ranking rows')
    check(manifest['tables'][1]['headers'][-1]=='Global TP - grade-random E(TP) [95% CI]',
          'auxiliary header identifies the random expectation comparator')
    check('Extra TP is measured against the grade-random expectation, not against Grade+ML.' in manifest['tables'][1]['caption'],
          'auxiliary caption distinguishes the two possible contrasts')
    source_rows=read('rows.csv');allocation_rows=read('allocations.csv')
    queue=[r for r in source_rows if r['fold']=='0']
    groups={grade:[r for r in queue if r['grade_code']==grade] for grade in ('a','b')}
    positives={grade:sum(int(float(r['y'])) for r in group) for grade,group in groups.items()}
    selected={grade:[r for r in group if r['grade_ml_b20']=='True'] for grade,group in groups.items()}
    slots={grade:len(group) for grade,group in selected.items()}
    detected={grade:sum(int(float(r['y'])) for r in group) for grade,group in selected.items()}
    for grade,code in (('a',0),('b',1)):
        q=one(allocation_rows,fold=0,budget=.2,grade=code)
        check((int(q['n']),int(q['positives']),int(q['k']))==(len(groups[grade]),positives[grade],slots[grade]),
              'example allocations agree with saved row decisions: '+grade)
    check(slots['b']==len(groups['b']) and 0<slots['a']<len(groups['a']),'full b and partial a inclusion')
    baseline=sum(slots[grade]*positives[grade]/len(groups[grade]) for grade in groups)
    interval=one(ci,fold=0,budget=.2,method='grade_ml')
    expected_example=dict(n=len(queue),k=math.floor(.2*len(queue)),a_n=len(groups['a']),b_n=len(groups['b']),
        a_slots=slots['a'],b_slots=slots['b'],a_positives=positives['a'],b_positives=positives['b'],
        a_ml_tp=detected['a'],b_ml_tp=detected['b'],a_random_expected_tp=slots['a']*positives['a']/len(groups['a']),
        total_ml_tp=sum(detected.values()),total_random_expected_tp=baseline,extra_tp=sum(detected.values())-baseline,
        ci_low=float(interval['ci_low']),ci_high=float(interval['ci_high']))
    check(set(manifest['worked_allocation'])==set(expected_example),'complete worked-example fields')
    for name,value in expected_example.items():
        check(math.isclose(manifest['worked_allocation'][name],value,rel_tol=0,abs_tol=1e-12),'row-derived example '+name)
    expression=f'{slots["a"]}*{positives["a"]}/{len(groups["a"])} = {num(expected_example["a_random_expected_tp"])}'
    check(expression in md and effect(interval) in md,'worked arithmetic and conditional interval in manuscript')
    from reporting.edition import edition_url
    version='e4c517b6f4b9671aff7b55f6886eb0f8bfaf9535';base='https://github.com/junjie-yang11/seismic-bump-forecasting'
    sources=[['Repository source snapshot',f'{base}/tree/{version}'],
        ['Pilot protocol',f'{base}/blob/{version}/phase2/ranking/protocol.json'],
        ['Ranking code',f'{base}/tree/{version}/phase2/ranking'],
        ['Saved evidence and verification guide',f'{base}/blob/{version}/results/phase2/ranking/README.md'],
        ['Numerical verifier',f'{base}/blob/{version}/phase2/ranking/verify.py'],
        ['Integrated report',edition_url('reports/overall/integrated_research_report.pdf')]]
    check(manifest['source_snapshot']==version and manifest['source_links']==sources,'fixed source snapshot and destinations')
    targets={r.get('Id'):r.get('Target') for r in relationships if r.get('Type','').endswith('/hyperlink') and r.get('TargetMode')=='External'}
    word_links=[[''.join(link.itertext()),targets.get(link.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'))]
                for link in body.findall('.//w:hyperlink',NS)]
    check(word_links==sources,'native Word hyperlinks match the fixed source labels and targets')
    for label,url in sources:check('['+label+']('+url+')' in md,'clickable Markdown source: '+label)
    for statement in ('same total and grade-specific allocations','not an isolated sensor effect','not validation of real-time dispatch',
                      'reallocated and reranked','distinct from the block-bootstrap uncertainty','That study has not been performed'):
        check(statement in md,'scope: '+statement)
    for bad in ('TODO','TBD','PLACEHOLDER','Scientific Agent Skills'):check(bad not in md,'no placeholder/tool bibliography')
    pdf=out/(STEM+'.pdf');check(pdf.read_bytes().startswith(b'%PDF-'),'valid exported PDF')
    pages=None
    if pdf_text:
        from pypdf import PdfReader
        reader=PdfReader(pdf);pages=len(reader.pages)
        check(2<=pages<=6,'short pilot report page range')
        check('/Author' not in (reader.metadata or {}),'clean PDF author metadata')
        text='\n'.join(p.extract_text() or '' for p in reader.pages)
        compact=re.sub(r'\s+','',text)
        check(re.sub(r'\s+','',expression) in compact,'worked arithmetic exported to PDF')
        pdf_targets=set()
        for page in reader.pages:
            for annotation in page.get('/Annots',[]):
                action=annotation.get_object().get('/A')
                if action:pdf_targets.add(str(action.get_object().get('/URI','')))
        for label,url in sources:check(url in pdf_targets,'clickable PDF source: '+label)
        check('GlobalTP-grade-randomE(TP)[95%CI]' in compact,'PDF auxiliary header names the random baseline')
        check('ExtraTPismeasuredagainstthegrade-randomexpectation,notagainstGrade+ML.' in compact,
              'PDF auxiliary caption identifies the subtraction baseline')
        for table in manifest['tables']:
            for row in table['rows']:
                for cell in row:
                    for number in re.findall(r'\b\d+\.\d+\b',cell):check(number in text,'PDF table number '+number)
    return dict(checks=count,tables=2,pages=pages,pdf_text_checked=pdf_text,source_links_checked=len(sources),worked_allocation_checked=True,
                scope='Pilot report source/code/artifact hashes, tables and row-derived allocation example, native Word/Markdown links, optional PDF text and link annotations; numerical ranking replay is separate',
                manifest_sha256=sha(out/'report_manifest.json'),outputs_sha256={name:sha(out/name) for name in (STEM+'.md',STEM+'.docx',STEM+'.pdf')})


def verify(root=ROOT,pdf_text=False):
    root=Path(root);out=root/'reports/ranking';out.mkdir(parents=True,exist_ok=True);path=out/'verification.json'
    started=datetime.now(timezone.utc).isoformat();path.write_text(json.dumps(dict(passed=False,status='running',started_at_utc=started)),encoding='utf-8')
    try:
        record=checks(root,pdf_text);record.update(passed=True,status='passed',started_at_utc=started,
            completed_at_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)))
        path.write_text(json.dumps(record,indent=2),encoding='utf-8')
        print('RANKING REPORT PASSED: %d checks; PDF text checked=%s.'%(record['checks'],pdf_text))
        return record
    except (Exception,KeyboardInterrupt) as error:
        path.write_text(json.dumps(dict(passed=False,status='failed',error_type=type(error).__name__,error=str(error)),indent=2),encoding='utf-8')
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pdf',action='store_true');args=parser.parse_args();verify(pdf_text=args.pdf)
