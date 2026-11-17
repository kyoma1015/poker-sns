import copy
import json
import math
import os
import unittest
from gto.qualification.native_mccfr import Solver, outcome_updates
from gto.qualification.variance_mccfr import VarianceSolver, cv_updates, canonical, canonical_cards
from gto.qualification.public_response import observe
from gto.qualification.native_mccfr import betting
from gto.qualification.build import load


class UnbiasedBaseline(unittest.TestCase):
    def test_expected_cf_and_variance_against_exact_values(self):
        # Single information set, arbitrarily known action baselines; integrate
        # sampling before the regret update. Exact-fold control lowers variance.
        pi=[.2,.3,.5];q=[.3,.3,.4];payoff=[-2,3,5]
        baseline=[-2,0,0];expected=[0.]*3;raw=[0.]*3;second=0.;zero_second=0.
        truth=[v-sum(p*v for p,v in zip(pi,payoff)) for v in payoff]
        for a in range(3):
            record=(None,pi,a,q[a],0.,1.,baseline)
            delta=list(cv_updates([record],payoff[a]))[0][2]
            z=list(outcome_updates([record[:6]],payoff[a]))[0][2]
            for i in range(3):expected[i]+=q[a]*delta[i];raw[i]+=q[a]*z[i]
            second+=q[a]*sum(x*x for x in delta);zero_second+=q[a]*sum(x*x for x in z)
        for i in range(3):self.assertAlmostEqual(expected[i],truth[i]);self.assertAlmostEqual(raw[i],truth[i])
        # A known fold baseline is not universally variance reducing: retain
        # this counterexample rather than changing the fixture to hide it.
        self.assertGreater(second,zero_second)
        for a in range(3):
            d=list(cv_updates([(None,pi,a,q[a],0.,1.,payoff)],payoff[a]))[0][2]
            for i in range(3):self.assertAlmostEqual(d[i],truth[i])

    def test_recursive_cv_expected_cf_matches_independent_oracle(self):
        from gto.abstract.matched_history import python_oracle
        ns=[dict(actor=0,children=[1,2]),dict(actor=1,children=[3,4]),
            dict(actor=-1,children=[],c0=2,c1=0),dict(actor=0,children=[5,6]),
            dict(actor=-1,children=[],c0=-3,c1=0),dict(actor=-1,children=[],c0=5,c1=0),dict(actor=-1,children=[],c0=-7,c1=0)]
        g=dict(nodes=ns,worlds=[dict(mass=1.,equity=0.)],info=[0,2,0,4,0,0,0]);pi=[.3,.7,.4,.6,.2,.8]
        exact=python_oracle(g,pi)
        for owner in (0,1):
            expected=[0.]*6;avg=[0.]*6
            def walk(k,mass,logq,ownq,reach,records):
                n=ns[k]
                if n['actor']<0:
                    for i,row,delta,w in cv_updates(records,n['c0']*(1 if owner==0 else -1)):
                        for a in range(2):expected[i+a]+=mass*delta[a];avg[i+a]+=mass*w*row[a]
                    return
                i=g['info'][k];row=pi[i:i+2];own=n['actor']==owner
                q=[.3+.4*p for p in row] if own else row
                for a,c in enumerate(n['children']):
                    rec=records+[(i,row,a,q[a],ownq,reach*math.exp(-logq),[1.5,-2.3])] if own else records
                    walk(c,mass*q[a],logq+math.log(q[a]),ownq+(math.log(q[a]) if own else 0),reach*(row[a] if own else 1),rec)
            walk(0,1,0,0,1,[])
            for node in (0,1,3):
                if ns[node]['actor']==owner:
                    for a in range(2):
                        i=g['info'][node]+a
                        self.assertAlmostEqual(expected[i],exact['grad'][i],places=12)
                        self.assertAlmostEqual(avg[i],exact['avg'][i],places=12)

    def test_external_first_expectation_and_average_match_independent_cf(self):
        from types import SimpleNamespace
        from gto.qualification.external_first import combine
        from gto.abstract.matched_history import python_oracle
        ns=[dict(actor=0,children=[1,2]),dict(actor=0,children=[3,4]),dict(actor=0,children=[5,6])]
        ns += [dict(actor=-1,children=[],c0=x,c1=0) for x in (2,-3,4,-7)]
        g=dict(nodes=ns,worlds=[dict(mass=1.,equity=0.)],info=[0,2,4,0,0,0,0])
        pi=[.25,.75,.3,.7,.4,.6];expected=python_oracle(g,pi);weighted=[]
        for a in (0,1):
            start=2+2*a;row=pi[start:start+2];q=[.3+.4*p for p in row]
            for b in (0,1):
                root=SimpleNamespace(key='0');child=SimpleNamespace(key=str(start))
                records=[(root,pi[:2],a,1.,0.,.5,[0.,0.]),
                         (child,row,b,q[b],0.,pi[a],[0.,0.])]
                for o,p,delta,w in cv_updates(records,ns[ns[a+1]['children'][b]]['c0']):
                    weighted.append((o,p,[x*q[b] for x in delta],w*q[b]))
        rows=combine(weighted)
        for key,row in rows.items():
            offset=int(key)
            for a in range(2):
                self.assertAlmostEqual(row['R'][a],expected['grad'][offset+a],places=12)
                self.assertAlmostEqual(row['S'][a],expected['avg'][offset+a],places=12)


