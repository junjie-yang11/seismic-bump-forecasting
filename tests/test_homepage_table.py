"""Check the complete display against the retained computed counts."""
from pathlib import Path
import unittest

from phase2.update_readme import decision_table, update


class HomepageEvidence(unittest.TestCase):
    def test_generated_table_and_five_percent_rounding(self):
        root = Path(__file__).resolve().parents[1]
        table = decision_table(root/'results/phase2/decision_value_pooled.csv')
        self.assertIn('| 5% | +0.68 | 1 | 87 | 25 |', table)
        self.assertIn('2,063 shifts; 88 hazardous labels', table)
        update(root, check=True)


if __name__ == '__main__':
    unittest.main()
