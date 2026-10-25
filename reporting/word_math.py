"""Small, structural native-Word equations for the integrated manuscript.

The same declared expressions have a LaTeX rendering for Markdown and an OMML
tree for editable Word math.  A signature reader exposes mathematical structure
so verification can check denominators, subscripts and delimiters rather than
comparing flattened text or relying on screenshots.
"""
from __future__ import annotations


MATH_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
WORD_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def text(value):
    return ('text', value)


def seq(*values):
    return ('seq', *values)


def sub(base, index):
    return ('sub', text(base), text(index))


def sup(base, index):
    return ('sup', text(base), text(index))


def summation(index, expression):
    return ('sum', text(index), expression)


def fraction(numerator, denominator):
    return ('frac', numerator, denominator)


def delimiter(left, right, content):
    return ('delim', left, right, content)


EQUATIONS = {
    'loss100': {
        'latex': r'L_{100}=\frac{100(r\,FN+FP)}{N}',
        'ast': seq(sub('L', '100'), text('='),
                   fraction(seq(text('100'), delimiter('(', ')',
                            seq(text('r'), text('FN'), text('+'), text('FP')))),
                            text('N'))),
    },
    'delta_none100': {
        'latex': r'\Delta L_{\mathrm{none},100}=\frac{100(FP-r\,TP)}{N}',
        'ast': seq(text('Δ'), sub('L', 'none,100'), text('='),
                   fraction(seq(text('100'), delimiter('(', ')',
                            seq(text('FP'), text('−'), text('r'), text('TP')))),
                            text('N'))),
    },
    'excess': {
        'latex': r'\mathrm{Excess}=\max\{0,\mathrm{Alerts}-\lfloor BN_{\mathrm{test}}\rfloor\}',
        'ast': seq(text('Excess'), text('='), text('max'),
                   delimiter('{', '}', seq(text('0'), text(','), text('Alerts'),
                             text('−'), delimiter('⌊', '⌋',
                                       seq(text('B'), sub('N', 'test')))))),
    },
    'brier_skill': {
        'latex': r'\mathrm{Brier\ skill}=1-\frac{BS_{\mathrm{model}}}{BS_{\mathrm{reference}}}',
        'ast': seq(text('Brier skill'), text('='), text('1'), text('−'),
                   fraction(sub('BS', 'model'), sub('BS', 'reference'))),
    },
    'ap': {
        'latex': r'AP=\sum_k P_k(R_k-R_{k-1})',
        'ast': seq(text('AP'), text('='), summation('k',
                   seq(sub('P', 'k'), delimiter('(', ')',
                       seq(sub('R', 'k'), text('−'), sub('R', 'k−1')))))),
    },
    'cost_boundary': {
        'latex': r'r^{*}=\frac{FP}{TP}',
        'ast': seq(sup('r', '*'), text('='), fraction(text('FP'), text('TP'))),
    },
    'scenario_loss': {
        'latex': r'L_{100}(\pi)=100[r\pi\,FNR+(1-\pi)FPR]',
        'ast': seq(sub('L', '100'), delimiter('(', ')', text('π')), text('='), text('100'),
                   delimiter('[', ']', seq(text('r'), text('π'), text('FNR'), text('+'),
                       delimiter('(', ')', seq(text('1'), text('−'), text('π'))), text('FPR')))),
    },
    'scenario_alert': {
        'latex': r'A(\pi)=\pi\,TPR+(1-\pi)FPR',
        'ast': seq(text('A'), delimiter('(', ')', text('π')), text('='), text('π'), text('TPR'), text('+'),
                   delimiter('(', ')', seq(text('1'), text('−'), text('π'))), text('FPR')),
    },
    'scenario_precision': {
        'latex': r'\mathrm{Precision}(\pi)=\frac{\pi\,TPR}{A(\pi)}',
        'ast': seq(text('Precision'), delimiter('(', ')', text('π')), text('='),
                   fraction(seq(text('π'), text('TPR')),
                            seq(text('A'), delimiter('(', ')', text('π'))))),
    },
    'batch_slots': {
        'latex': r'K=\lfloor BN_{\mathrm{test}}\rfloor',
        'ast': seq(text('K'), text('='), delimiter('⌊', '⌋', seq(text('B'), sub('N', 'test')))),
    },
    'tie_expectation': {
        'latex': r'E(TP_{\mathrm{boundary}})=\frac{hp}{m}',
        'ast': seq(text('E'), delimiter('(', ')', sub('TP', 'boundary')), text('='),
                   fraction(seq(text('h'), text('p')), text('m'))),
    },
    'total_expectation': {
        'latex': r'E(TP_{\mathrm{total}})=TP_{\mathrm{fully\ selected}}+E(TP_{\mathrm{boundary}})',
        'ast': seq(text('E'), delimiter('(', ')', sub('TP', 'total')), text('='),
                   sub('TP', 'fully selected'), text('+'), text('E'),
                   delimiter('(', ')', sub('TP', 'boundary'))),
    },
    'expected_loss': {
        'latex': r'E(L)=rP+K-(r+1)E(TP_{\mathrm{total}})',
        'ast': seq(text('E'), delimiter('(', ')', text('L')), text('='),
                   text('r'), text('P'), text('+'), text('K'), text('−'),
                   delimiter('(', ')', seq(text('r'), text('+'), text('1'))),
                   text('E'), delimiter('(', ')', sub('TP', 'total'))),
    },
}


