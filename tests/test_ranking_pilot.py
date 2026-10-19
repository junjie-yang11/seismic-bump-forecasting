"""Equal-allocation, tie, and reranking behavior rather than frozen-alert resampling."""
import itertools
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
from phase2.ranking.run import rank_queue,assess,allocation_pmf
from phase2.ranking.verify import weighted_detection,verify


class RankingPilotTests(unittest.TestCase):
    def test_grade_allocations_and_exact_k(self):
        g=np.array([0,0,1,1]);s=np.array([.9,.8,.2,.1]);keys=np.arange(4)/5
        p=rank_queue(g,s,keys,[.25,.75])
        np.testing.assert_array_equal(p[0]['grade_ml'],[False,False,True,False])
        np.testing.assert_array_equal(p[0]['global_ml'],[True,False,False,False])
        self.assertEqual(p[1]['quotas'],{1:2,0:1})
        for q,k in zip(p,(1,3)):
            self.assertEqual(q['grade_ml'].sum(),k);self.assertEqual(q['global_ml'].sum(),k)
            self.assertAlmostEqual(q['random_probability'].sum(),k)

    def test_labels_change_evaluation_but_not_decisions(self):
        g=[1,1,0,0];s=[.1,.2,.9,.8];keys=[.4,.3,.2,.1]
        a,pa,_=assess([0,1,0,1],g,s,keys,[.25]);b,pb,_=assess([1,0,1,0],g,s,keys,[.25])
        np.testing.assert_array_equal(pa[0]['grade_ml'],pb[0]['grade_ml'])
        self.assertNotEqual(a[0]['grade_ml_tp'],b[0]['grade_ml_tp'])

    def test_tied_model_scores_use_shared_label_independent_keys(self):
        p=rank_queue([1,1,1],[.5,.5,.5],[.8,.1,.4],[1/3])[0]
        np.testing.assert_array_equal(p['grade_ml'],[False,True,False])
        np.testing.assert_array_equal(p['global_ml'],p['grade_ml'])

    def test_exact_random_distribution_against_exhaustive_allocations(self):
        y=np.array([1,0,1,0,0]);g=np.ones(5)
        counts=np.bincount([int(y[list(indices)].sum()) for indices in itertools.combinations(range(5),2)],minlength=3)/10
        np.testing.assert_allclose(allocation_pmf(g,y,{1:2}),counts,rtol=0,atol=1e-15)

    def test_zero_full_and_zero_positive_queues(self):
        result,policies,pmfs=assess([0,0,0],[0,1,1],[.1,.2,.3],[.1,.2,.3],[0,1],True)
        self.assertEqual([r['k'] for r in result],[0,3])
        self.assertTrue(all(r['extra_grade_ml_tp']==0 for r in result))
        for p in pmfs:np.testing.assert_array_equal(p,[1.])

    def test_bootstrap_queue_must_be_reranked(self):
        g=np.ones(4);s=np.arange(4.);keys=np.arange(4.)
        original=rank_queue(g,s,keys,[.5])[0]['grade_ml']
        indices=np.array([0,0,1,3])
        # Merely reusing original flags fills one slot; reranking fills exactly two.
        self.assertEqual(original[indices].sum(),1)
        reranked=rank_queue(g[indices],s[indices],keys[indices],[.5])[0]['grade_ml']
        self.assertEqual(reranked.sum(),2)

    def test_weighted_prefix_matches_expanded_tied_queue(self):
        y=np.array([1,0,1]);g=np.ones(3);s=np.array([.2,.2,.1]);keys=np.array([.4,.1,.3])
        counts=np.array([2,3,1]);indices=np.repeat(np.arange(3),counts)
        selected=rank_queue(g[indices],s[indices],keys[indices],[.5])[0]['grade_ml']
        order=np.array([1,0,2])
        self.assertEqual(weighted_detection(y,counts,order,3),y[indices][selected].sum())

    def test_loss_identity_at_equal_k(self):
        y=np.array([1,0,1,0]);a=np.array([1,0,0,1],bool);b=np.array([1,0,1,0],bool);r=10
        loss=lambda flags:r*np.sum((y==1)&(~flags))+np.sum((y==0)&flags)
        self.assertEqual(loss(a)-loss(b),-(r+1)*(y[a].sum()-y[b].sum()))

    def test_invalid_inputs_rejected(self):
        for g,s,k,b in [([],[],[],[.1]),([9],[.1],[.1],[.1]),([1],[np.nan],[.1],[.1]),([1],[.2],[.1],[1.1])]:
            with self.assertRaises(ValueError):rank_queue(g,s,k,b)

    def test_failed_verification_revokes_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'results/phase2/ranking';out.mkdir(parents=True)
            path=out/'verification.json';path.write_text(json.dumps(dict(passed=True)))
            with self.assertRaises(FileNotFoundError):verify(root)
            self.assertFalse(json.loads(path.read_text())['passed'])

    def test_report_failure_revokes_success_and_old_pdf(self):
        from reporting import ranking,verify_ranking
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'reports/ranking';out.mkdir(parents=True)
            path=out/'verification.json';path.write_text(json.dumps(dict(passed=True)))
            stale=out/(ranking.STEM+'.pdf');stale.write_bytes(b'%PDF-old')
            with patch.object(ranking,'ROOT',root),patch.object(ranking,'DEST',out):
                with self.assertRaises(FileNotFoundError):ranking.build()
            self.assertFalse(stale.exists());self.assertFalse(json.loads(path.read_text())['passed'])
            path.write_text(json.dumps(dict(passed=True)))
            with self.assertRaises(FileNotFoundError):verify_ranking.verify(root)
            self.assertFalse(json.loads(path.read_text())['passed'])


if __name__=='__main__':unittest.main()
