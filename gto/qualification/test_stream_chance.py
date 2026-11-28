"""Streaming CF equals exact weighted integration, including clip placement."""
import tempfile,unittest
import numpy as np
from gto.qualification import active_chance as ac,stream_chance as sc,public_chance_solver as pcs,stream_br

class Streaming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.temp=tempfile.TemporaryDirectory();cls.lib=ac.build(cls.temp.name)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_exact_stratum_partition_and_causal_features(self):
        w=sc.strata();self.assertEqual(len(w),13);self.assertAlmostEqual(sum(w.values()),1,places=12)
        self.assertAlmostEqual(sum(v for (p,m,c),v in w.items() if m),1144/22100,places=12)
        self.assertAlmostEqual(sum(v for (p,m,c),v in w.items() if p==7),3796/22100,places=12)
        self.assertFalse(any(p==7 and m for p,m,c in w))
    def test_streamed_raw_CF_average_and_clip_match_joint_weighted_kernel(self):
        blocks=[pcs.block(self.lib,[0,5,10,15,20],.2),pcs.block(self.lib,[0,5,10,16,21],.8)]
        ns=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5),dict(actor=1,children=[3,4],round=3),dict(actor=-1,children=[],round=3,c0=-3,c1=6),dict(actor=-1,children=[],round=3,c0=2)]
        joint=ac.Game(self.lib,ns,blocks);stream=sc.Game(self.lib,ns,blocks)
        # Use same strategic row behavior even though active offsets differ.
        lookup=[None if n['actor']<0 else {key:j for j,key in enumerate(joint.keys[k])} for k,n in enumerate(ns)]
        mapping=np.empty(stream.S,dtype=int)
        for st,t,n,k in stream.rows:
            for j,key in enumerate(stream.keys[k]):mapping[st+j*n:st+(j+1)*n]=joint.base[k]+lookup[k][key]*n+np.arange(n)
        joint.R[:]=np.random.default_rng(17150101).random(joint.S);joint.A[:]=joint.R;stream.R[:]=joint.R[mapping];stream.A[:]=joint.A[mapping]
        for owner in (0,1):
            x=joint.evaluate_owner(joint.policy(False),owner);y=stream.evaluate_owner(stream.policy(False),owner)
            self.assertAlmostEqual(x[0],y[0],places=12)
            for got,want in ((stream.grad,joint.grad),(stream.avg,joint.avg),(stream.den,joint.den)):np.testing.assert_allclose(got,want[mapping],atol=1e-12)
        metric=stream_br.measure(self.lib,ns,[b['board'] for b in blocks],stream.export(),weights=[.2,.8]);self.assertAlmostEqual(metric['BR_SB_bb'],joint.evaluate_owner(joint.policy(),0)[1],places=10)
        joint.step();stream.step();np.testing.assert_allclose(stream.R,joint.R[mapping],atol=1e-12);np.testing.assert_allclose(stream.A,joint.A[mapping],atol=1e-12)
        with self.assertRaisesRegex(ValueError,'chunk-local BR'):stream.measure()
    def test_extra_legal_response_size_has_real_descendants(self):
        import os
        from gto.qualification.build import load
        rules,_=load(os.environ.get('QUALIFICATION_BUILD','/tmp/native-qualification'))
        ns=sc.expanded_tree(rules,[0,1,8,9,18,102],[23])
        found=[n for n in ns if n['actor']>=0 and n.get('native_prefix')==[[0,0,6]]]
        self.assertEqual(len(found),1);self.assertIn(23,found[0]['native_actions'])
        later=[n for n in ns if n['actor']>=0 and n.get('native_prefix')==[[0,0,6],[0,1,21]]]
        self.assertEqual(len(later),1);self.assertIn(1,later[0]['native_actions']);self.assertIn(102,later[0]['native_actions'])

    def test_vectorized_native_parent_cache_matches_original(self):
        from gto.qualification.active_policy import Policy as Old
        from gto.qualification.stream_policy import Policy as New
        from gto.qualification.build import load
        import os
        rules,native=load(os.environ.get('QUALIFICATION_BUILD','/tmp/native-qualification'))
        ns=ac.native_tree(rules,[0,1,8]);blocks=[pcs.block(self.lib,[0,5,10,15,20],.3),pcs.block(self.lib,[0,5,10,16,21],.7)]
        q=ac.Game(self.lib,ns,blocks);q.A[:]=np.random.default_rng(17150102).random(q.S)
        class F:policy_digest='test-only'
        f=F();f.native=native;f.rules=rules
        old=Old(q,f,{});new=New(q,f,{})
        for a,b in zip(old.backoff,new.backoff):
            self.assertEqual(a.keys(),b.keys())
            for key in a:np.testing.assert_allclose(a[key],b[key],atol=1e-12)

    def test_cached_partitions_match_original_and_preserve_history(self):
        from gto.qualification import stream_index,stream_sampling
        bs=[pcs.block(self.lib,[0,5,10,15,20],.3),pcs.block(self.lib,[0,5,10,16,21],.7)]
        ns=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5),dict(actor=1,children=[3,4],round=1),dict(actor=-1,children=[],round=1,c0=2),dict(actor=1,children=[5,6],round=3),dict(actor=-1,children=[],round=3,c0=-3,c1=6),dict(actor=-1,children=[],round=3,c0=2)]
        base=ac.Game(self.lib,ns,bs);split=[(2,base.keys[2][0][0])]
        original=ac.Game(self.lib,ns,bs,split);fast=stream_index.Game(self.lib,ns,bs,split)
        self.assertEqual(original.keys,fast.keys);np.testing.assert_array_equal(original.active,fast.active)
        q=stream_sampling.Game(self.lib,ns,bs,split);q.R[:]=np.random.default_rng(17150105).random(q.S);q.A[:]=q.R
        other=stream_sampling.replace_bank(q,bs[::-1]);
        for st,t,n,k in q.rows:
            dst=other.base[k];np.testing.assert_array_equal(other.R[dst:dst+t*n],q.R[st:st+t*n]);np.testing.assert_array_equal(other.A[dst:dst+t*n],q.A[st:st+t*n])
        with tempfile.TemporaryDirectory() as d:
            path=d+'/state.npz';other.save(path);before=other.policy();other.R.fill(0);other.restore(path);np.testing.assert_array_equal(other.policy(),before)
        before=other.policy();stream_sampling.reset_target(other);np.testing.assert_allclose(other.policy(),before,atol=1e-14);self.assertEqual(other.A.sum(),0)

    def test_batched_causal_features_equal_preserved_scalar_function(self):
        from gto.qualification.stream_features import features
        boards=[[0,4,8,13,18],[0,1,5,9,14],[48,0,4,9,14],[0,5,10,15,20]]
        for board in boards:
            block=pcs.block(self.lib,board);holes=block['holes'][::37]
            for r in (3,4,5):
                self.assertEqual(features(holes,board[:r]),[ac.feature(self.lib,h,board[:r]) for h in holes])

    def test_new_bank_current_policy_matches_pre_draw_frozen_native_policy(self):
        import copy,os
        from gto.qualification import stream_sampling,sampling_policy
        from gto.qualification.build import load
        from gto.qualification.native_mccfr import betting
        from gto.qualification.public_response import observe
        from gto.qualification.policy import act
        rules,native=load(os.environ.get('QUALIFICATION_BUILD','/tmp/native-qualification'));nodes=ac.native_tree(rules,[0,1,8])
        a=pcs.block(self.lib,[0,5,10,15,20]);b=pcs.block(self.lib,[0,5,10,16,21]);q=stream_sampling.Game(self.lib,nodes,[a]);q.R[:]=np.random.default_rng(17150107).random(q.S);q.A[:]=q.R*.7
        new=stream_sampling.replace_bank(q,[b]);current=copy.copy(q);current.A=current.R
        class F:
            policy_digest='test-only'
            def row(self,o,average=False):return [float(x==1) for x in o.actions]
        f=F();f.native=native;f.rules=rules;p=sampling_policy.Policy(current,f,{});pi=new.policy(False)
        wanted=[]
        for r in range(4):wanted.append(next(k for k,n in enumerate(nodes) if n['actor']>=0 and n['round']==r))
        for k in wanted:
            n=nodes[k];state=betting(rules)
            for h in n['native_prefix']:
                while state.round<h[0]:state.next_round()
                act(state,h[2] if h[2] in (0,1) else 3 if h[2]==-3 else h[2]+2)
            while state.round<n['round']:state.next_round()
            for h in (0,197,1080):
                o=observe(state,tuple(map(int,b['holes'][h])),b['board'][:(0,3,4,5)[n['round']]]);before=p.row(o);at=int(new.active[0,k,h]);after=pi[at:at+len(n['children'])]
                np.testing.assert_allclose(after,[before[o.actions.index(x)] for x in n['native_actions']],atol=1e-14)

    def test_depth_first_BR_and_finite_refinement_envelope_match_matrix_oracle(self):
        from gto.qualification import stream_sampling,stream_measure
        bs=[pcs.block(self.lib,[0,5,10,15,20],.2),pcs.block(self.lib,[0,5,10,16,21],.8)]
        ns=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5),dict(actor=1,children=[3,4],round=3),dict(actor=-1,children=[],round=3,c0=-3,c1=6),dict(actor=-1,children=[],round=3,c0=2)]
        q=stream_sampling.Game(self.lib,ns,bs);q.A[:]=np.random.default_rng(17150108).random(q.S)
        for fine in (False,True):
            old=stream_br.finite_measure(q,fine);new=stream_measure.measure(q,fine)
            for field in ('EV_bb','BR_SB_bb','BR_BB_bb','NashConv_bb'):self.assertAlmostEqual(old[field],new[field],places=10)
        bound=stream_measure.refinement_envelope(q);self.assertIsNone(bound['full_native_NC_upper']);self.assertGreaterEqual(min(bound['exact_same_policy_finite_information_gains']),-1e-10)

if __name__=='__main__':unittest.main()
