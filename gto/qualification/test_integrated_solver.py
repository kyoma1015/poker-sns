"""Integration gate: independent dense private-pair/path oracle before clipping."""
import ctypes as C,importlib.util,os,tempfile,unittest
from pathlib import Path
import numpy as np
from gto.qualification import sparse_solver as sparse,integrated_solver as integrated,public_chance_solver as pcs
from gto.qualification.build import load
from gto.qualification.native_mccfr import betting
from gto.qualification.public_response import observe
from gto.qualification.policy import act
from gto.native.training import NativeGame

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class Integrated(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.rules,cls.native=load(os.environ['QUALIFICATION_BUILD'])
        cls.module=integrated.build(Path(cls.tmp.name)/'new',os.environ['QUALIFICATION_BUILD'])
        equities=__import__('json').loads(Path('docs/qa/integrated-solver-20261126/prior-equities.json').read_text())['values']
        tables=type('FrozenPrior',(),{'pre_equities':staticmethod(lambda *args:equities)})
        cls.w,cls.origin=sparse.warm(tables,17120101)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def q(self,stacks=(100,100)):
        return integrated.Solver(self.module,self.w,self.origin,17137101,stacks=stacks,extra_support=[dict(round=0,history=[],actions=[18,19])])
    def test_generic_support_prefix_memory_prior_and_checkpoint(self):
        q=self.q();b=betting(self.rules);r=q.core.query([48,49],[],b.actor,0,b.history,list(observe(b,(48,49),()).actions),b.live,b.street,b.remaining,b.price,True)
        self.assertGreater(len(r['actions']),4);self.assertIn(9,r['actions']);self.assertIn(18,r['actions'])
        before=np.array(r['probabilities']);q.add_support(0,[],[15])
        after=q.core.query([48,49],[],b.actor,0,b.history,list(observe(b,(48,49),()).actions),b.live,b.street,b.remaining,b.price,True)
        self.assertIn(15,after['actions']);np.testing.assert_allclose(before,after['probabilities'],atol=1e-14)
        with self.assertRaises(ValueError):q.add_support(0,[],[999])
        step=q.step(10);self.assertTrue(step['complete'],step)
        with tempfile.TemporaryDirectory() as d:
            q.save(d);other=self.q();other.add_support(0,[],[15]);other.restore(d);q.step(10);other.step(10)
            a=Path(d)/'a';z=Path(d)/'b';q.core.save(str(a),'same');other.core.save(str(z),'same');self.assertEqual(a.read_bytes(),z.read_bytes())
        # Same information key must never have a draw-dependent warm prior.
        seen={};rng=np.random.default_rng(17137)
        for _ in range(300):
            deck=rng.choice(52,7,replace=False).tolist();own=deck[:2];board=deck[2:5]
            r=q.core.query(own,board,0,1,[],[1,4,5,6], [2,2],[0,0],[98,98],0,True)
            transformed=lambda xs:[4*(c//4)+(c%4+1)%4 for c in xs]
            perm=q.core.query(transformed(own),transformed(board),0,1,[],[1,4,5,6],[2,2],[0,0],[98,98],0,True)
            self.assertEqual(r['key'],perm['key']);np.testing.assert_allclose(r['prior'],perm['prior'],atol=1e-14)
            key=r['key'];p=np.array(r['prior'])
            if key in seen:np.testing.assert_allclose(p,seen[key],atol=1e-14)
            seen[key]=p
    def test_all_checkpoint_support_and_preflop_average_survive_import(self):
        q=self.q();b=betting(self.rules);o=observe(b,(48,49),[])
        before=q.core.query(o.own,o.board,o.actor,0,o.history,o.actions,o.live,o.street,o.remaining,o.price,True)['actions']
        result=q.import_preflop_checkpoint('docs/qa/sparse-generalization-20261124/hu-final/17120101/compact/best',self.rules)
        after=q.core.query(o.own,o.board,o.actor,0,o.history,o.actions,o.live,o.street,o.remaining,o.price,True)['actions']
        self.assertGreater(result['rows'],1000);self.assertTrue(result['all_old_actions_preserved'])
        self.assertTrue(set(before)<=set(after))
        inherited=next(x['actions'] for x in q.identity['inherited_support'] if not x['history'])
        self.assertTrue(set(inherited)<=set(after))
        # Synthetic old support contains a size omitted by the regenerated grid.
        import struct,gzip,json,hashlib
        from gto.qualification.native_mccfr import digest
        from gto.qualification.policy import sha
        fresh=self.q();identity=dict(prior_tables_digest=fresh.identity['prior_tables_digest'],sources={'gto/qualification/sparse_native.cc':sha(Path('gto/qualification/sparse_native.cc'))},scope='test-only codec fixture')
        number=lambda n:struct.pack('=Q',n)
        blob=lambda b:number(len(b))+b
        raw=blob(b'sparse-native-v1')+blob(digest(identity).encode())+number(0)+blob(b'test finite prewarm, not RNG resume')+number(1)
        raw+=blob(bytes([0,0,0,0]))+number(3)+struct.pack('=3q',0,1,14)
        for a in ([.1,.2,.7],[1.,2.,7.],[.1,.2,.7]):raw+=struct.pack('=3d',*a)
        raw+=number(0)+number(0)+number(1)
        with tempfile.TemporaryDirectory() as stage:
            folder=Path(stage);(folder/'checkpoint.bin.gz').write_bytes(gzip.compress(raw));(folder/'checkpoint.json').write_text(json.dumps(dict(identity=identity,sha256=hashlib.sha256(raw).hexdigest())))
            fresh.import_preflop_checkpoint(folder,self.rules)
        r=fresh.core.query(o.own,o.board,o.actor,0,o.history,o.actions,o.live,o.street,o.remaining,o.price,True)
        self.assertIn(14,r['actions']);np.testing.assert_allclose([r['probabilities'][o.actions.index(a)] for a in (0,1,14)],[.1,.2,.7],atol=1e-14)

    def test_multiplayer_batch_expectation_and_existing_sampler_replay(self):
        from gto.qualification.multiplayer_joint import SparseJoint,Joint,expanded_decks,path_oracle
        from gto.qualification.test_private_integrated_joint import canonical
        ds=expanded_decks(3);game=NativeGame([24,22,20])
        exact=Joint(self.native,game,ds,[.25]*4,action_scope='preflop',max_nodes=5000,max_seconds=30)
        q=integrated.Multiplayer(self.native,game,decks=ds,weights=[.25]*4,chance_batch=4,max_nodes=100000,max_seconds=30)
        q.batch=ds;oracle=path_oracle(exact,exact.policy(False));grad={};avg={}
        import random
        for owner in range(3):
            b=q.collect(owner,ds[0],random.Random(97),{},audit=True)
            for key,dst,scale in [('grad',grad,1.),('avg',avg,.5)]:
                for k,v in b[key].items():dst[k]=dst.get(k,np.zeros(len(v)))+scale*v
        for key in oracle['grad']:
            k=canonical(key)
            np.testing.assert_allclose(grad.get(k,np.zeros_like(oracle['grad'][key])),oracle['grad'][key],atol=2e-11)
            np.testing.assert_allclose(avg.get(k,np.zeros_like(oracle['avg'][key])),oracle['avg'][key],atol=2e-11)
        one=integrated.Multiplayer(self.native,game,chance_batch=1,average_mode='lazy')
        old=SparseJoint(self.native,game,average_mode='lazy')
        one.step();old.step();self.assertEqual(one.rng.getstate(),old.rng.getstate())
        for k in old.R:np.testing.assert_array_equal(one.R[k],old.R[k]);np.testing.assert_array_equal(one.A[k],old.A[k])
        for n in (6,9):
            game=NativeGame([24]*n,bba=2,rake_num=1,rake_den=20)
            q=integrated.Multiplayer(self.native,game,chance_batch=2,average_mode='lazy',max_seconds=5)
            q.step();other=integrated.Multiplayer(self.native,game,chance_batch=2,average_mode='lazy',max_seconds=5)
            other.restore(q.state());q.step();other.step();self.assertEqual(q.state(),other.state())

    def test_stratified_EV_allocation_and_native_context_payoffs(self):
        from gto.qualification.integrated_precision import allocation,tables
        weights=np.array([.001,.02,.1,.0001,0.])
        counts,radius=allocation(weights,.05,1e-7)
        self.assertLessEqual(radius,.05+1e-12);self.assertEqual(counts[-1],0)
        # Independent inequality: allocation has no outcome-dependent sample size.
        self.assertLessEqual(float(np.sum(np.divide(weights**2,counts,out=np.zeros_like(weights),where=counts>0))),2*.05**2/(10000*np.log(2e7)))
        q=self.q();board=[4,9,14,19,24];game=NativeGame([100,100])
        for prefix in ([],[9],[8,23]):
            b,hero,L,C=tables(q,self.rules,prefix);self.assertGreater(float(L.sum()),0)
            for response in (0,1):
                state=self.native.NativeState(game)
                for c in (48,49,0,1):state.apply_action(c)
                for a in prefix:state.apply_action(a)
                state.apply_action(102);state.apply_action(response)
                while state.is_chance_node() and not state.is_terminal():state.apply_action(board[len(state.audit()['board'])])
                value=state.returns()[hero]/2
                if response==0:self.assertEqual(value,b.live[1-hero]/2)
                else:
                    ranks=[self.native.rank7(h+board) for h in ([48,49],[0,1])]
                    self.assertEqual(value,50*((ranks[hero]>ranks[1-hero])-(ranks[hero]<ranks[1-hero])))

    def test_public_plan_expectation_matches_dense_native_reference(self):
        q=self.q((3,3));board=[4,9,14,19,24];block=pcs.block(q.ranklib,board);holes=block['holes'];rank=block['ranks'];T=len(holes)
        valid=~(holes[:,None,:,None]==holes[None,:,None,:]).any(axis=(2,3));M=valid/1070190.;E=(rank[:,None]>rank[None,:])+.5*(rank[:,None]==rank[None,:])
        nodes=[];game=NativeGame([3,3])
        def clone(s):
            c=self.native.NativeState(game)
            for a in s.audit()['replay']:c.apply_action(a)
            return c
        def fill(s):
            while s.is_chance_node() and not s.is_terminal():s.apply_action(board[len(s.audit()['board'])])
        def visit(s):
            fill(s);k=len(nodes);a=s.audit();n=dict(actor=-1,children=[]);nodes.append(n)
            if s.is_terminal():
                ref=betting(self.rules,(3,3))
                for h in a['history']:
                    while ref.round<h[0]:ref.next_round()
                    act(ref,h[2] if h[2] in (0,1) else 3 if h[2]==-3 else h[2]+2)
                while not ref.done:
                    self.assertIsNone(ref.actor);ref.next_round()
                net=[ref.settle(r,True)['net'][0]/2 for r in ([0,1],[0,0],[1,0])]
                self.assertAlmostEqual(net[1],(net[0]+net[2])/2,places=12);n.update(c0=net[0],c1=net[2]-net[0]);return k
            p=s.current_player();n['actor']=p;n['keys']=[];n['pi']=[]
            legal=s.legal_actions()
            for own in holes:
                r=q.core.query(own.tolist(),a['board'],p,a['round'],a['history'],legal,a['live'],a['street'],a['remaining'],a['price'],True)
                n['keys'].append(r['key']);n['pi'].append([r['probabilities'][legal.index(x)] for x in r['actions']]);n['actions']=r['actions']
            n['pi']=np.array(n['pi'])
            for action in n['actions']:
                child=clone(s);child.apply_action(action);n['children'].append(visit(child))
            return k
        root=self.native.NativeState(game)
        for c in (0,1,2,3):root.apply_action(c)
        visit(root);self.assertLess(len(nodes),200)
        for owner in (0,1):
            reach=np.ones((2,len(nodes),T))
            for k,n in enumerate(nodes):
                if n['actor']<0:continue
                for j,c in enumerate(n['children']):
                    reach[:,c]=reach[:,k];reach[n['actor'],c]*=n['pi'][:,j]
            V=np.zeros((len(nodes),T));grad={};avg={}
            for k in reversed(range(len(nodes))):
                n=nodes[k]
                if n['actor']<0:
                    pay=n['c0']+n['c1']*E if owner==0 else -(n['c0']+n['c1'])+n['c1']*E
                    V[k]=(M*pay)@reach[1-owner,k];continue
                child=V[n['children']].T
                V[k]=(child*n['pi']).sum(axis=1) if n['actor']==owner else child.sum(axis=1)
                if n['actor']==owner:
                    for h,key in enumerate(n['keys']):
                        grad.setdefault(key,np.zeros(len(n['actions'])));avg.setdefault(key,np.zeros(len(n['actions'])))
                        grad[key]+=child[h]-V[k,h];avg[key]+=reach[owner,k,h]*n['pi'][h]/1081
            actualG={};actualA={};prob=0.;ev=0.
            def enumerate_plans(plan,integrate_root=False):
                nonlocal prob,ev
                r=q.core.trace(board,owner,plan,integrate_root)
                if not r['complete']:
                    for a in range(len(r['need'])):enumerate_plans(plan+[a],integrate_root)
                else:
                    mass=r['probability'];prob+=mass;ev+=mass*r['value']
                    for u in r['updates']:
                        for name,dst in [('R',actualG),('A',actualA)]:
                            dst.setdefault(u['key'],np.zeros(len(u['actions'])));dst[u['key']]+=mass*np.array(u[name])
            enumerate_plans([]);self.assertAlmostEqual(prob,1.,places=11);self.assertAlmostEqual(ev,float(V[0].sum()),places=10)
            for key in grad:np.testing.assert_allclose(actualG.get(key,np.zeros_like(grad[key])),grad[key],atol=1e-10)
            for key in avg:np.testing.assert_allclose(actualA.get(key,np.zeros_like(avg[key])),avg[key],atol=1e-10)
            actualG={};actualA={};prob=0.;ev=0.;enumerate_plans([],True)
            self.assertAlmostEqual(ev,float(V[0].sum()),places=10)
            self.assertAlmostEqual(prob,len(nodes[0]['actions']),places=10)
            for key in grad:np.testing.assert_allclose(actualG.get(key,np.zeros_like(grad[key])),grad[key],atol=1e-10)
            for key in avg:np.testing.assert_allclose(actualA.get(key,np.zeros_like(avg[key])),avg[key],atol=1e-10)

if __name__=='__main__':unittest.main()
