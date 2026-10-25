"""Editable equation structure is evidence, not just flattened equation text."""
from copy import deepcopy
from io import BytesIO
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from reporting import word_math as math


class WordMathTests(unittest.TestCase):
    def test_equations_round_trip_structurally(self):
        from docx import Document
        for name, equation in math.EQUATIONS.items():
            with self.subTest(name=name):
                node = math.append_equation(Document().add_paragraph(), name)
                self.assertEqual(math.math_signature(node), equation['ast'])
                # Exercise the standard-library XML reader used by verifiers.
                self.assertEqual(math.math_signature(ET.fromstring(ET.tostring(node))), equation['ast'])

    def test_native_fractions_subscripts_and_floor_are_structural(self):
        from docx import Document
        ns = {'m': math.MATH_NS}
        loss = math.append_equation(Document().add_paragraph(), 'loss100')
        self.assertEqual(len(loss.findall('.//m:f', ns)), 1)
        self.assertEqual(loss.find('.//m:f/m:den/m:r/m:t', ns).text, 'N')
        self.assertEqual(loss.find('.//m:sSub/m:sub/m:r/m:t', ns).text, '100')
        excess = math.append_equation(Document().add_paragraph(), 'excess')
        floors = excess.findall('.//m:begChr', ns)
        self.assertIn('⌊', [x.get('{' + math.MATH_NS + '}val') for x in floors])

    def test_changed_denominator_minus_and_subscript_change_signature(self):
        from docx import Document
        ns = {'m': math.MATH_NS}
        original = math.append_equation(Document().add_paragraph(), 'delta_none100')
        for path, replacement in [('.//m:den/m:r/m:t', 'P'),
                                  ('.//m:sSub/m:sub/m:r/m:t', 'none,10')]:
            mutated = deepcopy(original); mutated.find(path, ns).text = replacement
            self.assertNotEqual(math.math_signature(mutated), math.EQUATIONS['delta_none100']['ast'])
        mutated = deepcopy(original)
        minus = next(x for x in mutated.findall('.//m:t', ns) if x.text == '−')
        minus.text = '+'
        self.assertNotEqual(math.math_signature(mutated), math.EQUATIONS['delta_none100']['ast'])

    def test_unknown_id_and_unrecognized_operators_fail(self):
        from docx import Document
        with self.assertRaises(KeyError):
            math.append_equation(Document().add_paragraph(), 'unknown')
        with self.assertRaises(KeyError):
            math.markdown_equation('unknown')
        node = ET.Element('{' + math.MATH_NS + '}oMath')
        ET.SubElement(node, '{' + math.MATH_NS + '}rad')
        with self.assertRaises(ValueError):
            math.math_signature(node)

    def test_ap_has_native_sum_and_cost_boundary_has_superscript(self):
        from docx import Document
        ns = {'m': math.MATH_NS}
        ap = math.append_equation(Document().add_paragraph(), 'ap')
        self.assertEqual(len(ap.findall('.//m:nary', ns)), 1)
        self.assertEqual(ap.find('.//m:nary/m:sub/m:r/m:t', ns).text, 'k')
        cost = math.append_equation(Document().add_paragraph(), 'cost_boundary')
        self.assertEqual(cost.find('.//m:sSup/m:sup/m:r/m:t', ns).text, '*')
        self.assertEqual(cost.find('.//m:f/m:den/m:r/m:t', ns).text, 'TP')

    def test_sum_index_operator_and_superscript_corruption_are_detected(self):
        from docx import Document
        ns = {'m': math.MATH_NS}
        original = math.append_equation(Document().add_paragraph(), 'ap')
        mutated = deepcopy(original); mutated.find('.//m:nary/m:sub/m:r/m:t', ns).text = 'j'
        self.assertNotEqual(math.math_signature(mutated), math.EQUATIONS['ap']['ast'])
        mutated = deepcopy(original)
        mutated.find('.//m:naryPr/m:chr', ns).set('{' + math.MATH_NS + '}val', '∏')
        with self.assertRaisesRegex(ValueError, 'operator or limits'):
            math.math_signature(mutated)
        cost = math.append_equation(Document().add_paragraph(), 'cost_boundary')
        cost.find('.//m:sSup/m:sup/m:r/m:t', ns).text = '2'
        self.assertNotEqual(math.math_signature(cost), math.EQUATIONS['cost_boundary']['ast'])

    def test_separate_verifier_checks_all_main_expressions(self):
        from docx import Document
        from reporting.verify_math import MAIN_EQUATION_IDS, verify_equations
        document = Document(); markdown = []
        for name in MAIN_EQUATION_IDS:
            math.append_equation(document.add_paragraph(), name)
            markdown.append(math.markdown_equation(name))
        body = ET.fromstring(ET.tostring(document._element.body))
        def check(condition, message):
            self.assertTrue(condition, message)
        verify_equations(body, '\n\n'.join(markdown), check)
        # A swapped numerator/denominator cannot pass with matching display text.
        fraction = body.find('.//{' + math.MATH_NS + '}f')
        denominator = fraction.find('{' + math.MATH_NS + '}den')
        denominator.find('.//{' + math.MATH_NS + '}t').text = 'wrong'
        with self.assertRaises(AssertionError):
            verify_equations(body, '\n\n'.join(markdown), check)

    def test_saved_docx_preserves_editable_math_and_markdown(self):
        from docx import Document
        document = Document()
        for name in math.EQUATIONS:
            math.append_equation(document.add_paragraph(), name)
            self.assertTrue(math.markdown_equation(name).startswith('$$\n'))
        package_bytes = BytesIO(); document.save(package_bytes)
        with ZipFile(package_bytes) as package:
            tree = ET.fromstring(package.read('word/document.xml'))
            self.assertFalse(any(name.startswith('word/media/') for name in package.namelist()))
        nodes = tree.findall('.//{' + math.MATH_NS + '}oMath')
        self.assertEqual([math.math_signature(x) for x in nodes],
                         [x['ast'] for x in math.EQUATIONS.values()])

    def test_boundary_cannot_replace_total_or_omit_fully_selected_detections(self):
        from docx import Document
        from reporting.verify_math import verify_equations
        ids = ('tie_expectation', 'total_expectation', 'expected_loss')
        document = Document()
        for name in ids:
            math.append_equation(document.add_paragraph(), name)
        body = ET.fromstring(ET.tostring(document._element.body))
        markdown = '\n\n'.join(math.markdown_equation(name) for name in ids)
        ns = {'m': math.MATH_NS}
        def check(condition, message):
            self.assertTrue(condition, message)
        verify_equations(body, markdown, check, ids)
        # Both totals must retain their explicit scope even if text looks similar.
        for target in (1, 2):
            mutated = deepcopy(body)
            equation = mutated.findall('.//m:oMath', ns)[target]
            index = next(x for x in equation.findall('.//m:sSub/m:sub/m:r/m:t', ns)
                         if x.text == 'total')
            index.text = 'boundary'
            with self.assertRaises(AssertionError):
                verify_equations(mutated, markdown, check, ids)
        mutated = deepcopy(body)
        equation = mutated.findall('.//m:oMath', ns)[1]
        term = next(x for x in equation.findall('m:sSub', ns)
                    if x.find('m:sub/m:r/m:t', ns).text == 'fully selected')
        equation.remove(term)
        with self.assertRaises(AssertionError):
            verify_equations(mutated, markdown, check, ids)


if __name__ == '__main__':
    unittest.main()
