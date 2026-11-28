"""Native legal-size generalization and independent external-sampling oracles."""
import copy,gzip,itertools,json,os,tempfile,unittest
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification import sparse_solver as s
from gto.qualification.build import load
from gto.qualification.native_mccfr import betting
from gto.qualification.policy import act,sha,legal
from gto.qualification.public_response import observe
from gto.native.training import NativeGame

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class SparseNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules,cls.native=load(os.environ['QUALIFICATION_BUILD']);cls.temp=tempfile.TemporaryDirectory();cls.module=s.build(cls.temp.name,os.environ['QUALIFICATION_BUILD'])
        classes=[-1]*2704
        for i,g in enumerate(model.classes()):
            for a,b in g:classes[a*52+b]=classes[b*52+a]=i
        cls.data=dict(classes=classes,pi=np.array([],dtype=float),support=np.array([],dtype=np.uint8),nodes=[],equity=[.5]*169)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def core(self,stacks=(100,100),full=False,fine=True,cap=1000000,sharing=False,extra=()):return self.module.Sparse(NativeGame(list(stacks)),dict(self.data,sharing=sharing,extra_support=list(extra)),17124001,full,fine,400000,cap)
    def query(self,q,b,own=(48,49),board=(),average=False):
        o=observe(b,own,board)
        return q.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,average)
    def test_all_root_sizes_get_actual_legal_responses_without_alias_or_fold_fill(self):
        q=self.core();keys=[]
        for a in legal(betting(self.rules)):
            if a<=1:continue
            b=betting(self.rules);act(b,a);r=self.query(q,b,own=(44,45));p=r['probabilities']
            self.assertAlmostEqual(sum(p),1.);self.assertGreater(p[legal(b).index(1)],0)
            self.assertTrue(set(r['actions'])<=set(legal(b)));keys.append(r['key'])
        self.assertEqual(len(keys),len(set(keys)))
        b=betting(self.rules);root=self.query(q,b);self.assertIn(9,root['actions'])
        act(b,8);self.assertIn(23,self.query(q,b)['actions'])
        allq=self.core(full=True);self.assertGreater(len(self.query(allq,betting(self.rules))['actions']),64)
    def test_short_allin_after_actual_raise_history_uses_native_legal_response(self):
        q=self.core();b=betting(self.rules)
        for action in (101,1):
            self.assertIn(action,legal(b));act(b,action)
        self.assertEqual(b.round,1);self.assertIn(3,legal(b));act(b,3)
        r=self.query(q,b,own=(44,45),board=(0,5,10))
        self.assertEqual(set(r['actions']),set(legal(b)))
        self.assertAlmostEqual(sum(r['probabilities']),1.)
        self.assertGreater(r['probabilities'][legal(b).index(1)],0.)
    def test_compact_shares_suit_isomorphs_and_keeps_category_draw_and_public_history(self):
        q=self.core(sharing=True);b=betting(self.rules);act(b,8);act(b,1)
        own=(44,45);board=(0,5,10)
        k=self.query(q,b,own,board)['key']
        perm=lambda c:4*(c//4)+(c%4+1)%4
        self.assertEqual(k,self.query(q,b,tuple(map(perm,own)),tuple(map(perm,board)))['key'])
        self.assertNotEqual(k,self.query(q,b,own,(46,5,10))['key'])
        self.assertNotEqual(self.query(q,b,(48,20),(0,4,9))['key'],self.query(q,b,(49,21),(0,4,9))['key'])
        other=betting(self.rules);act(other,9);act(other,1)
        self.assertNotEqual(k,self.query(q,other,own,board)['key'])
    def test_adaptive_public_node_support_is_not_a_fixed_size_patch(self):
        for action in (10,18,37,73):
            q=self.core(extra=[dict(round=0,history=[],actions=[action])]);r=self.query(q,betting(self.rules))
            self.assertIn(action,r['actions']);self.assertAlmostEqual(sum(r['probabilities']),1.)
        q=self.core(extra=[dict(round=0,history=[[0,0,7,7,5]],actions=[24])]);b=betting(self.rules);act(b,9)
        self.assertIn(24,self.query(q,b)['actions'])
    def test_batched_root_EV_matches_independent_fold_settlement_oracle(self):
        q=self.core();b=betting(self.rules);act(b,102);seed=[]
        for group in model.classes():
            row=self.query(q,b,group[0]);seed.append(dict(key=row['key'],actions=[0,1],R=[1.,0.],A=[1.,0.],prior=[1.,0.]))
        q.seed_preflop(seed);before=q.stats();r=q.root_ev([list(g[0]) for g in model.classes()[:3]],4,17127001,10.)
        self.assertEqual(before,q.stats());self.assertEqual(len(r['actions']),99)
        for row in r['rows']:
            self.assertEqual(row['samples'],4)
            for action,expected in ((0,-.5),(102,1.)):
                k=r['actions'].index(action);self.assertEqual(row['sum'][k]/4,expected)
                self.assertEqual(row['square'][k]/4,expected**2)
    def test_shared_rank_memory_prevents_known_paired_board_information_loss(self):
        q=self.core(sharing=True);b=betting(self.rules);act(b,8);act(b,1)
        for _ in range(4):act(b,1)
        board=(4,5,16,31,50)
        self.assertNotEqual(self.query(q,b,(44,37),board)['key'],self.query(q,b,(40,33),board)['key'])
        self.assertNotEqual(self.query(q,b,(48,28),board)['key'],self.query(q,b,(48,8),board)['key'])
    def test_refinement_splits_pair_and_set_aliased_by_old_flag(self):
        b=betting(self.rules);act(b,8);act(b,1)
        weak=(0,5,10);strong=(46,5,10)
        old=self.core(fine=False);fine=self.core(fine=True)
        self.assertEqual(self.query(old,b,(44,45),weak)['key'],self.query(old,b,(44,45),strong)['key'])
        self.assertNotEqual(self.query(fine,b,(44,45),weak)['key'],self.query(fine,b,(44,45),strong)['key'])
    def test_exact_conditional_allin_expectation_matches_original_rank(self):
        holes=[48,49,44,45];board=[0,5,10];deck=[x for x in range(52) if x not in holes+board];values=[]
        for x,y in itertools.combinations(deck,2):
            a=self.native.rank7(holes[:2]+board+[x,y]);b=self.native.rank7(holes[2:]+board+[x,y]);values.append((a>b)+.5*(a==b))
        self.assertEqual(len(values),990);self.assertAlmostEqual(self.module.equity_prefix(holes,board,16,1),sum(values)/990,places=12)
        for n in (4,5):
            shown=[0,5,10,15,20][:n];available=[x for x in range(52) if x not in holes+shown];runs=[()] if n==5 else [(x,) for x in available];vals=[]
            for suffix in runs:
                a=self.native.rank7(holes[:2]+shown+list(suffix));b=self.native.rank7(holes[2:]+shown+list(suffix));vals.append((a>b)+.5*(a==b))
            self.assertAlmostEqual(self.module.equity_prefix(holes,shown,16,1),sum(vals)/len(vals),places=12)
        a=self.module.equity_prefix(holes,[],128,171);b=self.module.equity_prefix(holes[2:]+holes[:2],[],128,171);self.assertEqual(a+b,1.)
    def test_allin_future_randomness_cannot_change_action_path(self):
        from gto.qualification.sparse_study import rb_value
        from gto.qualification.action_native import native_value
        class Policy:
            def __init__(self):self.path=[]
            def row(self,o,average=False):
                self.path.append((o.actor,o.round,o.history));weights={a:0. for a in o.actions}
                for a,w in zip((0,1,max(o.actions)),(.2,.3,.5)):weights[a if a in weights else 1]+=w
                return [weights[a] for a in o.actions]
        class Equity:
            def __init__(self):self.seeds=[]
            def equity_prefix(self,holes,board,n,seed):self.seeds.append(seed);return .5
        game=NativeGame([100,100]);deck=[48,49,44,45,0,5,10,15,20];module=Equity()
        for upper in range(1,12):
            a=Policy();b=Policy();c=Policy();rb_value(a,self.native,game,deck,(upper<<64)|1,module);rb_value(b,self.native,game,deck,(upper<<64)|2,module);native_value(c,self.native,game,deck,upper)
            self.assertEqual(a.path,b.path);self.assertEqual(a.path,c.path)
        self.assertTrue(module.seeds);self.assertTrue(set(module.seeds)<={1,2})
    def test_budget_abort_does_not_apply_partial_regret_or_averages(self):
        q=self.core(cap=1);r=q.step(1.);self.assertFalse(r['complete']);m=q.stats();self.assertEqual(m['iterations'],0);self.assertEqual(m['regret_visited'],0);self.assertEqual(m['average_visited'],0)
    def test_resume_saves_priors_warm_flags_and_rng_bit_exact(self):
        q=self.core(stacks=(3,3),full=True);self.assertTrue(q.step(2.)['complete']);path=Path(self.temp.name)
        q.save(str(path/'one.bin'),'test');other=self.core(stacks=(3,3),full=True);other.restore(str(path/'one.bin'),'test')
        self.assertTrue(q.step(2.)['complete']);self.assertTrue(other.step(2.)['complete']);q.save(str(path/'two.bin'),'test');other.save(str(path/'other.bin'),'test');self.assertEqual(sha(path/'two.bin'),sha(path/'other.bin'))
        with self.assertRaises(RuntimeError):other.restore(str(path/'one.bin'),'wrong')
    def test_external_regrets_and_average_expectation_match_independent_native_tree(self):
        q=self.core(stacks=(3,3),full=True);world=[48,49,44,45,0,5,10,15,20];nodes=[]
        ranks=[self.native.rank7(world[p:p+2]+world[4:]) for p in (0,2)]
        def build(b):
            k=len(nodes)
            if b.done:nodes.append(dict(actor=-1,children=[],utility=np.array(b.settle(ranks,b.round>=1)['net'])/2));return k
            r=self.query(q,b,world[2*b.actor:2*b.actor+2],world[4:4+(0,3,4,5)[b.round]]);acts=legal(b);n=dict(actor=b.actor,key=r['key'],actions=acts,pi=np.array(r['probabilities']),children=[]);nodes.append(n)
            for a in acts:
                c=copy.deepcopy(b);act(c,a);n['children'].append(build(c))
            return k
        build(betting(self.rules,(3,3)))
        for owner in (0,1):
            refR={};refA={}
            def value(k):
                n=nodes[k]
                if n['actor']<0:return n['utility'][owner]
                return sum(n['pi'][a]*value(c) for a,c in enumerate(n['children']))
            def walk(k,reach):
                n=nodes[k];p=n['actor']
                if p<0:return
                key=n['key'];refR.setdefault(key,np.zeros(len(n['pi'])));refA.setdefault(key,np.zeros(len(n['pi'])))
                if p==owner:
                    refR[key]+=reach[1-owner]*(np.array([value(c) for c in n['children']])-value(k))
                else:refA[key]+=reach[p]*n['pi']
                for a,c in enumerate(n['children']):
                    rr=list(reach);rr[p]*=n['pi'][a];walk(c,rr)
            walk(0,[1.,1.]);gotR={k:np.zeros_like(v) for k,v in refR.items()};gotA={k:np.zeros_like(v) for k,v in refA.items()};leaves=0;ev=0.
            def enumerate_plans(plan,weight):
                nonlocal leaves,ev
                r=q.trace(world,owner,plan)
                if not r['complete']:
                    for a,p in enumerate(r['need']):
                        if p:enumerate_plans(plan+[a],weight*p)
                    return
                leaves+=1
                if leaves>20000:raise AssertionError('exact plan budget exceeded')
                ev+=weight*r['value']
                for u in r['updates']:
                    gotR[u['key']]+=weight*np.array(u['R']);gotA[u['key']]+=weight*np.array(u['A'])
            enumerate_plans([],1.)
            self.assertAlmostEqual(ev,value(0),places=11)
            for k in refR:np.testing.assert_allclose(gotR[k],refR[k],atol=2e-11);np.testing.assert_allclose(gotA[k],refA[k],atol=2e-11)

if __name__=='__main__':unittest.main()
