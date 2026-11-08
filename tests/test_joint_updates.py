import json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import joint_stream as s,joint_updates as u,joint_update_audit as a

class IndependentAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.lib=s.build(Path(cls.tmp.name)/'br');cls.fast=u.build(Path(cls.tmp.name)/'train')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_exact_path_enumeration_all_gradients_average_weights_and_signs(self):
        for b,pi in enumerate(a.policies()):
            expected=a.oracle(b,pi);actual=a.native(self.lib,b,pi)
            for key in ('grad','avg','action_num','action_den'):
                for x,y in zip(actual[key],expected[key]):self.assertAlmostEqual(x,y,delta=1e-12)
            self.assertAlmostEqual(actual['ev'],expected['ev'],delta=1e-12)
    def test_all64_pure_responses_each_owner_match_full_population_br(self):
        pi=a.policies();native=a.native_br([a.native(self.lib,b,p) for b,p in enumerate(pi)])
        for owner in (0,1):self.assertAlmostEqual(native[owner],a.brute_br(pi,owner),delta=1e-12)
        ev=sum(a.WEIGHT[b]*a.oracle(b,p)['ev'] for b,p in enumerate(pi));self.assertGreaterEqual(native[0]-ev,-1e-12);self.assertGreaterEqual(native[1]+ev,-1e-12)
    def test_zero_own_reach_excluded_but_opponent_reach_zero_removes_regret(self):
        pi=a.policies()[0];pi[:2]=[1.,0.];out=a.native(self.lib,0,pi)
        self.assertEqual(out['avg'][8:10],[0.,0.]);self.assertGreater(max(abs(x) for x in out['grad'][8:10]),.01)
        pi[4:8]=[1.,0.,1.,0.];out=a.native(self.lib,0,pi)
        self.assertEqual(out['grad'][8:12],[0.]*4)
    def test_training_only_kernel_exactly_preserves_gradients_and_averages(self):
        for b,pi in enumerate(a.policies()):
            full=a.native(self.lib,b,pi);fast=a.native(self.fast,b,pi)
            for key in ('grad','avg','ev'):self.assertEqual(full[key],fast[key])
            self.assertEqual(fast['leaf'],[0.]*len(fast['leaf']))
    def test_update_formula_hand_calculated(self):
        args=([2.,-2.],[3.,5.],[-4.,1.],[.5,1.5],2)
        r,av=u.update(*args,'vanilla_linear');self.assertEqual(r,[-2.,-1.]);self.assertEqual(av,[4.,8.])
        r,av=u.update(*args,'cfr_plus');self.assertEqual(r,[0.,0.]);self.assertEqual(av,[4.,8.])
        r,av=u.update(*args,'dcfr');self.assertEqual(r,[-1.,-.5]);self.assertAlmostEqual(av[0],(3+.5)*4/9,delta=1e-14);self.assertAlmostEqual(av[1],(5+1.5)*4/9,delta=1e-14)
        r,_=u.update([1.],[0.],[1.],[0.],2,'dcfr');self.assertAlmostEqual(r[0],2*2**1.5/(2**1.5+1))
    def test_regret_matching_and_average_have_separate_inputs(self):
        rows=[(0,1,2,0)]
        self.assertEqual(s.strategy([-2.,-1.],[1.,3.],rows,False),[.5,.5]);self.assertEqual(s.strategy([-2.,-1.],[1.,3.],rows,True),[.25,.75])
    def test_analytic_asymmetric_matrix_equilibrium_all_methods(self):
        # A=[[2,-1],[-1,1]] has p=q=(.4,.6), value .2; no solver oracle.
        A=[[2.,-1.],[-1.,1.]]
        for method in ('vanilla',)+u.METHODS:
            R=[[.8e-15,.2e-15],[.3e-15,.7e-15]];S=[[0.,0.],[0.,0.]]
            for t in range(1,16385):
                P=[([max(0,x)/sum(max(0,z) for z in r) for x in r] if sum(max(0,z) for z in r)>0 else [.5,.5]) for r in R]
                q=[[sum(A[i][j]*P[1][j] for j in range(2)) for i in range(2)],[-sum(P[0][i]*A[i][j] for i in range(2)) for j in range(2)]]
                for player in (0,1):
                    v=sum(P[player][i]*q[player][i] for i in range(2));g=[x-v for x in q[player]]
                    if method=='vanilla':R[player]=[x+y for x,y in zip(R[player],g)];S[player]=[x+y for x,y in zip(S[player],P[player])]
                    else:R[player],S[player]=u.update(R[player],S[player],g,P[player],t,method)
            p,q=[[x/sum(row) for x in row] for row in S];nc=max(sum(A[i][j]*q[j] for j in range(2)) for i in range(2))-min(sum(p[i]*A[i][j] for i in range(2)) for j in range(2))
            self.assertLess(nc,.04,method);self.assertAlmostEqual(p[0],.4,delta=.03);self.assertAlmostEqual(q[0],.4,delta=.03)

class ScheduleResume(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tmp=tempfile.TemporaryDirectory();cls.lib=u.build(Path(cls.tmp.name)/'lib');cls.br=s.build(Path(cls.tmp.name)/'br')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_each_method_atomic_resume_and_independent_evaluation(self):
        with tempfile.TemporaryDirectory() as folder:
            rows=[{'representative':[0,4,8],'multiplicity':1},{'representative':[1,5,9],'multiplicity':3}];codes=[0,8]
            def read(path,row):
                b=rows.index(row);return {'codes':codes},[v for z,e in zip(a.MASSES[b],a.EQUITY[b]) for v in (z,z*e)]
            with patch.object(s.cache,'read',read):
                baseline=s.Store(Path(folder)/'frozen',rows)
                with baseline.db:baseline.put('baseline:ready',b'1')
                for method in u.METHODS:
                    x=u.Store(Path(folder)/(method+'a'),rows,method);y=u.Store(Path(folder)/(method+'b'),rows,method)
                    x.initialize(baseline,'unused');y.initialize(baseline,'unused');x.train(self.lib,'unused',epochs=2,max_blocks=4)
                    y.train(self.lib,'unused',max_blocks=1);before=y.digest()
                    with self.assertRaisesRegex(RuntimeError,'atomic'):y.train(self.lib,'unused',crash=True)
                    self.assertEqual(before,y.digest());y.db.close();y=u.Store(Path(folder)/(method+'b'),rows,method);y.train(self.lib,'unused',epochs=2,max_blocks=3)
                    self.assertEqual(x.digest(),y.digest());r=u.evaluate(x,self.br,'unused');self.assertEqual(r['coverage'],1);self.assertIsNone(r['positive_regret_bound_bb']);self.assertGreaterEqual(r['restricted_nashconv_interval_bb'][0],0)
                    with self.assertRaisesRegex(ValueError,'mismatch'):u.Store(Path(folder)/(method+'a'),rows,u.METHODS[(u.METHODS.index(method)+1)%3])
    def test_uninitialized_or_zero_budget_does_not_mutate(self):
        with tempfile.TemporaryDirectory() as folder:
            x=u.Store(Path(folder)/'x',[{'representative':[0,4,8],'multiplicity':1}],'dcfr');before=x.digest()
            with self.assertRaisesRegex(ValueError,'initialization'):x.train(self.lib,'unused')
            self.assertEqual(before,x.digest())

if __name__=='__main__':unittest.main()
