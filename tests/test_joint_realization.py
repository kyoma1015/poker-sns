import math,tempfile,unittest
from pathlib import Path
from gto.abstract import joint_realization as m,joint_stream as s,joint_alternating as a
class RealizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tmp=tempfile.TemporaryDirectory();cls.lib=s.build(Path(cls.tmp.name)/'native')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def policies(self,T=2):
        ns,base,rows,P,S,b=s.layout(T);out=[]
        for shift in (0,1):
            pi=[0.]*S
            for start,H,n,k in rows:
                for t in range(H):
                    vals=[1+((i+1+t+shift*3)%5) for i in range(n)];z=sum(vals);pi[start+t*n:start+(t+1)*n]=[v/z for v in vals]
            out.append(pi)
        return out
    def test_own_reach_equals_explicit_ancestor_product(self):
        pi=self.policies()[0];codes=[0,8];ns,base,rows,P,S,b=s.layout(2);parents={c:(k,i) for k,n in enumerate(ns) for i,c in enumerate(n['children'])};actual=m.info_reach(pi,codes)
        for start,H,n,k in rows:
            for t in (0,H-1):
                owner=ns[k]['actor'];key=k;expected=1.
                while key:
                    p,action=parents[key]
                    if ns[p]['actor']==owner:
                        own=t if ns[p]['street']=='flop' or ns[k]['street']=='preflop' else codes[t]//8
                        expected*=pi[base[p]+own*len(ns[p]['children'])+action]
                    key=p
                self.assertAlmostEqual(actual[start+t*n],expected,delta=1e-14)
    def test_one_player_realization_mixture_preserves_affine_expected_payoff(self):
        x,y=self.policies();owners=a.masks(2);obj={'codes':[0,8]};values=[.25,.025,.25,.1,.25,.175,.25,.225]
        def value(pi):return s.block(self.lib,obj,values,[0.]*len(pi),pi,True)['metrics'][0]
        for owner in (0,1):
            right=[v if owners[j]==owner else x[j] for j,v in enumerate(y)]
            for weight in (0.,.25,.5,1.):self.assertAlmostEqual(value(m.mixture(x,right,[0,8],weight)),(1-weight)*value(x)+weight*value(right),delta=1e-10)
    def test_preflop_mixture_cannot_depend_on_board_private_type_population(self):
        x,y=self.policies(2);u,v=self.policies(3);P=s.layout(2)[3]
        self.assertEqual(m.mixture(x,y,[0,8],.25)[:P],m.mixture(u,v,[0,8,16],.25)[:P])
    def test_policy_only_object_cannot_train_or_accept_invalid_policy(self):
        with self.assertRaisesRegex(ValueError,'EVALUATION_ONLY'):m.Evaluation.train(None)
        x,y=self.policies();x[0]=2
        with self.assertRaisesRegex(ValueError,'normalized'):m.mixture(x,y,[0,8])
if __name__=='__main__':unittest.main()
