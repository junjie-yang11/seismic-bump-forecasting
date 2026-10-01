import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from metrics import average_precision
from uncertainty import resample_indices,paired_ap_interval,_ap_groups,_weighted_ap

class UncertaintyTests(unittest.TestCase):
    def test_blocks_keep_phase_size_and_adjacency(self):
        fold=np.repeat([0,1],12)
        ix=resample_indices(np.random.default_rng(7),fold,4)
        self.assertEqual(len(ix),24)
        self.assertEqual((fold[ix]==0).sum(),12)
        for block in ix.reshape(-1,4):
            np.testing.assert_equal(np.diff(block),np.ones(3))
            self.assertEqual(len(np.unique(fold[block])),1)

    def test_identical_paired_predictions_have_zero_gap(self):
        y=(np.arange(48)%3==0).astype(float); p=np.linspace(0,1,48)
        result,samples=paired_ap_interval(y,np.vstack([p,p]),p,np.repeat([0,1],24),4,50)
        self.assertEqual(result['delta'],0)
        np.testing.assert_allclose(samples,0,atol=1e-15)
        self.assertAlmostEqual(result['ci_low'],0)
        self.assertAlmostEqual(result['ci_high'],0)

    def test_weighted_tied_ap_equals_explicit_resampling(self):
        y=np.array([0.,1.,1.,0.,1.]); p=np.array([.8,.8,.2,.1,.1])
        counts=np.array([3.,2.,1.,0.,2.]); ix=np.repeat(np.arange(5),counts.astype(int))
        self.assertAlmostEqual(_weighted_ap(y,counts,_ap_groups(y,p)),average_precision(y[ix],p[ix]))

    def test_deterministic_bootstrap(self):
        y=(np.arange(40)%4==0).astype(float); p=np.linspace(0,1,40)
        a,sa=paired_ap_interval(y,p,p[::-1],np.repeat([0,1],20),4,50,9)
        b,sb=paired_ap_interval(y,p,p[::-1],np.repeat([0,1],20),4,50,9)
        self.assertEqual(a,b); np.testing.assert_equal(sa,sb)
