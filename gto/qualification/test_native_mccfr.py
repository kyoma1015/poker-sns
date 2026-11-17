import itertools
import json
import math
import os
import random
import unittest
from gto.abstract.matched_history import python_oracle
from gto.qualification.build import load
from gto.qualification.native_mccfr import Solver, betting, digest, outcome_updates, rollout
from gto.qualification.public_response import observe
from gto.qualification.policy import act, legal
from gto.native.training import NativeGame


class OutcomeEstimator(unittest.TestCase):
    def test_expected_estimator_matches_independent_matched_history_cf_vectors(self):
        # Own action -> opponent action -> another own action. Exact enumerate
        # sampling paths, checking both owners and counterfactual own reach.
        ns=[dict(actor=0,children=[1,2]),dict(actor=1,children=[3,4]),
            dict(actor=-1,children=[],c0=2,c1=0),dict(actor=0,children=[5,6]),
            dict(actor=-1,children=[],c0=-3,c1=0),
            dict(actor=-1,children=[],c0=5,c1=0),dict(actor=-1,children=[],c0=-7,c1=0)]
        g=dict(nodes=ns,worlds=[dict(mass=1.,equity=0.)],info=[0,2,0,4,0,0,0])
        pi=[.3,.7,.4,.6,.2,.8];exact=python_oracle(g,pi)
        for owner in (0,1):
            expected=[0.]*6;average=[0.]*6
            def walk(k,prob,logq,ownq,reach,records):
                n=ns[k]
                if n['actor']<0:
                    for obs,row,delta,weight in outcome_updates(records,n['c0']*(1 if owner==0 else -1)):
                        for a in range(2):
                            expected[obs+a]+=prob*delta[a]
                            average[obs+a]+=prob*weight*row[a]
                    return
                i=g['info'][k];row=pi[i:i+2]
                q=[.3+.4*w for w in row] if n['actor']==owner else row
                for a,c in enumerate(n['children']):
                    own=n['actor']==owner
                    rec=records+[(i,row,a,q[a],ownq,reach*math.exp(-logq))] if own else records
                    walk(c,prob*q[a],logq+math.log(q[a]),ownq+(math.log(q[a]) if own else 0),reach*(row[a] if own else 1),rec)
            walk(0,1.,0.,0.,1.,[])
            for node in (0,1,3):
                if ns[node]['actor']==owner:
                    i=g['info'][node]
                    for a in range(2):
                        self.assertAlmostEqual(expected[i+a],exact['grad'][i+a],places=12)
                        self.assertAlmostEqual(average[i+a],exact['avg'][i+a],places=12)


@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class NativeSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.rules,cls.native=load(os.environ['QUALIFICATION_BUILD'])

    def test_checkpoint_resume_exact_and_policy_changes(self):
        a=Solver(self.rules,self.native);initial=a.policy_digest
        for _ in range(8):a.step()
        checkpoint=json.loads(json.dumps(a.snapshot()));b=Solver(self.rules,self.native);b.restore(checkpoint)
        for _ in range(8):a.step();b.step()
        self.assertEqual(a.snapshot(),b.snapshot());self.assertNotEqual(a.policy_digest,initial)
        self.assertTrue(any(any(x!=0 for x in row['R']) for row in a.rows.values()))
        checkpoint['identity']['epsilon']=.9
        with self.assertRaises(ValueError):b.restore(checkpoint)

    def test_all_root_sizes_sb_responses_and_short_allin(self):
        solver=Solver(self.rules,self.native)
        for _ in range(32):solver.step()
        provider=solver.response();keys=set()
        for a in legal(betting(self.rules)):
            b=betting(self.rules);act(b,a)
            if b.done:continue
            row=provider.row(b,[48,49],[]);self.assertEqual([a for a,_ in row],legal(b))
            self.assertAlmostEqual(sum(w for _,w in row),1);keys.add(observe(b,[48,49],[]).key)
            # The response must also cover SB re-response to every legal BB raise.
            for second,_ in row:
                c=betting(self.rules);act(c,a);act(c,second)
                if not c.done:
                    board=[] if c.round==0 else [4,5,6][: (0,3,4,5)[c.round]]
                    response=provider.row(c,[44,45],board)
                    self.assertEqual([x for x,_ in response],legal(c))
                    self.assertAlmostEqual(sum(w for _,w in response),1)
        self.assertEqual(len(keys),98)
        b=betting(self.rules,(3,3));act(b,1);act(b,1)
        self.assertEqual([a for a,_ in provider.row(b,[48,49],[4,5,6])],[1,3])

    def test_source_open_posterior_and_card_removal(self):
        from gto.qualification.mccfr_evaluate import open_posterior
        from gto.abstract.model import classes
        s=Solver(self.rules,self.native)
        reach,posterior,opens=open_posterior(s)
        self.assertAlmostEqual(reach,1/99,places=12)
        for actual,group in zip(posterior,classes()):
            self.assertAlmostEqual(actual,len(group)/1326,places=12)
        for _ in range(16):s.step()
        reach,posterior,opens=open_posterior(s)
        self.assertAlmostEqual(sum(posterior),1,places=12)
        for h in ((0,1),(48,49),(0,51)):
            direct=sum(p for other,p in opens.items() if not set(h).intersection(other))
            # BB-combo posterior mass is computed with card removal, not a
            # uniform opponent-class prior or future runout information.
            total=sum(opens.values());blocked=[sum(p for other,p in opens.items() if c in other) for c in h]
            self.assertAlmostEqual(direct,total-sum(blocked)+opens[h],places=10)

    def test_native_replay_and_no_evaluation_update(self):
        solver=Solver(self.rules,self.native)
        for _ in range(32):solver.step()
        before=solver.policy_digest;rng=random.Random(1711)
        for prefix in ([],[8],[8,22],[8,22,42],[8,92,102]):
            for _ in range(16):
                deck=rng.sample(range(52),9);state=self.native.NativeState(NativeGame([100,100]))
                result=rollout(solver,deck,rng,prefix,state)
                self.assertEqual(sum(result),0)
                self.assertTrue(all(-50<=v<=50 for v in result))
        self.assertEqual(before,solver.policy_digest)

if __name__=='__main__':unittest.main()
