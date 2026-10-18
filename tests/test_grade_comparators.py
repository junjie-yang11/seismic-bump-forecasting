"""Information isolation and canonical-grade edge cases for the supplement."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from phase2.comparators.run import choose,encode
from phase2.comparators.verify import verify

PLAN=dict(grade_order=['a','b','c','d'],budgets=[.01,.2],costs=[5,20])


class GradeRulesTests(unittest.TestCase):
    def test_future_grades_do_not_change_reference_choice(self):
        first=choose(['a','b','b','c'],[0,0,1,1],['a','d'],PLAN)
        second=choose(['a','b','b','c'],[0,0,1,1],['c','b'],PLAN)
        self.assertEqual([a['threshold'] for a in first[3]],[a['threshold'] for a in second[3]])

    def test_future_outcomes_only_change_evaluation(self):
        from phase2.decisions import evaluate
        result=choose(['a','b','c','c'],[0,0,1,1],['a','b','c','d'],PLAN)
        alerts=result[4]['B_r20'].copy();cutoff=[a['threshold'] for a in result[3]]
        one=evaluate([0,0,1,1],alerts,20);two=evaluate([1,1,0,0],alerts,20)
        repeat=choose(['a','b','c','c'],[0,0,1,1],['a','b','c','d'],PLAN)
        self.assertEqual(cutoff,[a['threshold'] for a in repeat[3]])
        np.testing.assert_array_equal(alerts,repeat[4]['B_r20'])
        self.assertNotEqual(one['loss'],two['loss'])

    def test_equal_grades_stay_together_and_capacity_is_historical(self):
        plan={**PLAN,'budgets':[.5]}
        result=choose(['a','a','b','b'],[0,0,1,0],['b']*6,plan)
        a=next(a for a in result[3] if a['rule']=='A_b50')
        self.assertEqual(a['reference_alerts'],2)
        self.assertTrue(result[4]['A_b50'].all())
        self.assertEqual(len(result[2]),3)

    def test_no_reference_positives_cost_rules_select_none(self):
        result=choose(['a','b','c'],[0,0,0],['d','b'],PLAN)
        for a in result[3]:
            if a['mechanism'] in ('B','C'):
                self.assertEqual(a['threshold'],float('inf'))
                self.assertFalse(result[4][a['rule']].any())

    def test_zero_slots_and_one_reference_score(self):
        result=choose(['b','b'],[1,0],['a','b','d'],PLAN)
        for a in result[3]:
            if a['mechanism'] in ('A','C'):self.assertEqual(a['threshold'],float('inf'))
        b=next(a for a in result[3] if a['rule']=='B_r20')
        self.assertEqual(b['threshold'],float('-inf'))
        self.assertTrue(result[4]['B_r20'].all())

    def test_canonical_cutoff_for_missing_reference_levels(self):
        plan={**PLAN,'budgets':[.5]}
        result=choose(['a','a','c','c'],[0,0,1,1],['a','b','c','d'],plan)
        a=next(a for a in result[3] if a['rule']=='A_b50')
        self.assertEqual(a['threshold'],2)
        np.testing.assert_array_equal(result[4]['A_b50'],[False,False,True,True])

    def test_unknown_or_empty_grades_rejected(self):
        for values in ([],['x'],['a',None]):
            with self.assertRaises(ValueError):encode(values)

    def test_equal_cost_optima_choose_fewer_alerts(self):
        result=choose(['a','b'],[1,0],['a','b','d'],{**PLAN,'costs':[1]})
        b=next(a for a in result[3] if a['rule']=='B_r01')
        self.assertEqual(b['optimal_decisions'],2)
        self.assertEqual(b['threshold'],float('inf'))
        self.assertFalse(result[4]['B_r01'].any())

    def test_failed_current_verification_revokes_old_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);out=root/'results/phase2/comparators';out.mkdir(parents=True)
            record=out/'verification.json';record.write_text(json.dumps(dict(passed=True)))
            with self.assertRaises(FileNotFoundError):verify(root)
            self.assertFalse(json.loads(record.read_text())['passed'])


if __name__=='__main__':unittest.main()
