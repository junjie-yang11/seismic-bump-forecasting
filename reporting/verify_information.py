"""Check the matched-information report against row-level inclusion evidence."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
STEM='monitoring_information_increment'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checks(root,pdf_text=False):
    out=root/'reports/information';count=0
    def check(ok,message):
        nonlocal count
        count+=1
        if not ok:raise AssertionError(message)
    def read(name):return list(csv.DictReader((root/'results/phase2/information'/name).open(encoding='utf-8',newline='')))
    def take(rows,**query):
        selected=[r for r in rows if all(float(r[k])==v if isinstance(v,(float,int)) else r[k]==v for k,v in query.items())]
        check(len(selected)==1,'one source row '+str(query));return selected[0]
    def num(x):return f'{float(x):.2f}'
    def effect(r):return num(r['delta_etp'])+' ['+num(r['ci_low'])+', '+num(r['ci_high'])+']'
    manifest=json.loads((out/'report_manifest.json').read_text(encoding='utf-8'))
    check(sha(root/'reporting/information.py')==manifest['generator_sha256'],'current information report generator')
    check(sha(root/'reporting/overall.py')==manifest['writer_sha256'],'current shared Word writer')
    for relative,digest in manifest['inputs'].items():check(sha(root/relative)==digest,'source '+relative)
    for name,digest in manifest['outputs'].items():check(sha(out/name)==digest,'generated output '+name)
    numerical=json.loads((root/'results/phase2/information/verification.json').read_text())
    check(numerical.get('passed') and numerical.get('refit'),'passed separate calculations and actual refit replay')
    check(numerical['verifier_sha256']==sha(root/'phase2/information/verify.py'),'current numerical verifier')
    check(numerical['provenance']['helper_sha256']==sha(root/'phase2/information/provenance.py'),'current historical-context verifier')
    check(numerical['provenance']['archive_sha256']==sha(root/'results/phase2/information/historical_context.zip'),'preserved original historical context')
    md=(out/(STEM+'.md')).read_text(encoding='utf-8')
    with ZipFile(out/(STEM+'.docx')) as package:
        body=ET.fromstring(package.read('word/document.xml')).find('w:body',NS)
        relationships=ET.fromstring(package.read('word/_rels/document.xml.rels'))
        core=ET.fromstring(package.read('docProps/core.xml'))
        for node in core:
            if node.tag.rsplit('}',1)[-1] in ('creator','lastModifiedBy'):check(not node.text,'clean Word author metadata')
    from reporting.verify_math import verify_equations
    from reporting.verify_overall import ordinary_paragraph_text
    verify_equations(body,md,check,('tie_expectation','total_expectation','expected_loss'))
    for paragraph in body.findall('w:p',NS):
        text=ordinary_paragraph_text(paragraph)
        if text.strip():
            prose=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',md) if paragraph.find('w:hyperlink',NS) is not None else md
            check(text in prose,'Word paragraph agrees with manuscript')
    version='de833195e2e7d025ca75c1efb57ac6d866127461'
    edition='manuscript-2026-10-26'
    base='https://github.com/junjie-yang11/seismic-bump-forecasting/blob/'+version+'/'
    sources=[
        ['UCI dataset and target definition','https://archive.ics.uci.edu/dataset/266/seismic+bumps'],
        ['Audited source and row mapping',base+'data/README.md'],
        ['Matched-information protocol',base+'phase2/information/protocol.json'],
        ['Model fitting and within-grade allocation',base+'phase2/information/run.py'],
        ['Numerical verification and refit replay',base+'phase2/information/verify.py'],
        ['Saved results and verification guide',base+'results/phase2/information/README.md'],
        ['Integrated manuscript in this edition','https://github.com/junjie-yang11/seismic-bump-forecasting/blob/'+edition+'/reports/overall/integrated_research_report.pdf'],
        ['Author contributions and AI assistance',base+'CONTRIBUTIONS.md']]
    check(manifest['source_version']==version and manifest['edition_tag']==edition,'scientific source and presentation edition distinguished')
    check(manifest['source_links']==sources,'fixed expected source destinations')
    targets={r.get('Id'):r.get('Target') for r in relationships if r.get('Type','').endswith('/hyperlink') and r.get('TargetMode')=='External'}
    word_links=[[''.join(link.itertext()),targets.get(link.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'))]
                for link in body.findall('.//w:hyperlink',NS)]
    check(word_links==sources,'native Word hyperlinks match source and edition targets')
    for label,url in sources:check('['+label+']('+url+')' in md,'clickable Markdown source '+label)
    audit=json.loads((root/'results/phase1/source_audit.json').read_text(encoding='utf-8'))
    check(f'containing {int(audit["mirror_rows"]):,} records' in md,'standalone audited mirror size')
    for statement in ('above 10,000 J in the subsequent eight-hour shift',
                      'a (no hazard), b (low hazard), c (high hazard) and d (danger state)',
                      'mirror contains only a, b for this field',
                      'Average precision (AP) is the sum of precision values weighted by recall increments',
                      'evaluating tied scores as a group'):
        check(statement in md,'standalone background '+statement)
    tables=[[[''.join(cell.itertext()) for cell in row.findall('w:tc',NS)] for row in table.findall('w:tr',NS)] for table in body.findall('w:tbl',NS)]
    check(len(tables)==len(manifest['tables'])==1,'one main result table')
    table=manifest['tables'][0]
    check(tables[0]==[table['headers']]+table['rows'],'Word table agrees with declared data')
    block=['| '+' | '.join(table['headers'])+' |','| '+' | '.join(['---']*len(table['headers']))+' |']
    block+=['| '+' | '.join(row)+' |' for row in table['rows']]
    check('\n'.join(block) in md,'complete GitHub Markdown table')
    rows=read('rows.csv');ev=read('evaluations.csv');ci=read('intervals.csv');expected=[]
    check(len(rows)==2063 and len({r['row'] for r in rows})==2063,'unique shared test rows')
    # Reconstruct the stated total as complete groups plus the partial boundary.
    # Do not reuse the experiment's ranking or inclusion-probability functions.
    for fold in range(4):
        block=[r for r in rows if int(r['fold'])==fold]
        for budget in (.01,.05,.10,.20):
            for design in ('base','extended'):
                groups={}
                for r in block:
                    key=(float(r['grade']),float(r[design+'_score']))
                    groups.setdefault(key,[]).append(float(r['y']))
                remaining=math.floor(budget*len(block));fully_selected=0.;boundary=0.
                for key in sorted(groups,reverse=True):
                    labels=groups[key];m=len(labels);p=sum(labels)
                    if remaining>=m:
                        fully_selected+=p;remaining-=m
                    elif remaining:
                        boundary=remaining*p/m;remaining=0
                    else:
                        break
                column=design+f'_prob_b{round(100*budget):02d}'
                row_total=math.fsum(float(r[column])*float(r['y']) for r in block)
                check(math.isclose(fully_selected+boundary,row_total,rel_tol=0,abs_tol=1e-10),
                      'fully selected TP plus boundary expectation equals saved total')
    for fold in (0,1,2,3,-1):
        cohort=[r for r in rows if fold<0 or int(r['fold'])==fold];p=sum(float(r['y']) for r in cohort)
        for budget in (.01,.05,.10,.20):
            column=f'_prob_b{round(100*budget):02d}'
            base=sum(float(r['base'+column])*float(r['y']) for r in cohort)
            extended=sum(float(r['extended'+column])*float(r['y']) for r in cohort)
            alerts=[sum(float(r[design+column]) for r in cohort) for design in ('base','extended')]
            k=sum(math.floor(budget*sum(int(r['fold'])==f for r in cohort)) for f in sorted({int(r['fold']) for r in cohort}))
            for value in alerts:check(math.isclose(value,k,rel_tol=0,abs_tol=1e-10),'exact allocation via inclusion expectation')
            source=take(ev,fold=fold,budget=budget)
            for field,value in (('base_etp',base),('extended_etp',extended),('base_efn',p-base),('extended_efn',p-extended),('delta_etp',extended-base)):
                check(math.isclose(float(source[field]),value,rel_tol=0,abs_tol=1e-10),'row-derived result '+field)
            interval=take(ci,fold=fold,budget=budget,block_length=32)
            check(math.isclose(float(interval['delta_etp']),extended-base,rel_tol=0,abs_tol=1e-10),'main point from rows')
            expected.append(['Pooled' if fold<0 else str(fold+1),f'{100*budget:.0f}%',str(k),num(base)+' / '+num(p-base),num(extended)+' / '+num(p-extended),effect(interval)])
    check(table['rows']==expected,'all twenty phase and pooled rows independently reconstructed')
    figure=list(csv.DictReader((out/'figure_data.csv').open(encoding='utf-8',newline='')))
    check(len(figure)==60 and len({(r['fold'],r['budget'],r['block_length']) for r in figure})==60,'complete figure settings')
    for row in figure:
        source=take(ci,fold=int(row['fold']),budget=float(row['budget']),block_length=int(row['block_length']))
        for key in ('replicates','delta_etp','ci_low','ci_high'):check(float(row[key])==float(source[key]),'figure source '+key)
        point=take(ev,fold=int(row['fold']),budget=float(row['budget']))
        check(math.isclose(float(row['delta_etp']),float(point['delta_etp']),rel_tol=0,abs_tol=1e-12),'unchanged points across block lengths')
    check((out/'information_increment.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n'),'valid plot PNG')
    check(len(body.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline'))==1,'one embedded increment figure')
    positive_counts=[str(sum(float(r['delta_etp'])>0 for r in ev if int(r['fold'])==f))+'/4' for f in range(4)]
    check('Positive point differences occur in '+', '.join(positive_counts) in md,'phase differences derived from saved results')
    main=[r for r in ci if int(r['fold'])>=0 and int(r['block_length'])==32]
    crosses=sum(float(r['ci_low'])<=0<=float(r['ci_high']) for r in main)
    check(f'{crosses}/{len(main)} main block-specific intervals include zero' in md,'main interval count in discussion')
    pooled=[r for r in ci if int(r['fold'])==-1]
    if all(float(r['ci_low'])<=0<=float(r['ci_high']) for r in pooled):
        check('All pooled intervals across the three specified block lengths include zero.' in md,'pooled interval direction across all lengths')
    for text in ('same four historical fitting/test splits','Policy-reference and test labels do not enter fitting or tuning',
                 'Both models use uniform allocation','Total expected detections add TP from all fully selected grade-score groups',
                 'the boundary contribution is zero','Pooled total expectations sum block totals','scores are never ranked across fitted blocks',
                 'recomputes grade allocations and reranks','Intervals exclude fitting, tuning and selection uncertainty',
                 'expected loss uses the total expected detections','not an observed inspection process','original stage-specific papers and ranking-pilot experimental results are retained'):
        check(text in md,'interpretation scope '+text)
    for bad in ('TODO','TBD','PLACEHOLDER','Scientific Agent Skills','2609.00065'):
        check(bad not in md,'no placeholder/tool bibliography '+bad)
    for target in re.findall(r'\]\(([^)]+)\)',md):
        if '://' not in target and not target.startswith('#'):check((out/target).exists(),'report image/link '+target)
    pdf=out/(STEM+'.pdf');check(pdf.read_bytes().startswith(b'%PDF-'),'valid exported PDF')
    pages=None
    if pdf_text:
        from pypdf import PdfReader
        reader=PdfReader(pdf);pages=len(reader.pages);check(2<=pages<=6,'short supplement page range')
        check('/Author' not in (reader.metadata or {}),'clean PDF author metadata')
        text='\n'.join(page.extract_text() or '' for page in reader.pages)
        pdf_targets=set()
        for page in reader.pages:
            for annotation in page.get('/Annots',[]):
                action=annotation.get_object().get('/A')
                if action:pdf_targets.add(str(action.get_object().get('/URI','')))
        for label,url in sources:check(url in pdf_targets,'clickable PDF source '+label)
        compact=re.sub(r'\s+','',text)
        check('Extendedminusbaseexpecteddetections' in compact,'PDF figure caption retains contrast direction')
        check('Discussion' in text and 'Protocol and computational evidence' in text,'report ends with interpretation and evidence')
        for row in table['rows']:
            for cell in row:
                for number in re.findall(r'\b\d+\.\d+\b',cell):check(number in text,'PDF table value '+number)
    return dict(checks=count,tables=1,figures=1,phase_and_pooled_rows=len(expected),figure_settings=len(figure),pages=pages,pdf_text_checked=pdf_text,source_links_checked=len(sources),standalone_background_checked=True,
        scope='Source/code/output hashes, row-derived expected detections and allocation counts, complete main table and all-length plot data, Word/Markdown agreement and optional PDF text; numerical bootstrap/model refit verification is separate',
        manifest_sha256=sha(out/'report_manifest.json'),outputs_sha256={name:sha(out/name) for name in (STEM+'.md',STEM+'.docx',STEM+'.pdf','figure_data.csv','information_increment.png','information_increment.svg')})


def verify(root=ROOT,pdf_text=False):
    root=Path(root);out=root/'reports/information';out.mkdir(parents=True,exist_ok=True)
    path=out/'verification.json';started=datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(dict(passed=False,status='running',started_at_utc=started)),encoding='utf-8')
    try:
        result=checks(root,pdf_text);result.update(passed=True,status='passed',started_at_utc=started,completed_at_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)))
        path.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(f'INFORMATION REPORT PASSED: {result["checks"]} checks, one table and one figure; PDF text checked={pdf_text}.')
        return result
    except (Exception,KeyboardInterrupt) as error:
        path.write_text(json.dumps(dict(passed=False,status='failed',started_at_utc=started,error_type=type(error).__name__,error=str(error)),indent=2),encoding='utf-8');raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pdf',action='store_true');args=parser.parse_args();verify(pdf_text=args.pdf)
