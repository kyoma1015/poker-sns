"""Active-index integration must preserve the existing independent CF oracle."""
import itertools,tempfile,unittest
import numpy as np
from gto.qualification import active_chance as a,public_chance_solver as pcs,integrated_br as br

class ActiveOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.lib=a.build(cls.temp.name)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_active_raw_CF_average_and_BR_match_existing_CSR(self):
        blocks=[pcs.block(self.lib,b,.5) for b in ([0,5,10,15,20],[0,5,10,16,21])]
        nodes=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5),dict(actor=1,children=[3,4],round=3),dict(actor=-1,children=[],round=3,c0=-3,c1=6),dict(actor=-1,children=[],round=3,c0=2)]
        dense=pcs.Game(self.lib,nodes,[dict(blocks[0],weight=1.)]);dense.use_blocks(blocks)
        # Configure the reused original symbol independently of the active ABI.
        import ctypes as C
        from gto.abstract import model
        self.lib.pcs_eval.argtypes=[C.c_int]*5+[model.IP]*13+[model.DP]*9+[C.c_int,model.DP];self.lib.pcs_eval.restype=C.c_int
        dense.R[:]=np.random.default_rng(17140101).random(dense.S);dp=dense.policy(False)
        q=a.Game(self.lib,nodes,blocks);mapping={}
        for b,block in enumerate(blocks):
            for k,n in enumerate(nodes):
                if n['actor']<0:continue
                r=n['round'];ids=dense.base[k]+((block['public']>>(3-r))*(169<<r)+(np.array(block['codes'])>>(3-r)))*len(n['children'])
                for at,old in zip(q.active[b,k],ids):mapping[int(at)]=int(old)
        for at,old in mapping.items():
            n=2;q.R[at:at+n]=dp[old:old+n]
        for owner in (0,1):
            expected=dense.evaluate_owner(dp,owner);actual=q.evaluate_owner(q.policy(False),owner);np.testing.assert_allclose(actual,expected,atol=1e-12)
            for at,old in mapping.items():
                for x,y in ((q.grad,dense.grad),(q.avg,dense.avg),(q.den,dense.den)):np.testing.assert_allclose(x[at:at+2],y[old:old+2],atol=1e-12)
        metric=br.measure(self.lib,nodes,[b['board'] for b in blocks],q.export(q.policy(False)))
        self.assertAlmostEqual(metric['BR_SB_bb'],q.evaluate_owner(q.policy(False),0)[1],places=10)
        child=a.Game(self.lib,nodes,blocks,[(2,key[0]) for key in q.keys[2]],parent=q)
        for x,y in zip(q.export(q.policy(False)),child.export(child.policy(False))):
            for u,v in zip(x,y):
                if u is not None:np.testing.assert_allclose(u['pi'],v['pi'],atol=1e-12)
    def test_six_action_CSR_is_not_truncated_to_four(self):
        blocks=[pcs.block(self.lib,[0,5,10,15,20])]
        values=[-3.,-2.,-1.,0.,1.,2.]
        nodes=[dict(actor=0,children=list(range(1,7)),round=0)]+[dict(actor=-1,children=[],round=0,c0=v) for v in values]
        q=a.Game(self.lib,nodes,blocks);ev,best=q.evaluate_owner(q.policy(),0)
        self.assertAlmostEqual(ev,-.5,places=12);self.assertAlmostEqual(best,2.,places=12)
        gradients=sum((q.grad[st:st+t*n].reshape(t,n).sum(axis=0) for st,t,n,k in q.rows))
        np.testing.assert_allclose(gradients,np.array(values)+.5,atol=1e-12)
        oracle=br.measure(self.lib,nodes,[blocks[0]['board']],q.export())
        self.assertAlmostEqual(oracle['BR_SB_bb'],best,places=12)

    def test_vectorized_initialization_preserves_reference_and_rejects_mixed_rows(self):
        from gto.qualification.active_study import initialize
        blocks=[pcs.block(self.lib,[0,5,10,15,20]),pcs.block(self.lib,[0,5,10,16,21])]
        for b in blocks:b['weight']=.5
        nodes=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5),dict(actor=-1,children=[],round=0,c0=1)]
        q=a.Game(self.lib,nodes,blocks);q.R[:]=np.random.default_rng(17143101).random(q.S);rows=q.export(q.policy(False));expected=np.zeros(q.S)
        for b in range(2):
            for h,at in enumerate(q.active[b,0]):expected[at:at+2]=rows[b][0]['pi'][h]
        initialize(q,rows);np.testing.assert_array_equal(q.R,expected*1e-6);np.testing.assert_array_equal(q.A,expected*.001)
        rows[1][0]['pi'][0]=[.123456789,.876543211]
        with self.assertRaisesRegex(ValueError,'one infoset'):initialize(q,rows)

    def test_features_are_suit_invariant_and_prefix_rank_is_exact(self):
        from gto.abstract import model
        cards=[0,5,10,15,20,25,30]
        for n in (5,6,7):
            # Existing seven-card evaluator equals max over five-card subsets.
            ranks=[int(self.lib.active_rank(model.ints(c),5)) for c in itertools.combinations(cards[:n],5)]
            self.assertEqual(int(self.lib.active_rank(model.ints(cards[:n]),n)),max(ranks))
        original=a.feature(self.lib,cards[:2],cards[2:])
        for p in a.PERMS:
            cv=lambda c:4*(c//4)+p[c%4]
            self.assertEqual(original,a.feature(self.lib,list(map(cv,cards[:2])),list(map(cv,cards[2:]))))
            self.assertEqual(a.observation(cards[:2],cards[2:]),a.observation(list(map(cv,cards[:2])),list(map(cv,cards[2:]))))
        # Prefix features do not see either possible turn/river suffix.
        self.assertEqual(a.feature(self.lib,cards[:2],cards[2:5]),a.feature(self.lib,cards[:2],(cards[2:5]+[40,45])[:3]))

    def test_cross_instance_resume_restores_warm_prior_and_next_update(self):
        from pathlib import Path
        from gto.qualification.active_resume import restore_prior
        blocks=[pcs.block(self.lib,[0,5,10,15,20])]
        nodes=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5),dict(actor=-1,children=[],round=0,c0=1)]
        q=a.Game(self.lib,nodes,blocks);q.A[:]=np.tile([.2,.8],q.S//2);q.R[:]=q.A
        child=a.Game(self.lib,nodes,blocks,parent=q)
        with tempfile.TemporaryDirectory() as d:
            initial=Path(d)/'initial.npz';last=Path(d)/'last.npz';child.save(initial)
            for _ in range(3):child.step()
            # Force the documented fallback case, rather than hope it occurs.
            child.R[:]=0;child.save(last)
            resumed=a.Game(self.lib,nodes,blocks);resumed.restore(last);restore_prior(resumed,initial)
            np.testing.assert_array_equal(resumed.prior,child.prior)
            child.step();resumed.step();np.testing.assert_array_equal(child.R,resumed.R);np.testing.assert_array_equal(child.A,resumed.A)

    def test_suit_orbit_response_scores_equal_explicit_24_permutations(self):
        # A finite board law is not suit symmetric until orbit-closed. Preserve
        # physical BR on the original law separately; never relabel it as NLH.
        absolute={};canonical={};records=[((0,5),(10,15,20),(1.,-2.)),((0,5),(11,14,21),(-1.,3.)),((4,8),(16,20,24),(2.,1.))]
        for own,board,values in records:
            key=a.observation(own,board);canonical.setdefault(key,np.zeros(2));canonical[key]+=values
            for p in a.PERMS:
                cv=lambda c:4*(c//4)+p[c%4]
                key=(tuple(sorted(map(cv,own))),tuple(sorted(map(cv,board))))
                absolute.setdefault(key,np.zeros(2));absolute[key]+=np.array(values)/24
        self.assertAlmostEqual(sum(max(v) for v in canonical.values()),sum(max(v) for v in absolute.values()),places=12)

    def test_native_adapter_matches_training_rows_and_explicit_offtree_backoff(self):
        from gto.qualification.build import load
        from gto.qualification.native_mccfr import betting
        from gto.qualification.public_response import observe
        from gto.qualification.policy import act
        from gto.qualification.active_policy import Policy
        import os
        rules,native=load(os.environ.get('QUALIFICATION_BUILD','/tmp/native-qualification'))
        nodes=a.native_tree(rules,[0,1,8]);blocks=[pcs.block(self.lib,[0,5,10,15,20])]
        q=a.Game(self.lib,nodes,blocks)
        class Backoff:
            policy_digest='test-legal-call';calls=0
            def row(self,o,average=False):
                self.calls+=1;return [float(x==1) for x in o.actions]
        fallback=Backoff();fallback.rules=rules;fallback.native=native
        policy=Policy(q,fallback,{'test_only':True});b=betting(rules)
        o=observe(b,(48,49),[]);np.testing.assert_allclose([policy.row(o)[o.actions.index(x)] for x in nodes[0]['native_actions']],[1/3]*3)
        act(b,9) # legal 3.5BB open absent in this three-action test game
        o=observe(b,(48,49),[]);p=policy.row(o);self.assertEqual(sum(p),1);self.assertEqual(p[o.actions.index(1)],1);self.assertEqual(fallback.calls,1)

if __name__=='__main__':unittest.main()
