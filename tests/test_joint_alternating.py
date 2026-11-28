import json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import joint_stream as s,joint_updates as u,joint_alternating as a,joint_reach as j

class AlternatingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tmp=tempfile.TemporaryDirectory();cls.train=u.build(Path(cls.tmp.name)/'train');cls.br=s.build(Path(cls.tmp.name)/'br')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):
        self.tmpdir=tempfile.TemporaryDirectory();self.addCleanup(self.tmpdir.cleanup);self.root=Path(self.tmpdir.name)
        self.rows=[{'representative':[0,4,8],'multiplicity':1},{'representative':[1,5,9],'multiplicity':3}];self.codes=[0,8]
        self.data=[[.2,.02,.3,.12,.1,.07,.4,.36],[.1,.09,.2,.12,.3,.12,.4,.04]]
        self.reader=patch.object(s.cache,'read',self.read);self.reader.start();self.addCleanup(self.reader.stop)
        baseline=s.Store(self.root/'baseline',self.rows)
        with baseline.db:baseline.put('baseline:ready',b'1')
        self.parent=u.Store(self.root/'parent',self.rows,'cfr_plus');self.parent.initialize(baseline,'unused');self.parent.train(self.train,'unused',epochs=3,max_blocks=6)
    def read(self,path,row):return {'codes':self.codes},self.data[self.rows.index(row)]
    def fork(self,name):return a.Store(self.root/name,self.rows,self.root/'parent')
    def reference(self):
        worlds=[]
        for board,row in enumerate(self.rows):
            for h,hc in enumerate(self.codes):
                for v,vc in enumerate(self.codes):
                    z,e=self.data[board][2*(h*2+v):2*(h*2+v)+2];worlds.append({'flop':row['representative'],'signals':(hc,vc),'mass':z*row['multiplicity']/4,'equity':e/z})
        g=j.prepare(s.tree()[0],worlds);R=[0.]*len(g['width']);S=[0.]*len(R);ns,base,rows,P,T,b=s.layout(2)
        for k,key,index in g['keys']:
            board=0 if ns[k]['street']=='preflop' else next(i for i,r in enumerate(self.rows) if tuple(r['representative'])==key[0]);t=key[0] if ns[k]['street']=='preflop' else self.codes.index(key[1]);r,avg=self.parent.state(board,2);at=base[k]+t*len(ns[k]['children'])
            for action in range(len(ns[k]['children'])):R[index+action]=r[at+action];S[index+action]=avg[at+action]
        return g,R,S
    def python_stage(self,g,R,S,owner,t):
        ns,ws=g['nodes'],g['worlds'];W=len(ws);pi=[0.]*len(R)
        for k,key,i in g['keys']:
            n=len(ns[k]['children']);v=[max(0.,x) for x in R[i:i+n]];z=sum(v);pi[i:i+n]=[x/z for x in v] if z else [1/n]*n
        reach0=[[0.]*W for _ in ns];reach1=[[0.]*W for _ in ns];reach0[0]=reach1[0]=[1.]*W;values=[[0.]*W for _ in ns]
        for k,node in enumerate(ns):
            for action,child in enumerate(node['children']):
                for w in range(W):
                    p=pi[g['info'][k*W+w]+action];reach0[child][w]=reach0[k][w]*(p if node['actor']==0 else 1.);reach1[child][w]=reach1[k][w]*(p if node['actor']==1 else 1.)
        grad=[0.]*len(R);avg=[0.]*len(R)
        for k in range(len(ns)-1,-1,-1):
            node=ns[k]
            for w,world in enumerate(ws):
                if node['actor']<0:values[k][w]=node['c0']+node['c1']*world['equity'];continue
                i=g['info'][k*W+w];values[k][w]=sum(pi[i+x]*values[c][w] for x,c in enumerate(node['children']))
                if node['actor']!=owner:continue
                sign=1 if owner==0 else -1;own=(reach0 if owner==0 else reach1)[k][w];opp=(reach1 if owner==0 else reach0)[k][w]
                for action,child in enumerate(node['children']):grad[i+action]+=world['mass']*opp*sign*(values[child][w]-values[k][w]);avg[i+action]+=world['mass']*own*pi[i+action]
        for k,key,i in g['keys']:
            if ns[k]['actor']==owner:
                for action in range(len(ns[k]['children'])):R[i+action]=max(0.,R[i+action]+grad[i+action]);S[i+action]+=t*avg[i+action]
    def test_full_owner_sweeps_equal_independent_monolithic_python(self):
        x=self.fork('x');g,R,S=self.reference()
        for owner in (0,1):self.python_stage(g,R,S,owner,4)
        x.train(self.train,'unused',epochs=1,max_blocks=4)
        ns,base,rows,P,T,b=s.layout(2)
        for k,key,index in g['keys']:
            board=0 if ns[k]['street']=='preflop' else next(i for i,r in enumerate(self.rows) if tuple(r['representative'])==key[0]);t=key[0] if ns[k]['street']=='preflop' else self.codes.index(key[1]);r,avg=x.state(board,2);at=base[k]+t*len(ns[k]['children'])
            for action in range(len(ns[k]['children'])):self.assertAlmostEqual(r[at+action],R[index+action],delta=1e-10);self.assertAlmostEqual(avg[at+action],S[index+action],delta=1e-10)
        pi=[0.]*len(S)
        for k,key,i in g['keys']:
            n=len(ns[k]['children']);z=sum(S[i:i+n]);pi[i:i+n]=[v/z for v in S[i:i+n]] if z else [1/n]*n
        expected=sum(j.independent_br(g,pi,owner) for owner in (0,1));actual=a.evaluate(x,self.br,'unused');self.assertAlmostEqual(actual['restricted_nashconv_interval_bb'][1],expected,delta=1e-10)
    def test_inherited_arrays_are_exact_and_parent_unchanged(self):
        before=a.numeric_digest(self.parent.db);x=self.fork('x');self.assertEqual(a.numeric_digest(x.db),before);x.train(self.train,'unused',epochs=1,max_blocks=4);self.assertEqual(a.numeric_digest(self.parent.db),before)
    def test_half_sweep_and_partial_population_not_evaluable(self):
        x=self.fork('x');x.train(self.train,'unused',max_blocks=1)
        with self.assertRaisesRegex(ValueError,'both full'):a.evaluate(x,self.br,'unused')
        x.train(self.train,'unused',max_blocks=1);self.assertEqual(x.meta()['owner'],1);self.assertEqual(x.meta()['cursor'],0)
        with self.assertRaisesRegex(ValueError,'both full'):a.evaluate(x,self.br,'unused')
    def test_atomic_restart_and_budget(self):
        x=self.fork('x');y=self.fork('y');x.train(self.train,'unused',epochs=1,max_blocks=4);y.train(self.train,'unused',max_blocks=2);before=y.digest()
        with self.assertRaisesRegex(RuntimeError,'transaction'):y.train(self.train,'unused',crash=True)
        self.assertEqual(before,y.digest());y.db.close();y=self.fork('y');y.train(self.train,'unused',max_blocks=2);self.assertEqual(x.digest(),y.digest());before=y.digest();y.train(self.train,'unused',seconds=0);self.assertEqual(before,y.digest())
if __name__=='__main__':unittest.main()