@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class RevisitAndResume(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rules,cls.native=load(os.environ['QUALIFICATION_BUILD'])

    def test_same_infoset_real_regret_and_average_accumulate(self):
        for cls,kwargs in ((Solver,{}),(VarianceSolver,dict(suits=True,control=True))):
            s=cls(self.rules,self.native,**kwargs);state=s.rng.getstate()
            s.trajectory(0);root=next(k for k in s.rows if not json.loads(k)['history'])
            before=copy.deepcopy(s.rows[root]);s.rng.setstate(state);s.trajectory(0)
            self.assertIn(root,s.rows);self.assertNotEqual(before['R'],s.rows[root]['R'])
            self.assertGreater(sum(s.rows[root]['S']),sum(before['S']))
            if isinstance(s,VarianceSolver):self.assertEqual(s.counts[root],2)

    def test_suit_orbit_preserves_history_rank_and_board_information(self):
        b=betting(self.rules);o=observe(b,[48,49],[])
        p=observe(b,[50,51],[]);different=observe(b,[44,45],[])
        self.assertEqual(canonical(o).key,canonical(p).key)
        self.assertNotEqual(canonical(o).key,canonical(different).key)
        self.assertNotEqual(canonical_cards((0,1),(4,8,12,16,20)),canonical_cards((0,1),(4,8,12,20,16)))

    def test_exact_169_orbits_and_global_suit_permutations(self):
        import itertools
        from gto.qualification.variance_mccfr import PERMUTATIONS
        b=betting(self.rules)
        keys={canonical(observe(b,h,[])).key for h in itertools.combinations(range(52),2)}
        self.assertEqual(len(keys),169)
        own=(48,45);board=(0,5,10,15,20)
        expected=canonical_cards(own,board)
        for p in PERMUTATIONS:
            conv=lambda c:c//4*4+p[c%4]
            self.assertEqual(canonical_cards(tuple(sorted(map(conv,own))),tuple(map(conv,board))),expected)

    def test_public_fold_baseline_is_exact_native_payoff(self):
        from gto.qualification.policy import act,legal
        from gto.native.training import NativeGame
        for prefix in ([],[8],[8,22],[8,92]):
            b=betting(self.rules);state=self.native.NativeState(NativeGame([100,100]))
            for card in (0,1,2,3):state.apply_action(card)
            for a in prefix:act(b,a);state.apply_action(a)
            owner=b.actor;self.assertIn(0,legal(b))
            exact=-(b.live[owner]+b.dead[owner])/2
            state.apply_action(0);self.assertEqual(state.returns()[owner]/2,exact)

    def test_external_freezes_full_batch_and_restarts_exactly(self):
        from gto.qualification.external_first import ExternalFirst
        a=ExternalFirst(self.rules,self.native);old=Solver(self.rules,self.native);a.migrate(old.snapshot())
        initial=a.policy_digest;calls=[];branch=a.branch
        def watched(*args):
            self.assertEqual(a.policy_digest,initial);calls.append(args[2]);return branch(*args)
        a.branch=watched;self.assertTrue(a.batch(0,99));a.branch=branch
        self.assertEqual(len(calls),99);self.assertEqual(a.leaves,99)
        root=next(k for k in a.rows if not json.loads(k)['history'])
        self.assertAlmostEqual(sum(a.rows[root]['S']),1)
        b=ExternalFirst(self.rules,self.native);b.restore(json.loads(json.dumps(a.snapshot())))
        for owner in (1,0):a.batch(owner);b.batch(owner)
        self.assertEqual(a.snapshot(),b.snapshot())
        before=copy.deepcopy(a.rows);self.assertFalse(a.batch(0,1));self.assertEqual(a.rows,before)

    def test_resume_and_explicit_migration(self):
        old=Solver(self.rules,self.native)
        for _ in range(4):old.step()
        source=json.loads(json.dumps(old.snapshot()));saved=copy.deepcopy(source)
        a=VarianceSolver(self.rules,self.native,suits=True,control=True);a.migrate(source)
        for _ in range(4):a.step()
        b=VarianceSolver(self.rules,self.native,suits=True,control=True);b.restore(json.loads(json.dumps(a.snapshot())))
        for _ in range(4):a.step();b.step()
        self.assertEqual(a.snapshot(),b.snapshot());self.assertEqual(source,saved)
        self.assertNotEqual(a.policy_digest,old.policy_digest)

if __name__=='__main__':unittest.main()
