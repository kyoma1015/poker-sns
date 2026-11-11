import unittest
from gto.abstract import joint_training as t,joint_training_window as w,joint_stream as s,joint_reach as j
from tests import test_joint_training as fixtures

class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixtures.TrainingTests.setUpClass()
    @classmethod
    def tearDownClass(cls):fixtures.TrainingTests.tearDownClass()
    def setUp(self):
        self.f=fixtures.TrainingTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.source=self.f.fork('source','vector');self.source.train(self.f.vector,'unused',max_blocks=4)
        self.cut=self.f.root/'cutoff';self.before=[self.source.state(i,2)[1] for i in range(2)];w.capture(self.source,self.cut)
    def view(self):
        result=w.Window(self.source,self.cut,self.f.root/'evaluation');self.addCleanup(result.close);return result
    def test_exact_delayed_mass_and_original_history_unchanged(self):
        self.source.train(self.f.vector,'unused',epochs=3,max_blocks=12);before=self.source.logical_digest();view=self.view()
        for i in range(2):
            reg,avg=view.state(i,2);r,a=self.source.state(i,2);self.assertEqual(reg,r);self.assertEqual(avg,[x-y for x,y in zip(a,self.before[i])])
        t.evaluate(view,self.f.br,'unused');self.assertEqual(before,self.source.logical_digest())
    def test_earlier_cutoff_and_no_overwrite_required(self):
        with self.assertRaisesRegex(ValueError,'earlier'):self.view()
        with self.assertRaisesRegex(ValueError,'overwrite'):w.capture(self.source,self.cut)
    def test_live_source_update_cannot_mix_evaluation_epochs(self):
        self.source.train(self.f.vector,'unused',max_blocks=4);view=self.view();self.source.train(self.f.vector,'unused',max_blocks=1)
        with self.assertRaisesRegex(ValueError,'advanced'):view.state(0,2)
    def test_window_independent_monolithic_br(self):
        self.source.train(self.f.vector,'unused',epochs=3,max_blocks=12);view=self.view();worlds=[]
        for b,row in enumerate(self.f.rows):
            for h,hc in enumerate((0,8)):
                for v,vc in enumerate((0,8)):
                    z,e=self.f.values[b][2*(h*2+v):2*(h*2+v)+2];worlds.append({'flop':row['representative'],'signals':(hc,vc),'mass':z*row['multiplicity']/4,'equity':e/z})
        g=j.prepare(s.tree()[0],worlds);pi=[0.]*len(g['width']);ns,base,_,P,_,_=s.layout(2)
        for k,key,index in g['keys']:
            board=0 if ns[k]['street']=='preflop' else next(i for i,row in enumerate(self.f.rows) if tuple(row['representative'])==key[0]);typ=key[0] if ns[k]['street']=='preflop' else (0,8).index(key[1]);_,avg=view.state(board,2);at=base[k]+typ*len(ns[k]['children']);n=len(ns[k]['children']);total=sum(avg[at:at+n]);pi[index:index+n]=[x/total for x in avg[at:at+n]] if total else [1/n]*n
        expected=sum(j.independent_br(g,pi,owner) for owner in (0,1));actual=t.evaluate(view,self.f.br,'unused');self.assertAlmostEqual(expected,actual['restricted_nashconv_interval_bb'][1],delta=1e-10)

if __name__=='__main__':unittest.main()
