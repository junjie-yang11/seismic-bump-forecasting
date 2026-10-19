"""A short, separate report for the prespecified frozen-score ranking pilot."""
from __future__ import annotations
import csv
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from .overall import write_outputs

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'reports/ranking'
STEM='within_grade_ranking_pilot'
TITLE='Ranking Within Hazard Grades at Fixed Inspection Capacity: A Retrospective Pilot'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    DEST.mkdir(parents=True,exist_ok=True);record=DEST/'verification.json'
    record.write_text(json.dumps(dict(passed=False,status='building')),encoding='utf-8')
    inputs={}
    def read(name):
        path=ROOT/name;inputs[name]=sha(path)
        return list(csv.DictReader(path.open(encoding='utf-8',newline='')))
    def one(rows,**query):
        part=[r for r in rows if all(float(r[k])==v if isinstance(v,(int,float)) else r[k]==v for k,v in query.items())]
        if len(part)!=1:raise ValueError('Expected one report source row: '+str(query))
        return part[0]
    def num(x):return f'{float(x):.2f}'
    def effect(r):return num(r['extra_tp'])+' ['+num(r['ci_low'])+', '+num(r['ci_high'])+']'
    try:
        (DEST/(STEM+'.pdf')).unlink(missing_ok=True)
        certificate=json.loads((ROOT/'results/phase2/ranking/verification.json').read_text(encoding='utf-8'))
        if not certificate.get('passed'):raise RuntimeError('Verify ranking computations before reporting')
        protocol=ROOT/'phase2/ranking/protocol.json';inputs['phase2/ranking/protocol.json']=sha(protocol)
        plan=json.loads(protocol.read_text(encoding='utf-8'))
        e=read('results/phase2/ranking/evaluations.csv');ci=read('results/phase2/ranking/intervals.csv')
        items=[dict(kind='title',text=TITLE),dict(kind='paragraph',text='Junjie Yang')];tables=[]
        def heading(text):items.append(dict(kind='heading',text=text))
        def para(text):items.append(dict(kind='paragraph',text=text))
        def table(key,caption,headers,rows):
            value=dict(id=key,caption=f'Table {len(tables)+1}. '+caption,headers=headers,rows=rows)
            tables.append(value);items.append(dict(kind='table',**value))
        heading('Research question and result')
        pooled=one(e,fold=-1,budget=.2);pooled_ci=one(ci,fold=-1,budget=.2,method='grade_ml')
        para('Can complete-model scores identify additional hazardous records within the same seismic grade and inspection allocation? This exploratory pilot uses saved fixed XGBoost scores on the existing four test blocks. It compares grade-priority ranking by model score with uniform random selection at exactly the same total and grade-specific allocations. Global model ranking is a separate auxiliary comparison.')
        para(f'At the 20% budget, grade-first ML detects {int(pooled["grade_ml_tp"])} hazardous records with {int(pooled["k"])} alerts, versus an analytic random expectation of {num(pooled["expected_random_tp"])} detections. The increment is {effect(pooled_ci)} records. '
             'The pooled intervals at all four budgets contain zero. Positive point increments at 5%, 10% and 20% do not resolve the direction of within-grade benefit under this conditional analysis. No grade, budget, model or seed is selected from these results.')
        heading('Data and fixed analysis protocol')
        para('The audited UCI mirror supplies seismic grades for 2,063 existing test records and 88 hazardous-shift labels. The observed primary field has a and b only. Higher grade receives priority. Within each grade, the full XGBoost score supplies the model ranking; seeded label-independent keys break score ties. The same keys are used for global model ranking. The full scores also use two other hazard grades, monitoring variables and shift type, so any increment is not an isolated sensor effect.')
        para('The separate protocol was saved before these calculations, after previous results had been inspected. It fixes seismic, the four original phases, budgets 1%, 5%, 10% and 20%, and the saved fixed-model scores. No model is trained, retuned or selected. The earlier Stage 2 whole-tie threshold rules remain unchanged; this pilot instead permits a grade group to be split to fill a hypothetical batch allocation.')
        para('For each phase, K=floor(B*N). Grade-random and grade-first ML receive identical k_g allocations, with E[TP_random]=sum_g k_g*P_g/N_g. Each expectation is calculated analytically rather than from one random draw. The saved hypergeometric allocation distribution describes random choice on this fixed queue; its spread is distinct from the block-bootstrap uncertainty interval.')
        para('The block analysis uses 2,000 paired moving-block draws of length 32 within phases. Every sampled queue is reallocated and reranked using frozen scores and the original label-independent tie keys, including duplicate copies. The random expectation is recomputed for each queue. Zero-positive draws are retained. Pooled results sum phase-specific allocations and detections; they never rank scores across separately fitted phase models. Intervals are unadjusted and exclude model-fitting and selection uncertainty.')
        heading('Phase results and pooled comparison')
        rows=[]
        for fold in (0,1,2,3,-1):
            for budget in plan['budgets']:
                r=one(e,fold=fold,budget=budget);interval=one(ci,fold=fold,budget=budget,method='grade_ml')
                rows.append(['Pooled' if fold<0 else str(fold+1),f'{100*budget:.0f}%',r['k'],num(r['expected_random_tp']),r['grade_ml_tp'],effect(interval)])
        table('ranking_primary','Extra detections from grade-first ML relative to analytic grade-random expectation. Brackets are conditional 95% block intervals.',
              ['Phase','Budget','K','Random E(TP)','Grade+ML TP','Extra TP [95%]'],rows)
        phase2_low=one(ci,fold=1,budget=.01,method='grade_ml')
        para('Phase-specific intervals and counts are the primary evidence. The pooled point increment is negative at 1% and positive at the three larger budgets, while all pooled intervals include both improvement and decrease. '
             f'Phase 2 at 1% instead has an increment of {effect(phase2_low)}, entirely below zero. '
             'Pooling does not erase that result. An interval spanning zero does not establish equivalence or exclude useful increments on another queue.')
        heading('Auxiliary ranking and interpretation')
        rows=[]
        for budget in plan['budgets']:
            r=one(e,fold=-1,budget=budget);interval=one(ci,fold=-1,budget=budget,method='global_ml')
            rows.append([f'{100*budget:.0f}%',r['k'],r['grade_ml_tp'],r['global_ml_tp'],effect(interval)])
        table('ranking_aux','Global model ranking on each phase, pooled afterwards. This can change allocations between grades and does not isolate within-grade information.',
              ['Budget','K','Grade+ML TP','Global ML TP','Global extra TP [95%]'],rows)
        para('The primary comparison holds grade-specific allocations fixed. The global comparison holds only total K fixed and therefore answers a different allocation question. Under the original hypothetical cost, L=r*P+K-(r+1)*TP. At fixed P and K, loss change is determined entirely by detection change; a second cost grid would not supply independent evidence.')
        para('These records are not verified simultaneously waiting inspection candidates. The pilot is retrospective batch ranking, not validation of real-time dispatch or accident prevention. Record order remains a temporal proxy. The present evidence does not establish a within-grade ranking increment or prove monitoring information useless. A source-attribution study would require matched grade-only and grade-plus-monitoring models, with shift type handled identically and equal fitting/tuning opportunities. That study has not been performed here.')
        heading('Code and evidence')
        para('The protocol and execution code are in phase2/ranking/. Results under results/phase2/ranking/ retain row-level decisions and random inclusion probabilities, allocations, evaluations, analytic allocation distributions and every block draw and reranked contrast. The verifier uses independent sorting, weighted-prefix reranking and SciPy hypergeometric probabilities. Author review and AI assistance follow the repository CONTRIBUTIONS.md statement; computational evidence comes from saved data and actual execution.')
        write_outputs(items,DEST,STEM,TITLE)
        manifest=dict(title=TITLE,created_at_utc=datetime.now(timezone.utc).isoformat(),inputs=inputs,
                      generator_sha256=sha(Path(__file__)),writer_sha256=sha(ROOT/'reporting/overall.py'),tables=tables,
                      source_certificate_at_build=dict(sha256=sha(ROOT/'results/phase2/ranking/verification.json'),scope=certificate['scope']),
                      outputs={name:sha(DEST/name) for name in (STEM+'.md',STEM+'.docx')})
        (DEST/'report_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        record.write_text(json.dumps(dict(passed=False,status='awaiting independent verification')),encoding='utf-8')
        print('Separate ranking pilot report generated: two tables; original study not rewritten.')
    except (Exception,KeyboardInterrupt) as error:
        record.write_text(json.dumps(dict(passed=False,status='failed',error_type=type(error).__name__,error=str(error)),indent=2),encoding='utf-8')
        raise


if __name__=='__main__':build()