def markdown_equation(equation_id):
    """Return a GitHub-compatible display equation, rejecting unknown IDs."""
    return '$$\n' + EQUATIONS[equation_id]['latex'] + '\n$$'


def _elements(expression):
    # Imported only for writing; signature inspection is standard-library only.
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    kind, *parts = expression
    if kind == 'seq':
        return [element for part in parts for element in _elements(part)]
    if kind == 'text':
        run = OxmlElement('m:r')
        properties = OxmlElement('m:rPr')
        normal = OxmlElement('m:nor'); normal.set(qn('m:val'), '1')
        properties.append(normal); run.append(properties)
        word_properties = OxmlElement('w:rPr')
        fonts = OxmlElement('w:rFonts')
        fonts.set(qn('w:ascii'), 'Cambria Math')
        fonts.set(qn('w:hAnsi'), 'Cambria Math')
        word_properties.append(fonts); run.append(word_properties)
        value = OxmlElement('m:t')
        value.text = parts[0]
        if ' ' in parts[0]:
            value.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        run.append(value)
        return [run]
    if kind == 'sub':
        node = OxmlElement('m:sSub')
        names = ('e', 'sub')
    elif kind == 'sup':
        node = OxmlElement('m:sSup')
        names = ('e', 'sup')
    elif kind == 'sum':
        lower, content = parts
        node = OxmlElement('m:nary'); properties = OxmlElement('m:naryPr')
        for name, value in (('chr', '∑'), ('limLoc', 'undOvr'), ('supHide', '1')):
            property_node = OxmlElement('m:' + name)
            property_node.set(qn('m:val'), value); properties.append(property_node)
        node.append(properties)
        for name, value in (('sub', lower), ('sup', text('')), ('e', content)):
            child = OxmlElement('m:' + name); child.extend(_elements(value)); node.append(child)
        return [node]
    elif kind == 'frac':
        node = OxmlElement('m:f')
        names = ('num', 'den')
    elif kind == 'delim':
        left, right, content = parts
        node = OxmlElement('m:d'); properties = OxmlElement('m:dPr')
        for name, value in (('begChr', left), ('endChr', right)):
            character = OxmlElement('m:' + name)
            character.set(qn('m:val'), value); properties.append(character)
        node.append(properties)
        body = OxmlElement('m:e')
        body.extend(_elements(content)); node.append(body)
        return [node]
    else:
        raise ValueError('Unsupported expression kind: ' + str(kind))
    for name, part in zip(names, parts):
        child = OxmlElement('m:' + name)
        child.extend(_elements(part)); node.append(child)
    return [node]


