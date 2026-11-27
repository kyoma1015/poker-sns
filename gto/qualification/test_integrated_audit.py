"""Independent restricted BR, nonlinear clipping and causal-key audit."""
import ctypes as C,os,tempfile,unittest
import numpy as np
from gto.qualification import integrated_br as br,public_chance_solver as pcs

class RestrictedOracle(unittest.TestCase):
    def test_same_infoset_aggregated_BR_matches_existing_independent_dense_kernel(self):
        from gto.abstract import model
        from gto.qualification import fullstreet_solver as fs
        with tempfile.TemporaryDirectory() as d:
            lib=pcs.build(d);blocks=[pcs.block(lib,[0,5,10,15,20],.3),pcs.block(lib,[0,5,10,16,21],.7)]
            nodes=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5),dict(actor=1,children=[3,4],round=3),dict(actor=-1,children=[],round=3,c0=-3,c1=6),dict(actor=-1,children=[],round=3,c0=2)]
            # BR uses equal board weights; dense law chosen to match that exactly.
            for b in blocks:b['weight']=.5
            dense=[]
            for b in blocks:
                h=b['holes'];r=b['ranks'];valid=~(h[:,None,:,None]==h[None,:,None,:]).any(axis=(2,3));dense.append(dict(b,mass=valid/1070190.,equity=(r[:,None]>r[None,:])+.5*(r[:,None]==r[None,:])))
            game=fs.Game(lib,nodes,dense);game.R[:]=np.random.default_rng(17139001).random(game.S);pi=game.policy(False);rows=[]
            for block in blocks:
                row=[]
                for k,n in enumerate(nodes):
                    if n['actor']<0:row.append(None);continue
                    round=n['round'];group=block['public']>>(3-round);code=np.array(block['codes'])>>(3-round);indices=game.base[k]+(group*(169<<round)+code)*len(n['children'])
                    row.append(dict(pi=np.array([pi[i:i+len(n['children'])] for i in indices]),keys=[(k,group,int(c)) for c in code]))
                rows.append(row)
            got=br.measure(lib,nodes,[b['board'] for b in blocks],rows);expected=[game.evaluate_owner(pi,p) for p in (0,1)]
            self.assertAlmostEqual(got['EV_bb'],expected[0][0],places=10);self.assertAlmostEqual(got['BR_SB_bb'],expected[0][1],places=10);self.assertAlmostEqual(got['BR_BB_bb'],expected[1][1],places=10)
            # Refining observations is an upper bound only IN THIS projected game.
            physical=br.measure(lib,nodes,[b['board'] for b in blocks],rows,physical=True)
            self.assertGreaterEqual(physical['NashConv_bb']+1e-10,got['NashConv_bb'])
    def test_rotation_is_a_chance_bijection_not_strategy_or_seat_permutation(self):
        import itertools
        worlds=list(itertools.permutations(range(6)));rotated=[x[2:]+x[:2] for x in worlds]
        self.assertEqual(set(worlds),set(rotated))
        self.assertEqual(sum((x[0]-2*x[2]+3*x[4])**2 for x in worlds),sum((x[0]-2*x[2]+3*x[4])**2 for x in rotated))
        self.assertIsNone(br.transfer_bound(.01))
        self.assertAlmostEqual(br.transfer_bound(.01,continuation_uniform_error=.02,chance_uniform_error=.03,omitted_gains=[.04,.05],information_gains=[.06,.07]),.33)
    def test_unbiased_raw_estimator_does_not_imply_unbiased_clip(self):
        samples=np.array([[1.,-1.],[-1.,1.]])
        np.testing.assert_array_equal(samples.mean(axis=0),[0.,0.]);np.testing.assert_array_equal(np.maximum(0,samples).mean(axis=0),[.5,.5])
        np.testing.assert_array_equal(np.maximum(0,samples.mean(axis=0)),[0.,0.])

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native required')
class NativeAudit(unittest.TestCase):
    def test_coarse_prior_constancy_signed_checkpoint_and_snapshot_query(self):
        from pathlib import Path
        import json
        from gto.qualification import integrated_solver as u,sparse_solver as s
        from gto.qualification.build import load
        from gto.qualification.native_mccfr import betting
        from gto.qualification.public_response import observe
        with tempfile.TemporaryDirectory() as d:
            rules,_=load(os.environ['QUALIFICATION_BUILD']);im=u.build(Path(d)/'new',os.environ['QUALIFICATION_BUILD'])
            eq=json.loads(Path('docs/qa/integrated-solver-20261126/prior-equities.json').read_text())['values'];w,o=s.warm(type('Prior',(),{'pre_equities':staticmethod(lambda *args:eq)}),17120101)
            origin=o;q=u.Solver(im,w,origin,17139002,coarse=True,signed_regret=True);seen={};rng=np.random.default_rng(17139003);collisions=0
            for _ in range(2000):
                cs=rng.choice(52,7,replace=False).tolist();own=cs[:2];board=cs[2:];r=q.core.query(own,board,0,3,[],[1,4,5,6],[2,2],[0,0],[98,98],0,True)
                if r['key'] in seen:np.testing.assert_array_equal(r['prior'],seen[r['key']]);collisions+=1
                seen[r['key']]=r['prior']
            self.assertGreater(collisions,50)
            from gto.abstract import model
            q.import_preflop_checkpoint('docs/qa/sparse-generalization-20261124/hu-final/17120101/compact/best',rules)
            root=betting(rules);observations=[observe(root,g[0],[]) for g in model.classes()];before=[q.row(o,True) for o in observations]
            q.rebase_warm()
            for o,p in zip(observations,before):
                np.testing.assert_allclose(q.row(o,True),p,atol=1e-14)
                r=q.core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,False)
                np.testing.assert_allclose(r['probabilities'],p,atol=1e-14)
            # Lazy opponent allocation changes storage, not updates or RNG.
            import struct
            def active(path):
                raw=path.read_bytes();at=0
                def num():
                    nonlocal at
                    x=struct.unpack_from('=Q',raw,at)[0];at+=8;return x
                def blob():
                    nonlocal at
                    n=num();x=raw[at:at+n];at+=n;return x
                blob();blob();t=num();halt=num();rng=blob();E=num()
                for _ in range(E):blob();n=num();at+=8*n
                count=num();out={}
                for _ in range(count):
                    key=blob();n=num();actions=struct.unpack_from('='+str(n)+'q',raw,at);at+=8*n;arrays=[]
                    for j in range(3):arrays.append(struct.unpack_from('='+str(n)+'d',raw,at));at+=8*n
                    visits,avg,warm=num(),num(),num()
                    if visits or avg:out[key]=(actions,arrays,visits,avg,warm)
                self.assertEqual(at,len(raw));return (t,halt,rng,out),count
            full=u.Solver(im,w,origin,17139011);lazy=u.Solver(im,w,origin,17139011,lazy_rows=True)
            for j in range(3):self.assertTrue(full.step(10)['complete']);self.assertTrue(lazy.step(10)['complete'])
            a=Path(d)/'full';b=Path(d)/'lazy';full.core.save(str(a),'same');lazy.core.save(str(b),'same');x,n=active(a);y,m=active(b);self.assertEqual(x,y);self.assertLess(m,n)
            print('exact lazy active-R/A/RNG rows',n,m)
            # Existing independent dense all-path oracle, same native chip ledger.
            from gto.qualification.test_integrated_solver import Integrated
            oracle=Integrated('test_public_plan_expectation_matches_dense_native_reference');oracle.module=im;oracle.w=w;oracle.origin=origin;oracle.rules=rules;oracle.native=load(os.environ['QUALIFICATION_BUILD'])[1]
            for coarse in (False,True):
                oracle.q=lambda stacks=(100,100),coarse=coarse:u.Solver(im,w,{},17139004,stacks=stacks,baseline=True,coarse=coarse)
                oracle.test_public_plan_expectation_matches_dense_native_reference()
            moments=[]
            for use in (False,True):
                small=u.Solver(im,w,{},17139013,stacks=(3,3),baseline=use);mean=second=mass=0.
                def walk(plan):
                    nonlocal mean,second,mass
                    r=small.core.trace([4,9,14,19,24],0,plan)
                    if not r['complete']:
                        for a in range(len(r['need'])):walk(plan+[a])
                    else:
                        z=sum(x['R'][-1]-x['R'][0] for x in r['updates'] if len(x['key'])==4 and x['key'][0]==0 and x['key'][1]==0);p=r['probability'];mass+=p;mean+=p*z;second+=p*z*z
                walk([]);self.assertAlmostEqual(mass,1.,places=10);moments.append((mean,max(0,second-mean*mean)))
            self.assertAlmostEqual(moments[0][0],moments[1][0],places=10);print('tiny native root gradient mean/variance control/baseline',moments)
            self.assertTrue(q.step(10)['complete']);q.save(Path(d)/'cp');other=u.Solver(im,w,origin,17139002,coarse=True,signed_regret=True);other.import_preflop_checkpoint('docs/qa/sparse-generalization-20261124/hu-final/17120101/compact/best',rules);other.rebase_warm();other.restore(Path(d)/'cp');q.step(10);other.step(10)
            a=Path(d)/'a';b=Path(d)/'b';q.core.save(str(a),'same');other.core.save(str(b),'same');self.assertEqual(a.read_bytes(),b.read_bytes())
