import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import joint_stream as s,joint_updates as u,joint_training as t,joint_alternating as a

class TrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();p=Path(cls.tmp.name)
        cls.legacy=t.build(p/'old','legacy');cls.vector=t.build(p/'new','vector');cls.br=s.build(p/'br')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):
        self.tmpdir=tempfile.TemporaryDirectory();self.addCleanup(self.tmpdir.cleanup);self.root=Path(self.tmpdir.name)
        self.rows=[{'representative':[0,4,8],'multiplicity':1},{'representative':[1,5,9],'multiplicity':3}]
        self.values=[[.2,.02,.3,.12,.1,.07,.4,.36],[.1,.09,.2,.12,.3,.12,.4,.04]]
        p=patch.object(s.cache,'read',lambda path,row:({'codes':[0,8]},self.values[self.rows.index(row)]));p.start();self.addCleanup(p.stop)
        base=s.Store(self.root/'base',self.rows)
        with base.db:base.put('baseline:ready',b'1')
        parent=u.Store(self.root/'parent',self.rows,'cfr_plus');parent.initialize(base,'unused');parent.train(self.legacy,'unused',epochs=3,max_blocks=6)
        self.parent_digest=a.numeric_digest(parent.db);parent.db.close();base.db.close()
    def fork(self,name,backend):
        x=t.Store(self.root/name,self.rows,self.root/'parent',backend);self.addCleanup(x.close);return x
    def test_inherits_every_numeric_byte_without_mutating_parent(self):
        x=self.fork('x','vector');self.assertEqual(x.logical_digest(),self.parent_digest)
        x.train(self.vector,'unused',epochs=1,max_blocks=4)
        self.assertEqual(a.numeric_digest(x.parent),self.parent_digest)
    def test_full_training_arrays_strategy_and_independent_br_match(self):
        old=self.fork('old','legacy');new=self.fork('new','vector')
        for x,lib in ((old,self.legacy),(new,self.vector)):x.train(lib,'unused',epochs=2,max_blocks=8)
        for i in range(2):
            for xs,ys in zip(old.state(i,2),new.state(i,2)):
                for x,y in zip(xs,ys):self.assertAlmostEqual(x,y,delta=1e-10)
            for average in (False,True):
                ps=[s.strategy(*z.state(i,2),s.layout(2)[2],average) for z in (old,new)]
                for x,y in zip(*ps):self.assertAlmostEqual(x,y,delta=1e-10)
        results=[t.evaluate(x,self.br,'unused') for x in (old,new)]
        for key in ('restricted_nashconv_interval_bb','sb_ev_interval_bb','sb_br_gain_bb','bb_br_gain_bb'):
            x,y=results[0][key],results[1][key]
            if isinstance(x,list):
                for m,n in zip(x,y):self.assertAlmostEqual(m,n,delta=1e-10)
            else:self.assertAlmostEqual(x,y,delta=1e-10)
    def test_resume_is_byte_deterministic_and_crash_atomic(self):
        x=self.fork('x','vector');y=self.fork('y','vector');x.train(self.vector,'unused',max_blocks=4);y.train(self.vector,'unused',max_blocks=1)
        before=y.digest()
        with self.assertRaisesRegex(RuntimeError,'transaction'):y.train(self.vector,'unused',crash=True)
        self.assertEqual(before,y.digest());y.train(self.vector,'unused',max_blocks=3)
        self.assertEqual(x.logical_digest(),y.logical_digest());self.assertEqual(x.digest(),y.digest())
        y.db.close();y.parent.close();y=t.Store(self.root/'y',self.rows,self.root/'parent','vector');self.assertEqual(x.digest(),y.digest());y.close()
        # Remove the closed original object's cleanup callback.
    def test_backend_switch_and_half_sweep_are_rejected(self):
        x=self.fork('x','vector')
        with self.assertRaisesRegex(ValueError,'kernel/backend'):x.train(self.legacy,'unused')
        with self.assertRaisesRegex(ValueError,'checkpoint mismatch'):t.Store(self.root/'x',self.rows,self.root/'parent','legacy')
        x.train(self.vector,'unused',max_blocks=1)
        with self.assertRaisesRegex(ValueError,'both full'):t.evaluate(x,self.br,'unused')

if __name__=='__main__':unittest.main()
