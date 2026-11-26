"""Independent path oracle for finite integration before regret clipping."""
import json,os,unittest
import numpy as np
from gto.qualification.private_integrated_joint import FiniteIntegratedJoint
from gto.qualification.multiplayer_joint import Joint,expanded_decks,path_oracle,path_br
from gto.qualification.build import load
from gto.native.training import NativeGame


def canonical(key):
    d=json.loads(key)
    if d['round']==0:
        lo,hi=sorted(c//4 for c in d['own']);suited=d['own'][0]%4==d['own'][1]%4
        d['own']=[4*lo,4*hi+(0 if lo!=hi and suited else 1)]
    return json.dumps(d,sort_keys=True,separators=(',',':'))

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class IntegratedJoint(unittest.TestCase):
    def test_native_off_half_BB_grid_min_raise_allin_and_short_allin(self):
        _,native=load(os.environ['QUALIFICATION_BUILD'])
        q=native.NativeState(NativeGame([41,43],bb=4))
        for c in (48,49,0,1):q.apply_action(c)
        self.assertIn(43,q.legal_actions())  # SB all-in to41chips =10.25BB.
        q.apply_action(13)  # raise-to11chips =2.75BB.
        q.apply_action(20)  # raise-to18chips; last full increment7.
        self.assertIn(27,q.legal_actions())  # min-to25chips =6.25BB.
        self.assertNotIn(26,q.legal_actions())
        short=native.NativeState(NativeGame([7,23],bb=4))
        for c in (48,49,0,1):short.apply_action(c)
        self.assertEqual(short.legal_actions(),[0,1,9])
        short.apply_action(9)  # short all-in to7<required8chips.
        self.assertEqual(short.legal_actions(),[0,1])
        short.apply_action(1)
        for c in (4,9,14,19,24):
            if short.is_chance_node():short.apply_action(c)
        self.assertTrue(short.is_terminal());self.assertAlmostEqual(sum(short.returns()),0.)

    def test_all_owner_raw_regret_average_and_resume_match_independent_paths(self):
        _,native=load(os.environ['QUALIFICATION_BUILD']);game=NativeGame([24,22,20]);ds=expanded_decks(3)
        exact=Joint(native,game,ds,[.25]*4,action_scope='preflop',max_nodes=5000,max_seconds=30)
        q=FiniteIntegratedJoint(native,game,decks=ds,weights=[.25]*4,action_scope='preflop',max_nodes=100000,max_seconds=30)
        for _ in range(2):
            beforeR={k:v.copy() for k,v in q.R.items()};beforeA={k:v.copy() for k,v in q.A.items()}
            pi={k:q.policy(False).get(canonical(k),np.ones(len(a))/len(a)) for k,a in exact.actions.items()}
            oracle=path_oracle(exact,pi);q.step()
            for key,a in exact.actions.items():
                if len(a)==1:continue
                c=canonical(key)
                np.testing.assert_allclose(q.R[c],np.maximum(0,beforeR.get(c,np.zeros(len(a)))+oracle['grad'][key]),atol=2e-11)
                np.testing.assert_allclose(q.A[c],beforeA.get(c,np.zeros(len(a)))+q.t*oracle['avg'][key],atol=2e-11)
        clone=FiniteIntegratedJoint(native,game,decks=ds,weights=[.25]*4,action_scope='preflop',max_nodes=100000,max_seconds=30)
        clone.restore(q.state());q.step();clone.step();self.assertEqual(q.state(),clone.state())
        with self.assertRaises(ValueError):FiniteIntegratedJoint(native,NativeGame([24]*6),decks=expanded_decks(6),weights=[.25]*4)

if __name__=='__main__':unittest.main()
