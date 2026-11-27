"""N-owner chance stratification: exact proposal law and raw-CF oracle."""
import os,random,unittest
import numpy as np
from gto.qualification.stream_multiplayer import Stratified,systematic_indices
from gto.qualification.stream_chance import strata
from gto.qualification.multiplayer_joint import Joint,expanded_decks,path_oracle
from gto.qualification.build import load
from gto.native.training import NativeGame

class StrataProposal(unittest.TestCase):
    def test_systematic_CDF_expected_mass_equals_exact_target(self):
        weights=np.array(list(strata().values()))
        for K in (1,2,4,13):
            cuts={0.,1.}
            for z in np.cumsum(weights):
                for j in range(K):
                    x=K*z-j
                    if 0<x<1:cuts.add(float(x))
            cuts=sorted(cuts);got=np.zeros(len(weights))
            for a,b in zip(cuts,cuts[1:]):got+=np.bincount(systematic_indices(weights,K,min(np.nextafter(1.,0.),(a+b)/2)),minlength=len(weights))*(b-a)/K
            np.testing.assert_allclose(got,weights,atol=2e-15)

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class NOwner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):_,cls.native=load(os.environ['QUALIFICATION_BUILD'])
    def test_all_finite_chance_raw_CF_matches_independent_three_owner_oracle(self):
        decks=expanded_decks(3);game=NativeGame([24,22,20]);joint=Joint(self.native,game,decks,[.25]*4,max_nodes=5000,action_scope='preflop')
        q=Stratified(self.native,game,seed=17150201,decks=decks,weights=[.25]*4,chance_batch=4,max_nodes=100000,max_seconds=30)
        pi=joint.policy(False);expected=path_oracle(joint,pi);q._draw();grads={};avg={}
        for owner in range(3):
            part=q.collect(owner,q.batch[0][0],random.Random(owner+13),pi,audit=True)
            for key,v in part['grad'].items():grads[key]=grads.get(key,np.zeros(len(v)))+v
            for key,v in part['avg'].items():avg[key]=avg.get(key,np.zeros(len(v)))+v/2
        for key,v in expected['grad'].items():np.testing.assert_allclose(grads[key],v,atol=1e-10)
        for key,v in expected['avg'].items():np.testing.assert_allclose(avg[key],v,atol=1e-10)
    def test_six_nine_conditional_decks_information_and_resume(self):
        from gto.qualification.stream_chance import flop_features
        from gto.qualification.fullstreet_solver import public_code
        for n in (6,9):
            q=Stratified(self.native,NativeGame([12]*n),seed=17150201+n,chance_batch=2,max_nodes=20000,max_seconds=10,average_mode='lazy')
            first=q._draw()
            for deck,w in q.batch:
                self.assertEqual(len(deck),52);self.assertEqual(len(set(deck)),52);self.assertEqual(w,.5)
                board=deck[2*n:2*n+5];self.assertIn((public_code(board),*flop_features(board)[1:]),strata())
            state=q.state();r=Stratified(self.native,q.game,seed=17150201+n,chance_batch=2,max_nodes=20000,max_seconds=10,average_mode='lazy');r.restore(state)
            q.step();r.step();self.assertEqual(q.state(),r.state())
