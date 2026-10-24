"""Tie expectations, changing queues and historical fitting isolation."""
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
from phase2.information.run import inclusion_probabilities,expected_detections,fit_design


class InformationTests(unittest.TestCase):
    def test_uniform_boundary_ties_equal_enumerated_allocations(self):
        g=np.array([1,0,0,0]);s=np.array([.1,.8,.8,.8]);y=np.array([1,1,0,1])
        p=inclusion_probabilities(g,s,.5)
        np.testing.assert_allclose(p,[1,1/3,1/3,1/3])
        outcomes=[y[[0,i]].sum() for i in (1,2,3)]
        self.assertAlmostEqual(p@y,np.mean(outcomes));self.assertAlmostEqual(p.sum(),2)

    def test_probabilities_are_label_free_and_order_invariant(self):
        g=np.array([0,1,0,1]);s=np.array([.4,.1,.4,.9]);order=np.array([3,1,0,2])
        p=inclusion_probabilities(g,s,.75)
        np.testing.assert_array_equal(p[order],inclusion_probabilities(g[order],s[order],.75))
        np.testing.assert_array_equal(inclusion_probabilities(g,s,0),np.zeros(4))
        np.testing.assert_array_equal(inclusion_probabilities(g,s,1),np.ones(4))

    def test_weighted_reranking_matches_explicit_duplicate_queue(self):
        y=np.array([1,0,1,0]);g=np.array([1,0,0,0]);s=np.array([.1,.8,.8,.2])
        draws=np.array([[0,2,1,1],[2,0,2,0],[1,1,1,1]])
        budgets=[0,.25,.5,1]
        got=expected_detections(y,g,s,draws,budgets)
        for i,w in enumerate(draws):
            ix=np.repeat(np.arange(4),w)
            for j,b in enumerate(budgets):
                self.assertAlmostEqual(got[i,j],inclusion_probabilities(g[ix],s[ix],b)@y[ix])
        # Resampling saved inclusion probabilities would fail on this draw.
        self.assertNotAlmostEqual(got[0,2],np.dot(draws[0]*y,inclusion_probabilities(g,s,.5)))

    def test_zero_positive_draws_and_identical_scores_are_retained(self):
        g=np.zeros(3);s=np.ones(3);counts=np.array([[1,1,1],[0,3,0]])
        r=expected_detections([1,0,1],g,s,counts,[1/3])
        self.assertAlmostEqual(r[0,0],2/3);self.assertEqual(r[1,0],0)

    def test_invalid_inputs_rejected(self):
        for b in (-.1,1.1,float('nan')):
            with self.assertRaises(ValueError):inclusion_probabilities([0],[.1],b)
        with self.assertRaises(ValueError):inclusion_probabilities([0],[float('nan')],.5)
        with self.assertRaises(ValueError):expected_detections([0],[0],[.1],[[.5]],[.5])
        with self.assertRaises(ValueError):expected_detections([0],[0],[.1],[[0]],[.5])

    def test_reference_and_future_labels_never_enter_fit_or_tuning(self):
        from phase2.information import run as module
        X=np.arange(20,dtype=float).reshape(10,2);y=np.array([0,1]*5,dtype=float)
        calls=[]
        class FakeModel:
            def __init__(self,*args,**kwargs):pass
            def fit(self,x,yy):calls.append(('fit',x.copy(),yy.copy()));return self
            def predict_proba(self,x):return x[:,0]/20
        def choose(x,yy,*args):
            calls.append(('tune',x.copy(),yy.copy()));return (2,80),[],np.array([0,1]),np.array([2,3]),[]
        with patch.object(module,'BoostedModel',FakeModel),patch.object(module,'select_parameters',side_effect=choose):
            first=fit_design(X,y,np.arange(4),np.array([8,9]),['x','z'])
            changed=y.copy();changed[4:]=1-changed[4:]
            second=fit_design(X,changed,np.arange(4),np.array([8,9]),['x','z'])
        np.testing.assert_array_equal(first[1],second[1])
        for _,x,yy in calls:
            np.testing.assert_array_equal(x,X[:4]);np.testing.assert_array_equal(yy,y[:4])

    def test_invalid_fit_indices_are_rejected_before_fitting(self):
        X=np.arange(20,dtype=float).reshape(10,2);y=np.array([0,1]*5,dtype=float)
        for fit,test in (([-1,0],[8,9]),([0,0],[8,9]),([0.5,1],[8,9]),([0,1],[1,2]),([5,6],[3,4])):
            with self.assertRaises(ValueError):fit_design(X,y,fit,test,['x','z'])

    def test_failed_experiment_revokes_previous_success(self):
        from phase2.information.run import run
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'results/phase2/information';out.mkdir(parents=True)
            record=out/'verification.json';record.write_text(json.dumps({'passed':True}))
            with self.assertRaises(FileNotFoundError):run(root)
            self.assertFalse(json.loads(record.read_text())['passed'])
            self.assertEqual(json.loads((out/'run_manifest.json').read_text())['status'],'failed')


if __name__=='__main__':unittest.main()
