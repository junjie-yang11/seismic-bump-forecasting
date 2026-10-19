"""Independently check the integrated paper against saved rows and counts.

The default needs only the standard library. ``--pdf`` additionally checks
exported PDF text with pypdf in the reporting environment. No model is fitted.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
STEM='integrated_research_report'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def _checks(root, pdf_text):
    out=root/'reports/overall'; count=0; checked_inputs={}
    def check(condition,message):
        nonlocal count
        count+=1
        if not condition: raise AssertionError(message)
    def read(relative):
        checked_inputs[relative]=sha(root/relative)
        with (root/relative).open(newline='',encoding='utf-8') as stream:return list(csv.DictReader(stream))
    def take(rows,**query):
        found=[]
        for r in rows:
            ok=True
            for k,v in query.items():
                if isinstance(v,(int,float)):
                    ok=bool(r[k]) and float(r[k])==v
                else:ok=r[k]==v
                if not ok:break
            if ok:found.append(r)
        check(len(found)==1,'unique source selection '+str(query))
        return found[0]
    def fmt(x,d=4): return f'{float(x):.{d}f}'
    def bounds(a,b,d=4):return f'[{fmt(a,d)}, {fmt(b,d)}]'
    def range_text(values,d=2):
        values=list(map(float,values));a,b=min(values),max(values)
        return fmt(a,d) if a==b else f'{fmt(a,d)} to {fmt(b,d)}'

    manifest=json.loads((out/'report_manifest.json').read_text(encoding='utf-8'))
    check(sha(root/'reporting/overall.py')==manifest['generator_sha256'],'current generator hash')
    for relative,value in manifest['inputs'].items():check(sha(root/relative)==value,'unchanged source '+relative)
    for name,value in manifest['outputs'].items():check(sha(out/name)==value,'current generated artifact '+name)
    md=(out/(STEM+'.md')).read_text(encoding='utf-8')
    with ZipFile(out/(STEM+'.docx')) as package:
        body=ET.fromstring(package.read('word/document.xml')).find('w:body',NS)
        core=ET.fromstring(package.read('docProps/core.xml'))
        for node in core:
            if node.tag.rsplit('}',1)[-1] in ('creator','lastModifiedBy'):
                check(not node.text,'clean Word author metadata')
    for p in body.findall('w:p',NS):
        text=''.join(p.itertext())
        if text.strip():check(text in md,'Word paragraph agrees with manuscript')
    word_tables=[]
    for t in body.findall('w:tbl',NS):
        word_tables.append([[''.join(c.itertext()) for c in row.findall('w:tc',NS)]
                            for row in t.findall('w:tr',NS)])
    check(len(word_tables)==len(manifest['tables'])==14,'thirteen numbered tables with two Table 3 panels')
    tables={}
    for observed,declared in zip(word_tables,manifest['tables']):
        check(observed==[declared['headers']]+declared['rows'],'Word table '+declared['id'])
        for cells in observed:check('| '+' | '.join(cells)+' |' in md,'Markdown table row')
        block=['| '+' | '.join(declared['headers'])+' |',
               '| '+' | '.join(['---']*len(declared['headers']))+' |']
        block += ['| '+' | '.join(row)+' |' for row in declared['rows']]
        check('\n'.join(block) in md,'contiguous GitHub Markdown table '+declared['id'])
        tables[declared['id']]=observed[1:]
    references=re.findall(r'^\[(\d+)\] (.+)$',md,re.M)
    check([int(n) for n,_ in references]==list(range(1,len(references)+1)),'continuous bibliography')
    check(len(references)==17,'retained scientific, data and method references')
    prose=md.split('## References')[0]
    # Bibliographic indices are positive; [0,0] is an explicitly reported zero interval.
    citations=[int(n) for group in re.findall(r'\[([1-9]\d*(?:,[1-9]\d*)*)\]',prose) for n in group.split(',')]
    check(set(citations)==set(range(1,len(references)+1)),'each citation resolves and every source is used')
    for unwanted in ['Scientific Agent Skills','2609.00065','TODO','TBD','PLACEHOLDER']:
        check(unwanted not in md,'no unwanted tool reference or placeholder '+unwanted)
    check('AI-assisted writing workflows do not supply scientific evidence' in md,'AI disclosure separated from evidence')
    check('wholly within the common test rows' in md and 'supplementary, overlapping evidence' in md,'overlapping holdout explicit')
    check('not a direct grade-to-alarm rule' in md,'ratings-only meaning explicit')
    check('separately specified supplement' in md and 'interval is [0,0] by construction' in md,'new conditional no-alarm evidence explicit')
    check('weighted by recall increments' in md and 'precision increments' not in md,'correct AP definition')
    check('not to AP-minus-pi' in md,'protocol interval distinct from AP-gain uncertainty')
    for target in re.findall(r'\]\(([^)]+)\)',md):
        if '://' not in target and not target.startswith('#'):check((out/target).exists(),'report image/link '+target)

    ab=read('results/phase1/feature_ablation.csv')
    full={m:take(ab,model=m,variant='full') for m in ('LR','CART','XGBoost')}
    predictions=read('results/phase2/predictions.csv')
    pred=[r for r in predictions if r['model']=='XGBoost' and r['scheme']=='time']
    labels={int(r['row']):int(float(r['y'])) for r in pred}
    check(len(labels)==len(pred)==2063,'unique common test rows')
    check(sum(labels.values())==88,'common positive count from row evidence')
    pi=sum(labels.values())/len(labels)
    refs=read('results/phase2/references.csv')
    expected=[]
    for f in range(4):
        q=[r for r in pred if int(r['fold'])==f]
        h=[r for r in refs if r['model']=='XGBoost' and r['scheme']=='time' and int(r['fold'])==f]
        expected.append([str(f+1),str(len(q)),str(sum(int(float(r['y'])) for r in q)),
                         f'{100*sum(int(float(r["y"])) for r in q)/len(q):.2f}%',str(len(h)),str(sum(int(float(r['y'])) for r in h))])
    check(tables['cohorts']==expected,'cohort table from row-level labels and references')
    shared=read('results/phase1/shared_test_comparison.csv');ci=read('results/phase1/paired_uncertainty.csv')
    xr=read('results/phase1/xgboost_shared_by_seed.csv');xc=read('results/phase1/xgboost_protocol_interval.csv')[0]
    expected=[]
    for m in ('LR','CART','XGBoost'):
        if m=='XGBoost':random=sum(float(r['random_ap']) for r in xr)/len(xr);result=xc
        else:
            src=next(r for r in shared if ('logistic' in r['model'])==(m=='LR'))
            random=float(src['random_pr_auc']);result=take(ci,model=m,block_length=32)
        ap=float(full[m]['pr_auc'])
        check(int(full[m]['n'])==len(labels) and int(full[m]['positives'])==sum(labels.values()),'AP cohort '+m)
        expected.append([m,fmt(random),fmt(ap),fmt(ap-pi),fmt(result['delta']),bounds(result['ci_low'],result['ci_high'])])
    check(tables['ranking']==expected,'AP table and descriptive baseline gains')
    gaps=read('results/phase1/gap_attenuation.csv')
    original=read('results/phase1/metrics_by_scheme.csv');expected=[]
    for model in ('LR','CART'):
        g=take(gaps,model=model)
        name=next(r['model'] for r in shared if ('logistic' in r['model'])==(model=='LR'))
        oldrandom=take(original,model=name,validation='random stratified 10-fold')
        ordered=take(original,model=name,validation='time-ordered expanding window')
        common=take(shared,model=name)
        oldgap=float(oldrandom['pr_auc'])-float(ordered['pr_auc'])
        newgap=float(common['random_pr_auc'])-float(common['time_pr_auc'])
        reduction=1-newgap/oldgap
        for actual,value in ((g['original_gap'],oldgap),(g['same_test_gap'],newgap),(g['gap_reduction_fraction'],reduction)):
            check(math.isclose(float(actual),value,rel_tol=1e-12,abs_tol=1e-14),'gap from original/common AP sources')
        expected.append([model,fmt(oldgap,5),fmt(newgap,5),f'{100*reduction:.1f}%'])
    check(tables['gap_attenuation']==expected,'Table 3b uses unrounded gaps')
    check('Attenuation = 1 - common-cohort gap / different-cohort gap' in md,'attenuation formula explicit')
    check('Two questions organize the analysis' in md and 'one is not a prospective validation of the other' in md,'two questions preserve separate protocols')
    probability=read('results/phase1/probability_reference_comparison.csv');expected=[]
    for m in ('LR','CART','XGBoost'):
        r=take(probability,model=m,validation='time',fold=-1)
        expected.append([m]+[fmt(r[k]) for k in ('model_brier','historical_brier','historical_skill','oracle_brier','oracle_skill')])
    check(tables['probability']==expected,'Brier references and skills')
    abci=read('results/phase1/feature_ablation_intervals.csv');expected=[]
    for m in ('LR','CART','XGBoost'):
        r=take(ab,model=m,variant='ratings_only');v=take(abci,model=m,variant='ratings_only')
        expected.append([m,fmt(full[m]['pr_auc']),fmt(r['pr_auc']),fmt(float(full[m]['pr_auc'])-float(r['pr_auc'])),bounds(-float(v['ci_high']),-float(v['ci_low']))])
    check(tables['ablation']==expected,'ablation contrast sign and interval inversion')

    decisions=read('results/phase2/decisions.csv')
    d=[r for r in decisions if r['model']=='XGBoost' and r['scheme']=='time' and r['workflow']=='fixed']
    check(len(d)==len(pred) and {(int(r['fold']),int(r['row'])) for r in d}
          =={(int(r['fold']),int(r['row'])) for r in pred},'unique, phase-aligned decision keys')
    def counts(rule):
        selected=[r for r in d if r[rule].lower() in ('true','1')]
        tp=sum(labels[int(r['row'])] for r in selected);fp=len(selected)-tp
        return tp,fp,sum(labels.values())-tp,len(selected)
    rules=[('none',None,'none')]+[(f'A_b{b:02d}',b,'A') for b in (1,5,10,20)]+[('B_r10',None,'B')]+[(f'C_b{b:02d}_r10',b,'C') for b in (1,5,10,20)]
    expected=[]
    for rule,b,m in rules:
        tp,fp,fn,alerts=counts(rule)
        if b is None:excess='-'
        else:
            total=0
            for f in range(4):
                q=[r for r in d if int(r['fold'])==f]
                a=sum(r[rule].lower() in ('true','1') for r in q)
                total+=max(0,a-math.floor(b/100*len(q)))
            excess=str(total)
        expected.append([m,'-' if b is None else str(b)+'%',fmt(100*(10*fn+fp)/len(labels),2),
                         fmt(100*(fp-10*tp)/len(labels),2),str(tp),str(fn),str(fp),str(alerts),excess])
    check(tables['decision']==expected,'decision counts, loss and phase-wise excess from raw decisions')
    audits=read('results/phase2/threshold_explanations.csv')
    e=read('results/phase2/evaluations.csv');expected=[]
    for f in range(4):
        a=[r for r in e if r['model']=='XGBoost' and r['scheme']=='time' and r['workflow']=='fixed' and int(r['fold'])==f and r['mechanism']=='A' and float(r['cost'])==10]
        c=[r for r in e if r['model']=='XGBoost' and r['scheme']=='time' and r['workflow']=='fixed' and int(r['fold'])==f and r['mechanism']=='C']
        quiet=[r for r in audits if r['model']=='XGBoost' and r['scheme']=='time' and int(r['fold'])==f and int(r['reference_alerts'])==0]
        expected.append([str(f+1),f'{sum(float(r["excess"])>0 for r in a)}/4',f'{sum(float(r["excess"])>0 for r in c)}/16',
                         str(sum(r['no_alarm_reason']=='cost_selects_no_alarm' for r in quiet)),str(sum(r['no_alarm_reason']=='capacity_changes_to_no_alarm' for r in quiet))])
    check(tables['capacity']==expected,'capacity denominators and reference-only causes')
    expected=[]
    original_audits=read('results/phase2/audits.csv')
    for m in ('A','B','C'):
        historical=[r for r in original_audits if r['model']=='XGBoost' and r['scheme']=='time' and r['mechanism']==m]
        finite={(int(r['fold']),r['rule']) for r in historical if math.isfinite(float(r['threshold']))}
        q=[r for r in e if r['model']=='XGBoost' and r['scheme']=='time' and r['workflow']=='fixed' and (int(r['fold']),r['rule']) in finite]
        differences=[];alert_changes=[]
        for r in q:
            t=take(e,model='XGBoost',scheme='time',workflow='refitted',fold=int(r['fold']),rule=r['rule'],cost=float(r['cost']))
            differences.append(float(t['loss100'])-float(r['loss100']))
            alert_changes.append(float(t['alerts'])-float(r['alerts']))
        expected.append([m,str(len(finite)),str(sum(float(r['threshold'])==math.inf for r in historical)),
                         str(sum(float(r['threshold'])==-math.inf for r in historical)),range_text(differences),range_text(alert_changes,0)])
    check(tables['refitting']==expected,'refit counts and differences from original evaluations')
    expected=[]
    for b in (1,5,10,20):
        tp,fp,fn,alerts=counts(f'C_b{b:02d}_r10')
        check(tp>0 or fp==0,'displayed no-detection boundary is no-alarm-equivalent')
        expected.append([str(b)+'%',str(tp),str(fp),str(alerts),fmt(fp/tp,2) if tp else '-'])
    check(tables['boundaries']==expected,'frozen cost equality from row decisions')
    expected=[]
    for b in (1,5,10,20):
        tp,fp,fn,alerts=counts(f'C_b{b:02d}_r10');tpr=tp/sum(labels.values());fpr=fp/(len(labels)-sum(labels.values()))
        row=[str(b)+'%']
        for p in (.05,.10):
            expected_alerts=p*tpr+(1-p)*fpr
            delta=100*((1-p)*fpr-10*p*tpr)
            row.extend([fmt(delta,2),f'{100*expected_alerts:.2f}%',f'{100*p*tpr/expected_alerts:.2f}%' if expected_alerts else 'NA'])
        expected.append(row)
    check(tables['scenarios']==expected,'scenario loss, workload and precision from class-conditional counts')
    se=read('results/phase2/comparators/evaluations.csv');sc=read('results/phase2/comparators/intervals.csv')
    sd=read('results/phase2/comparators/decisions.csv')
    grade_b={field:sorted([r for r in sd if r['method']==field],key=lambda r:int(r['row'])) for field in ('seismic','seismoacoustic','ghazard')}
    for field in ('seismoacoustic','ghazard'):
        check([(r['row'],r['B_r10']) for r in grade_b[field]]==[(r['row'],r['B_r10']) for r in grade_b['seismic']],
              'grade B decisions are identical, not merely dependent')
    check(all((r['B_r10']=='True')==(int(r['fold'])==0) for r in grade_b['seismic']),'grade B alarms all phase 1 and none later')
    check('three grade B rules make exactly the same row-level decisions' in md and '101 fewer false alerts' in md,'common B comparator and detection tradeoff explicit')
    check('an unresolved pooled direction does not erase a resolved increase' in md,'phase and pooled conclusions remain distinct')
    def effect(r):return fmt(r['loss_delta100'],2)+' '+bounds(r['ci_low'],r['ci_high'],2)
    def integer(value):return str(int(float(value)))
    def expand(rows, methods):
        expanded=[]
        for row in rows:
            fold=-1 if row[0]=='Pooled' else int(row[0])-1
            budgets=[float(v.strip().rstrip('%'))/100 for v in row[1].split(',')]
            for method in methods:
                reference=None
                cohort=sorted([r for r in sd if r['method']==method and (fold<0 or int(r['fold'])==fold)],key=lambda r:int(r['row']))
                for budget in budgets:
                    column=f'C_b{round(100*budget):02d}_r10'
                    vector=[(r['row'],r['y'],r[column]) for r in cohort]
                    check(reference is None or vector==reference,'grouped budgets have exactly identical decisions')
                    reference=vector
            for budget in budgets:expanded.append([row[0],f'{100*budget:.0f}%']+row[2:])
        check(len({tuple(r[:2]) for r in expanded})==len(expanded),'no omitted/duplicated grouped cohort-budget keys')
        return sorted(expanded)
    expected=[]
    for f in (0,1,2,3,-1):
        for b in (.01,.05,.1,.2):
            e=take(se,method='XGBoost',fold=f,mechanism='C',cost=10,budget=b)
            r=take(sc,left_method='XGBoost',right_method='none',fold=f,mechanism='C',cost=10,budget=b)
            expected.append(['Pooled' if f<0 else str(f+1),f'{100*b:.0f}%',effect(r),integer(e['tp']),integer(e['fn']),integer(e['alerts'])])
    check(expand(tables['no_alarm_intervals'],('XGBoost',))==sorted(expected),'complete phase and pooled C-minus-none intervals and detections')
    expected=[]
    for b in (.01,.05,.1,.2):
        for m in ('XGBoost','seismic','seismoacoustic','ghazard'):
            e=take(se,method=m,fold=-1,mechanism='C',cost=10,budget=b)
            r=take(sc,left_method=m,right_method='none',fold=-1,mechanism='C',cost=10,budget=b)
            expected.append([f'{100*b:.0f}%',m,effect(r)]+[integer(e[k]) for k in ('tp','fn','fp','alerts','excess')])
    expanded=[]
    for row in tables['grade_decisions']:
        budgets=[v.strip() for v in row[0].split(',')]
        excess=[v.strip() for v in row[-1].split(',')]
        check(len(budgets)==len(excess),'capacity excess mapped to each budget')
        reference=None
        cohort=sorted([r for r in sd if r['method']==row[1]],key=lambda r:int(r['row']))
        for budget,value in zip(budgets,excess):
            column=f"C_b{int(budget.rstrip('%')):02d}_r10"
            vector=[(r['row'],r['y'],r[column]) for r in cohort]
            check(reference is None or vector==reference,'pooled grade groups use identical row decisions')
            reference=vector
            expanded.append([budget]+row[1:-1]+[value])
    check(len(expanded)==len({tuple(r[:2]) for r in expanded})==16,'all sixteen method-budget settings retained')
    check(sorted(expanded)==sorted(expected),'all grade methods and budget-specific capacity retained')
    expected=[]
    for f in (0,1,2,3,-1):
        for b in (.01,.05,.1,.2):
            row=['Pooled' if f<0 else str(f+1),f'{100*b:.0f}%']
            for m in ('seismic','seismoacoustic','ghazard'):
                row.append(effect(take(sc,left_method='XGBoost',right_method=m,fold=f,mechanism='C',cost=10,budget=b)))
            expected.append(row)
    check(expand(tables['grade_intervals'],('XGBoost','seismic','seismoacoustic','ghazard'))==sorted(expected),'all phase-specific ML-minus-grade intervals')
    plot=read('reports/overall/decision_tradeoffs.csv')
    check(len(plot)==20,'all four budgets in four phases plus supplemental pooled figure')
    check(len({(r['fold'],r['budget']) for r in plot})==20,'unique plot settings')
    for r in plot:
        check((r['model'],r['workflow'],r['mechanism'],r['cost'])==('XGBoost','fixed','C','10'),'fixed decision-figure conditions')
        fold=int(r['fold']);budget=float(r['budget']);column=f'C_b{round(100*budget):02d}_r10'
        cohort=[v for v in sd if v['method']=='XGBoost' and (fold<0 or int(v['fold'])==fold)]
        positive=sum(int(float(v['y'])) for v in cohort)
        alerted=[v for v in cohort if v[column].lower() in ('true','1')]
        tp=sum(int(float(v['y'])) for v in alerted);fp=len(alerted)-tp
        for field,value in (('n',len(cohort)),('positives',positive),('alerts',len(alerted)),('tp',tp),('fn',positive-tp)):
            check(int(r[field])==value,'plot counts from raw decisions '+field)
        check(math.isclose(float(r['delta_loss100']),100*(fp-10*tp)/len(cohort),abs_tol=1e-10),'plot loss sign and arithmetic')
        ci=take(sc,left_method='XGBoost',right_method='none',fold=fold,mechanism='C',cost=10,budget=budget)
        for field in ('ci_low','ci_high'):check(float(r[field])==float(ci[field]),'correct policy-minus-none interval '+field)
        observed=take(se,method='XGBoost',fold=fold,mechanism='C',cost=10,budget=budget)
        for field in ('slots','excess'):check(int(r[field])==int(float(observed[field])),'plot capacity field '+field)
    check((out/'decision_tradeoffs.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n'),'valid decision plot PNG')
    appendix=(out/'comparator_appendix.md').read_text(encoding='utf-8')
    lookup={(r['left_method'],r['rule'],r['cost'],r['fold']):r for r in sc if r['comparison']=='policy-none'}
    for e in se:
        ci=lookup[(e['method'],e['rule'],e['cost'],e['fold'])]
        cells=['Pooled' if int(e['fold'])<0 else str(int(e['fold'])+1),e['method'],e['rule'],effect(ci)]
        cells += [integer(e[k]) for k in ('tp','fn','fp','alerts')]+[integer(e['excess']) if e['excess'] else '-']
        check('| '+' | '.join(cells)+' |' in appendix,'full-cost appendix policy row')
    for r in sc:
        if r['comparison']!='ML-grade':continue
        cells=['Pooled' if int(r['fold'])<0 else str(int(r['fold'])+1),r['right_method'],r['rule'],effect(r)]
        check('| '+' | '.join(cells)+' |' in appendix,'full-cost appendix paired contrast')
    figures=len(body.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline'))
    check(figures==4,'four inline figures including decision evidence')
    pdf=out/(STEM+'.pdf');check(pdf.read_bytes().startswith(b'%PDF-'),'valid PDF export')
    pages=None
    if pdf_text:
        from pypdf import PdfReader
        reader=PdfReader(pdf);pages=len(reader.pages)
        check(8<=pages<=22,'expected integrated report page range')
        text='\n'.join(p.extract_text() or '' for p in reader.pages)
        check('Scientific Agent Skills' not in text and '2609.00065' not in text,'no tool paper in PDF')
        check('/Author' not in (reader.metadata or {}),'clean PDF author metadata')
        for table in manifest['tables']:
            for row in table['rows']:
                for cell in row:
                    for value in re.findall(r'\b\d+\.\d+\b',cell):check(value in text,'PDF table decimal '+value)
        check('References' in (reader.pages[-1].extract_text() or ''),'reference section retained at report end')
    return dict(checks=count,tables=len(tables),figures=figures,pages=pages,pdf_text_checked=pdf_text,
                scope='Saved-source hashes, aligned row counts/decisions, independently reconstructed report tables, citation and Word/Markdown agreement; optional exported-PDF text. No model fitting or field validation.',
                manifest_sha256=sha(out/'report_manifest.json'),generator_sha256=sha(root/'reporting/overall.py'),
                checked_row_and_table_inputs_sha256=checked_inputs,
                outputs_sha256={name:sha(out/name) for name in (STEM+'.md',STEM+'.docx',STEM+'.pdf','evidence_overview.png','decision_tradeoffs.png','decision_tradeoffs.csv','comparator_appendix.md')})


def verify(root=ROOT,pdf_text=False):
    root=Path(root);out=root/'reports/overall';out.mkdir(parents=True,exist_ok=True)
    record=out/'verification.json';started=datetime.now(timezone.utc).isoformat()
    record.write_text(json.dumps(dict(passed=False,status='running',started_at_utc=started)),encoding='utf-8')
    try:
        result=_checks(root,pdf_text)
        result.update(passed=True,status='passed',started_at_utc=started,
                      completed_at_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)))
        record.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(f'OVERALL REPORT PASSED: {result["checks"]} checks, {result["tables"]} tables; PDF text checked={pdf_text}.')
        return result
    except (Exception,KeyboardInterrupt) as error:
        record.write_text(json.dumps(dict(passed=False,status='failed',started_at_utc=started,
            error_type=type(error).__name__,error=str(error)),indent=2),encoding='utf-8')
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--pdf',action='store_true');args=parser.parse_args()
    verify(args.root,args.pdf)
