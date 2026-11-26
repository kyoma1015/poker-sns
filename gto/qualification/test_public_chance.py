"""Independent dense private-pair oracle for the integrated PCS kernel."""
import ctypes as C
import tempfile
import unittest
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification import public_chance_solver as p, fullstreet_solver as f

class PublicChance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.lib=p.build(cls.tmp.name)
        cls.b=p.block(cls.lib,[0,5,10,15,20])
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def dense(self,b):
        h=b['holes'];r=b['ranks'];valid=~(h[:,None,:,None]==h[None,:,None,:]).any(axis=(2,3))
        return dict(public=b['public'],codes=b['codes'],weight=b['weight'],
                    mass=valid/1070190.,equity=(r[:,None]>r[None,:])+.5*(r[:,None]==r[None,:]))
    def test_rank_prefix_card_removal_matches_direct_all_pairs(self):
        b=self.b;h=b['holes'];r=b['ranks'];rng=np.random.default_rng(91)
        for opp in (np.ones(1081),rng.random(1081),np.eye(1,1081,37).ravel()):
            mass=np.empty(1081);win=mass.copy();ptr=lambda x:x.ctypes.data_as(model.DP)
            self.assertEqual(self.lib.pcs_terminal(1081,model.ints(h.ravel()),model.ints(r),ptr(opp),ptr(mass),ptr(win)),0)
            d=self.dense(b);np.testing.assert_allclose(mass,d['mass']@opp*1070190,atol=5e-12)
            np.testing.assert_allclose(win,(d['mass']*d['equity'])@opp*1070190,atol=5e-12)
    def test_regret_average_ev_br_and_action_ev_match_frozen_dense_kernel(self):
        nodes=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5,c1=0),
               dict(actor=1,children=[3,4],round=3),dict(actor=-1,children=[],round=3,c0=-3,c1=6),
               dict(actor=-1,children=[],round=3,c0=2,c1=0)]
        q=p.Game(self.lib,nodes,[self.b]);d=f.Game(self.lib,nodes,[self.dense(self.b)])
        rng=np.random.default_rng(71);q.R[:]=rng.random(q.S);d.R[:]=q.R;pi=q.policy(False)
        for owner in (0,1):
            got=q.evaluate_owner(pi,owner);expected=d.evaluate_owner(pi,owner)
            np.testing.assert_allclose(got,expected,atol=1e-11)
            for a,b in zip((q.grad,q.avg,q.den,q.num,q.evden),(d.grad,d.avg,d.den,d.num,d.evden)):
                np.testing.assert_allclose(a,b,atol=1e-11)
        # Independent simultaneous CFR+ update, including visits and linear average.
        expectedR=q.R.copy();expectedA=q.A.copy()
        for owner in (0,1):
            d.evaluate_owner(pi,owner)
            for start,t,n,k in q.rows:
                if nodes[k]['actor']==owner:
                    sl=slice(start,start+t*n);expectedR[sl]=np.maximum(0,q.R[sl]+d.grad[sl]);expectedA[sl]+=d.avg[sl]
        q.step();np.testing.assert_allclose(q.R,expectedR,atol=1e-11);np.testing.assert_allclose(q.A,expectedA,atol=1e-11)
    def test_weighted_public_chance_and_shared_prefix_BR_match_dense_oracle(self):
        nodes=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5,c1=0),
               dict(actor=1,children=[3,4],round=3),dict(actor=-1,children=[],round=3,c0=-3,c1=6),
               dict(actor=-1,children=[],round=3,c0=2,c1=0)]
        blocks=[dict(self.b,weight=.3),p.block(self.lib,[0,5,10,16,21],.7)]
        q=p.Game(self.lib,nodes,blocks);dense=f.Game(self.lib,nodes,[self.dense(b) for b in blocks])
        q.R[:]=np.random.default_rng(511).random(q.S);pi=q.policy(False)
        for owner in (0,1):
            np.testing.assert_allclose(q.evaluate_owner(pi,owner),dense.evaluate_owner(pi,owner),atol=2e-11)
            for a,b in zip((q.grad,q.avg,q.den),(dense.grad,dense.avg,dense.den)):
                np.testing.assert_allclose(a,b,atol=2e-11)

    def test_csr_more_than_four_actions_and_exact_checkpoint_replay(self):
        nodes=[dict(actor=0,children=list(range(1,8)),round=0)]+[dict(actor=-1,children=[],round=0,c0=float(i),c1=0) for i in range(7)]
        q=p.Game(self.lib,nodes,[self.b]);self.assertAlmostEqual(q.measure()['restricted_NC_bb'],3.,places=10)
        for _ in range(64):q.step()
        self.assertLess(q.measure()['restricted_NC_bb'],.01)
        path=Path(self.tmp.name)/'cp.npz';q.save(path);other=p.Game(self.lib,nodes,[self.b]);other.restore(path)
        q.step();other.step();np.testing.assert_array_equal(q.R,other.R);np.testing.assert_array_equal(q.A,other.A)
    def test_two_player_joint_convergence_and_current_range_recomputation(self):
        nodes=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5,c1=0),
               dict(actor=1,children=[3,4],round=3),dict(actor=-1,children=[],round=3,c0=-3,c1=6),
               dict(actor=-1,children=[],round=3,c0=2,c1=0)]
        q=p.Game(self.lib,nodes,[self.b]);curve=[]
        for target in (0,16,64,256):
            while q.t<target:q.step()
            curve.append(q.measure()['restricted_NC_bb'])
        self.assertLess(curve[-1],.005)
        self.assertLess(curve[-1],curve[1]);self.assertLess(curve[1],curve[0])
        # Opponent behavior changes the exact conditional action value immediately.
        pi=q.policy();q.evaluate_owner(pi,0);before=q.num.copy()
        start,t,n,k=q.rows[1];pi[start:start+t*n]=np.tile([1.,0.],t)
        q.evaluate_owner(pi,0);self.assertGreater(np.max(abs(q.num-before)),1e-5)

    def test_future_information_prefix_and_board_law_validation(self):
        a=p.block(self.lib,[0,5,10,15,20]);b=p.block(self.lib,[0,5,10,16,21]);own=(48,49)
        ca=a['codes'][np.where((a['holes']==own).all(axis=1))[0][0]]
        cb=b['codes'][np.where((b['holes']==own).all(axis=1))[0][0]]
        self.assertEqual(ca>>2,cb>>2);self.assertEqual(a['public']>>2,b['public']>>2)
        with self.assertRaises(ValueError):p.block(self.lib,[0,0,1,2,3])
        with self.assertRaises(ValueError):p.Game(self.lib,[dict(actor=-1,children=[],round=0)], [dict(a,weight=.5)])

if __name__=='__main__':unittest.main()