def append_equation(paragraph, equation_id):
    """Append editable OMML to an existing paragraph; return its math element."""
    expression = EQUATIONS[equation_id]['ast']
    from docx.oxml import OxmlElement
    node = OxmlElement('m:oMath')
    node.extend(_elements(expression))
    paragraph._p.append(node)
    return node


def math_signature(node):
    """Read a narrow OMML subset and reject unexpected math structures.

    Accepts either lxml or xml.etree elements. Styling is not mathematical
    evidence: run properties are ignored, but all substantive children must
    correspond to supported operations. Single-child wrapper sequences are
    collapsed to match the declared AST.
    """
    def qualified(name):
        return '{' + MATH_NS + '}' + name

    def children(parent):
        expressions = [parse(child) for child in parent]
        if not expressions:
            raise ValueError('Empty mathematical expression')
        return expressions[0] if len(expressions) == 1 else seq(*expressions)

    def required(parent, name):
        matches = parent.findall(qualified(name))
        if len(matches) != 1:
            raise ValueError('Expected one math child ' + name)
        return matches[0]

    def parse(current):
        tag = current.tag
        if tag == qualified('r'):
            values = current.findall(qualified('t'))
            allowed = {qualified('t'), qualified('rPr'), '{' + WORD_NS + '}rPr'}
            if len(values) != 1 or any(child.tag not in allowed for child in current):
                raise ValueError('Unexpected mathematical run')
            return text(values[0].text or '')
        if tag == qualified('f'):
            if {child.tag for child in current} != {qualified('num'), qualified('den')}:
                raise ValueError('Unexpected fraction structure')
            return fraction(children(required(current, 'num')), children(required(current, 'den')))
        if tag == qualified('sSub'):
            if {child.tag for child in current} != {qualified('e'), qualified('sub')}:
                raise ValueError('Unexpected subscript structure')
            return ('sub', children(required(current, 'e')), children(required(current, 'sub')))
        if tag == qualified('sSup'):
            if {child.tag for child in current} != {qualified('e'), qualified('sup')}:
                raise ValueError('Unexpected superscript structure')
            return ('sup', children(required(current, 'e')), children(required(current, 'sup')))
        if tag == qualified('nary'):
            if {child.tag for child in current} != {qualified('naryPr'), qualified('sub'), qualified('sup'), qualified('e')}:
                raise ValueError('Unexpected summation structure')
            properties = required(current, 'naryPr')
            expected = {'chr': '∑', 'limLoc': 'undOvr', 'supHide': '1'}
            if len(properties) != len(expected):
                raise ValueError('Unexpected summation properties')
            for name, value in expected.items():
                if required(properties, name).get(qualified('val')) != value:
                    raise ValueError('Unexpected summation operator or limits')
            if children(required(current, 'sup')) != text(''):
                raise ValueError('Unexpected upper summation limit')
            return ('sum', children(required(current, 'sub')), children(required(current, 'e')))
        if tag == qualified('d'):
            if {child.tag for child in current} != {qualified('dPr'), qualified('e')}:
                raise ValueError('Unexpected delimiter structure')
            props = required(current, 'dPr')
            left = required(props, 'begChr').get(qualified('val'))
            right = required(props, 'endChr').get(qualified('val'))
            if len(props) != 2 or left is None or right is None:
                raise ValueError('Unexpected delimiter properties')
            return delimiter(left, right, children(required(current, 'e')))
        raise ValueError('Unsupported mathematical node: ' + str(tag))

    if node.tag != qualified('oMath'):
        raise ValueError('Expected m:oMath root')
    result = children(node)
    return result if result[0] == 'seq' else seq(result)
