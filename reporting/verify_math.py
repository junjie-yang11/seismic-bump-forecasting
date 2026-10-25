"""Expected equations specified separately from the Word/Markdown author."""
from reporting.word_math import math_signature


def expected_equations():
    t=lambda x:('text',x)
    s=lambda *x:('seq',*x)
    sub=lambda x,y:('sub',t(x),t(y))
    frac=lambda a,b:('frac',a,b)
    d=lambda a,b,c:('delim',a,b,c)
    return [
        (r'\mathrm{Brier\ skill}=1-\frac{BS_{\mathrm{model}}}{BS_{\mathrm{reference}}}',
         s(t('Brier skill'),t('='),t('1'),t('−'),frac(sub('BS','model'),sub('BS','reference')))),
        (r'L_{100}=\frac{100(r\,FN+FP)}{N}',
         s(sub('L','100'),t('='),frac(s(t('100'),d('(',')',s(t('r'),t('FN'),t('+'),t('FP')))),t('N')))),
        (r'\Delta L_{\mathrm{none},100}=\frac{100(FP-r\,TP)}{N}',
         s(t('Δ'),sub('L','none,100'),t('='),frac(s(t('100'),d('(',')',s(t('FP'),t('−'),t('r'),t('TP')))),t('N')))),
        (r'\mathrm{Excess}=\max\{0,\mathrm{Alerts}-\lfloor BN_{\mathrm{test}}\rfloor\}',
         s(t('Excess'),t('='),t('max'),d('{','}',s(t('0'),t(','),t('Alerts'),t('−'),d('⌊','⌋',s(t('B'),sub('N','test')))))))
    ]


def verify_equations(body, markdown, check):
    nodes=body.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath')
    expected=expected_equations()
    check(len(nodes)==len(expected),'four native editable equations')
    for node,(latex,structure) in zip(nodes,expected):
        check(math_signature(node)==structure,'independent mathematical structure: '+latex)
        check('$$\n'+latex+'\n$$' in markdown,'matching Markdown mathematical expression: '+latex)
