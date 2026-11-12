import json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import joint_stream as s,joint_reach as j
from gto.abstract.joint_reach_study import tree

class StreamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.lib=s.build(Path(cls.tmp.name)/'native');cls.old=j.build(Path(cls.tmp.name)/'old')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory();self.addCleanup(self.dir.cleanup)
        self.rows=[{'representative':[0,4,8],'multiplicity':1},{'representative':[1,5,9],'multiplicity':2}]
        self.codes=[0,8];self.data=[[.25,.025,.25,.1,.25,.15,.25,.225],[.25,.225,.25,.15,.25,.1,.25,.025]]
    def reader(self,path,row):
        return {'codes':self.codes,'row':row},self.data[self.rows.index(row)]
    def store(self,name):return s.Store(Path(self.dir.name)/name,self.rows)
    def monolithic(self):
        worlds=[]
        for b,row in enumerate(self.rows):
            for i,a in enumerate(self.codes):
                for v,c in enumerate(self.codes):
                    k=(i*2+v)*2;z,e=self.data[b][k:k+2];worlds.append({'flop':row['representative'],'signals':(a,c),'mass':z*row['multiplicity']/3,'equity':e/z})
        return j.prepare(tree()[0],worlds)
    def test_streamed_updates_equal_monolithic_full_chance_cfr(self):
        store=self.store('a');g=self.monolithic();old=j.Solver(self.old,g)
        with patch.object(s.cache,'read',self.reader):
            store.train(self.lib,'unused',epochs=2,max_blocks=4);expected=old.run(2)
            actual=s.evaluate(store,self.lib,'unused')
        self.assertAlmostEqual(actual['partial_sb_ev_bb'],expected['sb_ev_bb'],delta=1e-8)
        self.assertAlmostEqual(actual['restricted_nashconv_interval_bb'][1],expected['joint_nashconv_bb'],delta=1e-8)
        ns,base,rows,P,S,b=s.layout(2)
        for k,key,i in g['keys']:
            board=0 if ns[k]['street']=='preflop' else next(t for t,r in enumerate(self.rows) if tuple(r['representative'])==key[0])
            reg,sums=store.state(board,2);t=key[0] if ns[k]['street']=='preflop' else self.codes.index(key[1]);at=base[k]+t*len(ns[k]['children'])
            for a in range(len(ns[k]['children'])):
                self.assertAlmostEqual(reg[at+a],old.regret[i+a],delta=1e-8)
                self.assertAlmostEqual(sums[at+a],old.sums[i+a],delta=1e-8)
    def test_restart_and_atomic_rollback(self):
        a=self.store('a');b=self.store('b')
        with patch.object(s.cache,'read',self.reader):
            a.train(self.lib,'unused',epochs=2,max_blocks=4)
            b.train(self.lib,'unused',max_blocks=1);before=b.digest()
            with self.assertRaisesRegex(RuntimeError,'simulated'):b.train(self.lib,'unused',max_blocks=1,crash=True)
            self.assertEqual(before,b.digest());b.db.close();b=self.store('b');b.train(self.lib,'unused',max_blocks=3,epochs=2)
        self.assertEqual(a.digest(),b.digest())
    def test_partial_epoch_cannot_be_evaluated(self):
        a=self.store('a')
        with patch.object(s.cache,'read',self.reader):a.train(self.lib,'unused',max_blocks=1)
        with self.assertRaisesRegex(ValueError,'coherent'):s.evaluate(a,self.lib,'unused')
    def test_shared_preflop_frozen_until_whole_population(self):
        a=self.store('a');before=s.unpack(a.get('pre'))[:2*a.pre]
        with patch.object(s.cache,'read',self.reader):
            a.train(self.lib,'unused',max_blocks=1)
            self.assertEqual(before,s.unpack(a.get('pre'))[:2*a.pre])
            a.train(self.lib,'unused',max_blocks=1)
            self.assertNotEqual(before,s.unpack(a.get('pre'))[:2*a.pre])
    def test_wrong_checkpoint_identity_rejected(self):
        a=self.store('a');a.db.close()
        with self.assertRaisesRegex(ValueError,'identity'):s.Store(Path(self.dir.name)/'a',list(reversed(self.rows)))
    def test_evaluation_resume_and_safe_unknown_bounds(self):
        a=self.store('a');b=self.store('b')
        with patch.object(s.cache,'read',self.reader):
            partial=s.evaluate(a,self.lib,'unused',max_blocks=1)
            self.assertEqual(partial['coverage'],1/3);self.assertIsNone(partial['sb_br_gain_bb']);self.assertFalse(partial['target_0_1_bb_pass'])
            self.assertGreater(partial['sb_ev_interval_bb'][1]-partial['sb_ev_interval_bb'][0],60)
            x=s.evaluate(a,self.lib,'unused');y=s.evaluate(b,self.lib,'unused')
        for k in ('partial_sb_ev_bb','restricted_nashconv_interval_bb','sb_br_gain_bb','state_digest'):self.assertEqual(x[k],y[k])
    def test_zero_wall_budget_preserves_checkpoint(self):
        a=self.store('a');before=a.digest();r=a.train(self.lib,'unused',seconds=0)
        self.assertEqual(r['blocks'],0);self.assertEqual(before,a.digest())
    def test_reported_wall_time_is_not_a_policy_row_offset(self):
        a=self.store('a')
        with patch.object(s.time,'monotonic',return_value=100.):
            result=s.evaluate(a,self.lib,'unused',max_blocks=0)
        self.assertEqual(result['wall_seconds'],0.)

if __name__=='__main__':unittest.main()
