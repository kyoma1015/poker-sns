"""Blind-ledger integration regression, not a release-accuracy certificate."""
import itertools,math,os,random,unittest,json
from collections import defaultdict
from gto.qualification.blind_oracle import *

class BlindGame(unittest.TestCase):
    def fixture(self):
        return {(h,r):([.1,.3,.6] if len(a)==3 else [.25,.75]) for h,a in ACTIONS.items() for r in range(3)}
    def test_blind_fold_showdown_net_and_card_removal(self):
        for h,u in [(('F',),-.5),(('R','F'),1.),(('C','R','F'),-1.),(('R','R','F'),-3.)]:
            self.assertEqual(payoff(h,(4,0)),u)
        for h,stake in [(('C','C'),1.),(('R','C'),3.),(('C','R','C'),3.),(('R','R','C'),10.)]:
            self.assertEqual(payoff(h,(4,0)),stake);self.assertEqual(payoff(h,(0,4)),-stake)
            self.assertEqual(payoff(h,(4,5)),0.)
        # Opponent same rank has only ONE remaining card, other ranks TWO each.
        compatible=[w for w in WORLDS if w[0]==4]
        self.assertEqual([sum(w[1]//2==r for w in compatible) for r in range(3)],[2,2,1])
    def test_conditional_ev_times_reach_equals_root_contribution(self):
        pi=self.fixture();root=exact(pi)[0];parts=[];reach=[]
        def continuation(h,w):
            if h not in ACTIONS:return payoff(h,w)
            return sum(p*continuation(h+(a,),w) for a,p in zip(ACTIONS[h],row(pi,h,w)))
        for j,a in enumerate(ACTIONS[()]):
            mass=sum(row(pi,(),w)[j]/30 for w in WORLDS)
            contribution=sum(row(pi,(),w)[j]*continuation((a,),w)/30 for w in WORLDS)
            reach.append(mass);parts.append(contribution/mass*mass)
        self.assertAlmostEqual(sum(reach),1);self.assertAlmostEqual(sum(parts),root)
    def test_outcome_expectation_end_to_end_equals_full_tree(self):
        pi=self.fixture();pi[((),0)]=[0.,.2,.8]
        _,grad,avg=exact(pi)
        for owner in (0,1):
            gs=defaultdict(lambda:None);av=defaultdict(lambda:None)
            def add(dst,k,v,m):
                if dst[k] is None:dst[k]=[0.]*len(v)
                dst[k]=[x+m*y for x,y in zip(dst[k],v)]
            def walk(h,w,mass,qprefix,reach,records,averages):
                if h not in ACTIONS:
                    for k,_,d,_ in general_updates(records,payoff(h,w)*(1 if owner==0 else -1)):add(gs,k,d,mass)
                    for k,v in averages:add(av,k,v,mass)
                    return
                p=ACTOR[h];k=key(h,w);pr=row(pi,h,w)
                avgs=averages+[(k,[x*reach[p]/qprefix for x in pr])] if p!=owner else averages
                qs=[.6/len(pr)+.4*x for x in pr] if p==owner else pr
                for j,(a,q) in enumerate(zip(ACTIONS[h],qs)):
                    if not q:continue
                    r=reach[:];r[p]*=pr[j]
                    rec=(k,pr,j,q,reach[1-owner]/qprefix,[0.]*len(pr),p==owner)
                    walk(h+(a,),w,mass*q,qprefix*q,r,records+[rec],avgs)
            for w in WORLDS:walk((),w,1/30,1.,[1.,1.],[],[])
            for k in grad:
                expected=grad[k] if ACTOR[k[0]]==owner else avg[k]
                actual=gs[k] if ACTOR[k[0]]==owner else av[k]
                for x,y in zip(actual,expected):self.assertAlmostEqual(x,y,places=11)
    def test_external_expectation_end_to_end_equals_full_tree(self):
        pi=self.fixture();_,grad,avg=exact(pi);s=FiniteCFR('external')
        class Tape:
            def __init__(self,us):self.us=iter(us)
            def random(self):return next(self.us)
        for owner in (0,1):
            gs=defaultdict(lambda:None);av=defaultdict(lambda:None)
            def add(dst,k,v,m):
                if dst[k] is None:dst[k]=[0.]*len(v)
                dst[k]=[x+m*y for x,y in zip(dst[k],v)]
            hs=[h for h in ACTIONS if ACTOR[h]!=owner]
            for w in WORLDS:
                for plan in itertools.product(*(range(len(ACTIONS[h])) for h in hs)):
                    prob=1/30;us={}
                    for h,j in zip(hs,plan):
                        pr=row(pi,h,w);prob*=pr[j];us[h]=sum(pr[:j])+pr[j]/2
                    order=hs if owner==0 else [()]+([] if ACTIONS[()][plan[0]]=='F' else [(ACTIONS[()][plan[0]],'R')])
                    g,a=s.external(pi,owner,w,Tape([us[h] for h in order]))
                    for k,v in g:add(gs,k,v,prob)
                    for k,v in a:add(av,k,v,prob)
            for k in grad:
                expected=grad[k] if ACTOR[k[0]]==owner else avg[k]
                actual=gs[k] if ACTOR[k[0]]==owner else av[k]
                for x,y in zip(actual,expected):self.assertAlmostEqual(x,y,places=11)
    def test_actual_production_collector_matches_card_game_oracle(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from gto.qualification.action_baseline import ActionBaselineSolver
        from gto.qualification import action_baseline as production
        class B:
            round=0
            def __init__(self):self.history=()
            @property
            def actor(self):return ACTOR[self.history]
            @property
            def done(self):return self.history not in ACTIONS
            def settle(self,ranks,postflop):
                u=payoff(self.history,[2*r for r in ranks]);return {'net':[2*u,-2*u]}
        class Native:
            @staticmethod
            def rank7(cards):return cards[0]//2
        class Tape:
            def __init__(self,us):self.us=iter(us)
            def random(self):return next(self.us)
        def obs(b,own,board):
            return SimpleNamespace(key=(b.history,own[0]//2),round=0,history=b.history,
                actor=b.actor,actions=ACTIONS[b.history])
        pi=self.fixture();_,grad,avg=exact(pi)
        solver=ActionBaselineSolver(None,Native());solver.observation=lambda o:o
        solver.rows={k:dict(actions=list(ACTIONS[k[0]]),R=v[:],S=[0.]*len(v)) for k,v in pi.items()}
        for owner in (0,1):
            gs=defaultdict(lambda:None);av=defaultdict(lambda:None)
            def add(dst,k,v,m):
                if dst[k] is None:dst[k]=[0.]*len(v)
                dst[k]=[x+m*y for x,y in zip(dst[k],v)]
            def paths(h,w,mass,us):
                if h not in ACTIONS:yield mass,us;return
                pr=row(pi,h,w);q=[.6/len(pr)+.4*x for x in pr] if ACTOR[h]==owner else pr
                for j,a in enumerate(ACTIONS[h]):yield from paths(h+(a,),w,mass*q[j],us+[sum(q[:j])+q[j]/2])
            with patch.object(production,'betting',lambda rules:B()),patch.object(production,'observe',obs),patch.object(production,'act',lambda b,a:setattr(b,'history',b.history+(a,))):
                for w in WORLDS:
                    for mass,us in paths((),w,1/30,[]):
                        g,a=solver.collect(owner,[w[0],99,w[1],98,0,1,2,3,4],Tape(us))
                        for o,_,v,_ in g:add(gs,o.key,v,mass)
                        for o,pr,weight in a:add(av,o.key,[weight*x for x in pr],mass)
            for k in grad:
                expected=grad[k] if ACTOR[k[0]]==owner else avg[k]
                actual=gs[k] if ACTOR[k[0]]==owner else av[k]
                for x,y in zip(actual,expected):self.assertAlmostEqual(x,y,places=11)

    def test_first_external_actual_collector_exact_expectation(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from gto.qualification.first_external import FirstExternalSolver
        from gto.qualification import first_external as production
        class B:
            round=0
            def __init__(self):self.history=()
            @property
            def actor(self):return ACTOR[self.history]
            @property
            def done(self):return self.history not in ACTIONS
            def settle(self,ranks,postflop):
                u=payoff(self.history,[2*r for r in ranks]);return {'net':[2*u,-2*u]}
        class Native:
            @staticmethod
            def rank7(cards):return cards[0]//2
        current=[()];us={}
        class Tape:
            def random(self):return us[current[0]]
            def getrandbits(self,n):return 0
        def obs(b,own,board):
            current[0]=b.history
            return SimpleNamespace(key=(b.history,own[0]//2),round=0,history=b.history,
                actor=b.actor,actions=ACTIONS[b.history])
        pi=self.fixture();_,grad,avg=exact(pi)
        solver=FirstExternalSolver(None,Native());solver.observation=lambda o:o
        solver.baseline=lambda o,p:[1.3,-2.1,.8][:len(o.actions)]
        solver.rows={k:dict(actions=list(ACTIONS[k[0]]),R=v[:],S=[0.]*len(v)) for k,v in pi.items()}
        for owner in (0,1):
            gs=defaultdict(lambda:None);av=defaultdict(lambda:None)
            def add(dst,k,v,m):
                if dst[k] is None:dst[k]=[0.]*len(v)
                dst[k]=[x+m*y for x,y in zip(dst[k],v)]
            # Independently enumerate a random-action plan at EVERY sampled node;
            # unreachable choices marginalize to1; external first nodes excluded.
            hs=[h for h in ACTIONS if not (ACTOR[h]==owner and len(h)==owner)]
            for w in WORLDS:
                for plan in itertools.product(*(range(len(ACTIONS[h])) for h in hs)):
                    prob=1/30;us.clear()
                    for h,j in zip(hs,plan):
                        pr=row(pi,h,w);q=[.6/len(pr)+.4*x for x in pr]
                        prob*=q[j];us[h]=sum(q[:j])+q[j]/2
                    with patch.object(production,'betting',lambda rules:B()),patch.object(production,'observe',obs),patch.object(production,'act',lambda b,a:setattr(b,'history',b.history+(a,))),patch.object(production.random,'Random',lambda seed:Tape()):
                        g,a=solver.collect(owner,[w[0],99,w[1],98,0,1,2,3,4],Tape())
                    for o,_,v,_ in g:add(gs,o.key,v,prob)
                    for o,pr,weight in a:add(av,o.key,[weight*x for x in pr],prob)
            for k in grad:
                expected=grad[k] if ACTOR[k[0]]==owner else avg[k]
                actual=gs[k] if ACTOR[k[0]]==owner else av[k]
                for x,y in zip(actual,expected):self.assertAlmostEqual(x,y,places=10)

    def test_complete_br_equals_independent_private_plan_enumeration(self):
        pi=self.fixture()
        def value(h,w,owner,plan):
            if h not in ACTIONS:return payoff(h,w)*(1 if owner==0 else -1)
            if ACTOR[h]==owner:return value(h+(plan[h],),w,owner,plan)
            return sum(p*value(h+(a,),w,owner,plan) for a,p in zip(ACTIONS[h],row(pi,h,w)))
        for owner in (0,1):
            hs=[h for h in ACTIONS if ACTOR[h]==owner];total=0.
            for rank in range(3):
                total+=max(sum(value((),w,owner,dict(zip(hs,actions)))/30 for w in WORLDS if w[owner]//2==rank)
                           for actions in itertools.product(*(ACTIONS[h] for h in hs)))
            self.assertAlmostEqual(best_response(pi,owner)[0],total,places=12)
    def test_checkpoint_exact_continuation_all_three_methods(self):
        for method in ('outcome','external','exact'):
            a=FiniteCFR(method)
            for _ in range(12):a.step()
            b=FiniteCFR(method);b.restore(json.loads(json.dumps(a.snapshot())))
            for _ in range(4):a.step();b.step()
            self.assertEqual(a.snapshot(),b.snapshot())

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class NativeBlindLedger(unittest.TestCase):
    def test_native_first_external_checkpoint_continues_exactly(self):
        import tempfile
        from pathlib import Path
        from gto.qualification.build import load
        from gto.qualification.action_baseline import ActionBaselineSolver
        from gto.qualification.first_external import FirstExternalSolver
        from gto.qualification.first_external_study import load_experiment
        from gto.qualification.variance_study import compressed
        rules,native=load(os.environ['QUALIFICATION_BUILD']);base=ActionBaselineSolver(rules,native,baseline=True,targeted=True)
        before=base.snapshot();a=FirstExternalSolver(rules,native);a.adopt(base,17118049);a.step()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.json.gz';compressed(path,a.snapshot());b=load_experiment(rules,native,path)
            a.step();b.step();self.assertEqual(a.snapshot(),b.snapshot())
        self.assertEqual(before,base.snapshot())

    def test_reference_and_native_match_independent_chip_ledger(self):
        from gto.qualification.build import load
        from gto.qualification.native_mccfr import betting,rollout
        from gto.qualification.policy import act
        from gto.native.training import NativeGame
        rules,native=load(os.environ['QUALIFICATION_BUILD'])
        for prefix,expected in [([0],[-.5,.5]),([8,0],[1.,-1.]),([8,22,0],[-3.,3.]),([1,8,0],[-1.,1.])]:
            b=betting(rules);state=native.NativeState(NativeGame([100,100]));deck=[48,49,0,1,4,9,14,19,24]
            for c in deck[:4]:state.apply_action(c)
            for a in prefix:act(b,a);state.apply_action(a)
            self.assertEqual([x/2 for x in b.settle([0,0],False)['net']],expected)
            self.assertEqual([x/2 for x in state.returns()],expected)
        # Called preflop shove: independent BB net is +/-50 or0, never gross pot100.
        deck=[48,49,0,1,4,9,14,19,24];state=native.NativeState(NativeGame([100,100]))
        class Fixed:
            def row(self,o,average=False):return [float(a==1) for a in o.actions]
        s=Fixed();s.rules=rules;s.native=native
        result=rollout(s,deck,random.Random(1),[102,1],state)
        sign=(native.rank7(deck[:2]+deck[4:])>native.rank7(deck[2:4]+deck[4:]))-(native.rank7(deck[:2]+deck[4:])<native.rank7(deck[2:4]+deck[4:]))
        self.assertEqual(result,[50*sign,-50*sign])

if __name__=='__main__':unittest.main()
