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
