"""Behavioral checks of the declared decisions and data boundaries."""
import unittest
import numpy as np
from unittest.mock import patch
from .decisions import candidates,select,batch_topk,evaluate
from .experiment import fit_fold,validate_model_settings

class DecisionTests(unittest.TestCase):
    def test_evaluation_accepts_binary_numeric_decisions(self):
        for dtype in (bool, int, float):
            result = evaluate([1,0,1,0], np.array([1,1,0,0], dtype=dtype), 10, .25)
            self.assertEqual([result[k] for k in ('tp','fp','fn','tn','loss','alerts','excess')],
                             [1,1,1,1,11,2,1])
        for decisions in ([1,.5,0,0], [1,np.nan,0,0]):
            with self.assertRaises(ValueError): evaluate([1,0,1,0], decisions, 10)

    def test_evaluation_rejects_invalid_capacity_budgets(self):
        for budget in (-.1, 1.1, np.nan, np.inf):
            with self.assertRaisesRegex(ValueError, 'Budget'):
                evaluate([1,0], [1,0], 10, budget)

    def test_imported_settings_cannot_silently_change_locked_protocol(self):
        with patch.dict('boosting.PARAMETERS',{'eta':.2}):
            with self.assertRaisesRegex(ValueError,'locked protocol'):
                validate_model_settings()

    def test_failed_rerun_invalidates_previous_verification(self):
        import json
        import tempfile
        from pathlib import Path
        from . import run as runner
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            (out/'verification.json').write_text(json.dumps({'passed':True,'replay':True}))
            with patch.object(runner,'OUT',out),patch.object(runner,'_run',side_effect=RuntimeError('test failure')):
                with self.assertRaises(RuntimeError): runner.run()
            self.assertFalse(json.loads((out/'verification.json').read_text())['passed'])
            self.assertEqual(json.loads((out/'run_manifest.json').read_text())['status'],'failed')

    def test_canonical_groups_and_extremes(self):
        s=np.array([.8,.8,.3,.1]); y=np.array([1,0,1,0]); c=candidates(s,y)
        self.assertEqual(c.alerts.tolist(),[0,2,3,4])
        self.assertEqual(c.threshold.tolist(),[np.inf,.8,.3,-np.inf])
        for _,row in c.iterrows(): self.assertEqual(int((s>=row.threshold).sum()),row.alerts)

    def test_cost_ties_choose_fewer_alerts_and_zero_gap(self):
        c=candidates([.9,.1],[0,1])
        b=select(c,'B',cost=1)
        self.assertEqual(b['reference_alerts'],0)
        self.assertEqual(b['optimal_decisions'],2)
        self.assertEqual(b['loss_gap'],0)

    def test_capacity_and_unconstrained_loss_order(self):
        c=candidates([.9,.8,.7,.2],[1,0,1,0])
        for b in [0,.01,.5,1]:
            for r in [5,10,20,50]:
                constrained=select(c,'C',b,r); unconstrained=select(c,'B',cost=r)
                self.assertLessEqual(constrained['reference_alerts'],int(b*4))
                self.assertGreaterEqual(constrained['reference_loss'],unconstrained['reference_loss'])

    def test_no_positive_reference_and_zero_slots(self):
        c=candidates([.5,.5,.1],[0,0,0])
        self.assertEqual(select(c,'B',cost=50)['threshold'],np.inf)
        self.assertEqual(select(c,'C',.5,50)['threshold'],np.inf)
        self.assertEqual(select(c,'A',.01)['threshold'],np.inf)

    def test_batch_topk_does_not_split_boundary_ties(self):
        alert,t=batch_topk([.8,.8,.3,.1],.25)
        self.assertEqual(int(alert.sum()),0)
        alert,t=batch_topk([.8,.8,.3,.1],.5)
        self.assertEqual(alert.tolist(),[True,True,False,False])

    def test_future_capacity_can_exceed_reference_capacity(self):
        c=candidates([.9,.7,.3,.1],[1,0,0,0]); a=select(c,'A',.25)
        result=evaluate([1,0,0,0],np.array([.95,.92,.91,.2])>=a['threshold'],10,.25)
        self.assertEqual(result['excess'],2)

    def test_test_labels_cannot_change_parameters_scores_or_rules(self):
        rng=np.random.default_rng(23); X=rng.normal(size=(160,2)); y=(X[:,0]>.3).astype(float)
        tr=np.arange(120); te=np.arange(120,160)
        changed=y.copy(); changed[te]=1-changed[te]
        for model in ('LR','CART','XGBoost'):
            with self.subTest(model=model):
                original=fit_fold(model,X,y,tr,te,['a','b'])
                future=fit_fold(model,X,changed,tr,te,['a','b'])
                self.assertEqual(original['manifest'],future['manifest'])
                self.assertEqual(original['tuning'],future['tuning'])
                for k in ('reference_score','fixed_score','refitted_score'): np.testing.assert_array_equal(original[k],future[k])
                reference=np.array(original['manifest']['reference_rows'])
                for mechanism in ('A','B','C'):
                    a=select(candidates(original['reference_score'],y[reference]),mechanism,.1 if mechanism!='B' else None,10 if mechanism!='A' else None)
                    b=select(candidates(future['reference_score'],changed[reference]),mechanism,.1 if mechanism!='B' else None,10 if mechanism!='A' else None)
                    self.assertEqual(a['threshold'],b['threshold'])
                    for workflow in ('fixed_score','refitted_score'):
                        np.testing.assert_array_equal(original[workflow]>=a['threshold'],future[workflow]>=b['threshold'])

    def test_policy_reference_labels_do_not_fit_or_tune_fixed_model(self):
        rng=np.random.default_rng(3); X=rng.normal(size=(160,2)); y=(X[:,0]>.1).astype(float)
        for model in ('LR','CART','XGBoost'):
            with self.subTest(model=model):
                original=fit_fold(model,X,y,np.arange(120),np.arange(120,160),['a','b'])
                changed=y.copy(); reference=original['manifest']['reference_rows']; changed[reference]=1-changed[reference]
                other=fit_fold(model,X,changed,np.arange(120),np.arange(120,160),['a','b'])
                self.assertEqual(original['tuning'],other['tuning'])
                for key in ('fixed_score','reference_score'):
                    np.testing.assert_array_equal(original[key],other[key])
                self.assertTrue(set(original['manifest']['fit_rows']).isdisjoint(reference))
                if model == 'XGBoost':
                    self.assertTrue(set(original['manifest']['tuning_fit_rows']).isdisjoint(reference))
                    self.assertTrue(set(original['manifest']['tuning_reference_rows']).isdisjoint(reference))

if __name__=='__main__': unittest.main()
