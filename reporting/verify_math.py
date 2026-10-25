"""Expected equations specified separately from the Word/Markdown author."""
from reporting.word_math import math_signature


MAIN_EQUATION_IDS = ('ap', 'brier_skill', 'loss100', 'delta_none100', 'excess',
                    'cost_boundary', 'scenario_loss', 'scenario_alert',
                    'scenario_precision', 'batch_slots', 'tie_expectation', 'total_expectation', 'expected_loss')


def expected_equations(equation_ids=None):
    t=lambda x:('text',x)
    s=lambda *x:('seq',*x)
    sub=lambda x,y:('sub',t(x),t(y))
    frac=lambda a,b:('frac',a,b)
    d=lambda a,b,c:('delim',a,b,c)
    registry={
        'ap': (r'AP=\sum_k P_k(R_k-R_{k-1})',
         s(t('AP'),t('='),('sum',t('k'),s(sub('P','k'),d('(',')',s(sub('R','k'),t('−'),sub('R','k−1'))))))),
        'brier_skill': (r'\mathrm{Brier\ skill}=1-\frac{BS_{\mathrm{model}}}{BS_{\mathrm{reference}}}',
         s(t('Brier skill'),t('='),t('1'),t('−'),frac(sub('BS','model'),sub('BS','reference')))),
        'loss100': (r'L_{100}=\frac{100(r\,FN+FP)}{N}',
         s(sub('L','100'),t('='),frac(s(t('100'),d('(',')',s(t('r'),t('FN'),t('+'),t('FP')))),t('N')))),
        'delta_none100': (r'\Delta L_{\mathrm{none},100}=\frac{100(FP-r\,TP)}{N}',
         s(t('Δ'),sub('L','none,100'),t('='),frac(s(t('100'),d('(',')',s(t('FP'),t('−'),t('r'),t('TP')))),t('N')))),
        'excess': (r'\mathrm{Excess}=\max\{0,\mathrm{Alerts}-\lfloor BN_{\mathrm{test}}\rfloor\}',
         s(t('Excess'),t('='),t('max'),d('{','}',s(t('0'),t(','),t('Alerts'),t('−'),d('⌊','⌋',s(t('B'),sub('N','test'))))))),
        'cost_boundary': (r'r^{*}=\frac{FP}{TP}',
         s(('sup',t('r'),t('*')),t('='),frac(t('FP'),t('TP')))),
        'scenario_loss': (r'L_{100}(\pi)=100[r\pi\,FNR+(1-\pi)FPR]',
         s(sub('L','100'),d('(',')',t('π')),t('='),t('100'),d('[',']',s(t('r'),t('π'),t('FNR'),t('+'),d('(',')',s(t('1'),t('−'),t('π'))),t('FPR'))))),
        'scenario_alert': (r'A(\pi)=\pi\,TPR+(1-\pi)FPR',
         s(t('A'),d('(',')',t('π')),t('='),t('π'),t('TPR'),t('+'),d('(',')',s(t('1'),t('−'),t('π'))),t('FPR'))),
        'scenario_precision': (r'\mathrm{Precision}(\pi)=\frac{\pi\,TPR}{A(\pi)}',
         s(t('Precision'),d('(',')',t('π')),t('='),frac(s(t('π'),t('TPR')),s(t('A'),d('(',')',t('π')))))),
        'batch_slots': (r'K=\lfloor BN_{\mathrm{test}}\rfloor',
         s(t('K'),t('='),d('⌊','⌋',s(t('B'),sub('N','test'))))),
        'tie_expectation': (r'E(TP_{\mathrm{boundary}})=\frac{hp}{m}',
         s(t('E'),d('(',')',sub('TP','boundary')),t('='),frac(s(t('h'),t('p')),t('m')))),
        'total_expectation': (r'E(TP_{\mathrm{total}})=TP_{\mathrm{fully\ selected}}+E(TP_{\mathrm{boundary}})',
         s(t('E'),d('(',')',sub('TP','total')),t('='),sub('TP','fully selected'),t('+'),t('E'),d('(',')',sub('TP','boundary')))),
        'expected_loss': (r'E(L)=rP+K-(r+1)E(TP_{\mathrm{total}})',
         s(t('E'),d('(',')',t('L')),t('='),t('r'),t('P'),t('+'),t('K'),t('−'),d('(',')',s(t('r'),t('+'),t('1'))),t('E'),d('(',')',sub('TP','total')))),
    }
    return [registry[key] for key in (MAIN_EQUATION_IDS if equation_ids is None else equation_ids)]


def verify_equations(body, markdown, check, equation_ids=None):
    nodes=body.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath')
    expected=expected_equations(equation_ids)
    check(len(nodes)==len(expected),'complete native editable equation inventory')
    for node,(latex,structure) in zip(nodes,expected):
        check(math_signature(node)==structure,'independent mathematical structure: '+latex)
        check('$$\n'+latex+'\n$$' in markdown,'matching Markdown mathematical expression: '+latex)
