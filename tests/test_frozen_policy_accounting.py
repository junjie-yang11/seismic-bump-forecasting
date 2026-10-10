"""Decision value and scenario semantics, including policies issuing no alerts."""
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from phase2.supplement import cost_boundary, scenario_precision


class FrozenPolicyAccountingTests(unittest.TestCase):
    def test_failed_supplement_rebuild_revokes_previous_success(self):
        from phase2 import supplement
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            record=out/'supplement_verification.json'
            record.write_text(json.dumps(dict(passed=True)))
            with patch.object(supplement,'OUT',out),patch.object(supplement,'_build',side_effect=RuntimeError('partial rebuild')):
                with self.assertRaisesRegex(RuntimeError,'partial rebuild'):supplement.build()
            state=json.loads(record.read_text())
            self.assertFalse(state['passed']);self.assertEqual(state['status'],'failed')
            self.assertEqual(state['error'],'partial rebuild')

    def test_cost_boundary_changes_loss_sign_without_changing_decisions(self):
        y=np.array([1,0,0,0,1])
        alerts=np.array([True,True,True,False,False])
        tp=int(np.sum(alerts & (y==1))); fp=int(np.sum(alerts & (y==0)))
        equality,status=cost_boundary(tp,fp)
        self.assertEqual((equality,status),(2.,'finite'))
        # Compare policy and no-alarm losses directly, retaining the same alerts.
        for cost,sign in [(1,1),(2,0),(3,-1)]:
            policy=cost*np.sum(~alerts & (y==1))+fp
            no_alarm=cost*np.sum(y==1)
            self.assertEqual(np.sign(policy-no_alarm),sign)
        np.testing.assert_array_equal(alerts,[True,True,True,False,False])

    def test_no_alarm_and_false_alerts_have_different_boundary_statuses(self):
        for counts,status in [((0,0),'no_alarm_equivalent'),((0,3),'never_improves')]:
            boundary,label=cost_boundary(*counts)
            self.assertTrue(np.isnan(boundary));self.assertEqual(label,status)
        self.assertEqual(cost_boundary(2,0),(0.,'finite'))

    def test_invalid_confusion_counts_are_rejected(self):
        for counts in [(-1,0),(1,-1),(.5,2),(1,np.nan),(np.inf,1)]:
            with self.assertRaises(ValueError):cost_boundary(*counts)

    def test_precision_uses_class_masses_instead_of_average_class_precision(self):
        # 100 hypothetical shifts: 10 positives, TPR .5, FPR 1/9.
        # Expected alerts comprise 5 true and 10 false alerts.
        precision=scenario_precision(.1,.5,1/9)
        self.assertAlmostEqual(float(precision),5/15)

    def test_no_expected_alerts_has_undefined_precision(self):
        values=scenario_precision([.02,.05,.10,.15],1.,0.)
        self.assertTrue(np.isnan(values).all())
        self.assertEqual(float(scenario_precision(.1,0.,0.)),1.)
        self.assertEqual(float(scenario_precision(.1,1.,.5)),0.)

    def test_prevalence_endpoints_and_invalid_rates(self):
        self.assertEqual(float(scenario_precision(0.,.5,.1)),0.)
        self.assertEqual(float(scenario_precision(1.,.5,.1)),1.)
        self.assertTrue(np.isnan(scenario_precision(1.,1.,.1)))
        self.assertTrue(np.isnan(scenario_precision(.1,np.nan,.2)))
        self.assertTrue(np.isnan(scenario_precision(.1,.2,np.nan)))
        for values in [(-.1,.2,.3),(.1,1.1,.3),(.1,.2,np.inf)]:
            with self.assertRaises(ValueError):scenario_precision(*values)


if __name__=='__main__':unittest.main()
