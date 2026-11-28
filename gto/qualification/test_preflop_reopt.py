"""Kernel estimand and independent native settlement regressions."""
import itertools,math,os,time,unittest
import numpy as np
from gto.qualification.preflop_reopt import *
from gto.qualification.range_continuation import INDEX
from gto.qualification.action_native import native_value
from gto.native.training import NativeGame

class WeightTests(unittest.TestCase):
    def test_board_chance_correction_exact_small_deck(self):
        # For a fixed disjoint private deal, sum q(board)*importance =1.
        boards=list(itertools.combinations(range(10),2));holes={0,1,2,3}
        mass=sum(not holes.intersection(b) for b in boards)/len(boards)
        self.assertAlmostEqual(mass*math.comb(10,2)/math.comb(6,2),1)
        self.assertAlmostEqual(RATIO,math.prod((52-i)/(48-i) for i in range(5)))
    def test_aggregation_skips_shared_cards_and_preserves_net(self):
        a=np.array([INDEX[(0,1)],INDEX[(0,2)]]);b=np.array([INDEX[(0,3)],INDEX[(3,4)]]);r=np.arange(1326)
        got=aggregate(a,b,r,6);expected=np.zeros(169**2)
        for x in a:
            for y in b:
                if not set(HOLES[x]).intersection(HOLES[y]):expected[CLASS[x]*169+CLASS[y]]+=6*np.sign(r[x]-r[y])
        np.testing.assert_array_equal(got,expected)
        self.assertEqual(aggregate(a,b,r,6,fold=-3).sum(),-6)

@unittest.skipUnless(os.environ.get('RANGE_BUILD') and os.environ.get('QUALIFICATION_BUILD'),'native and range builds required')
class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p=load(os.environ['QUALIFICATION_BUILD'],ARTIFACT,os.environ['RANGE_BUILD']+'/range.so')
    def test_kernel_scalar_replay_with_native_oracle(self):
        p=self.p;nodes=tree(p.rules);states=matched_states(p.rules,nodes)
        # A low-pot and a 3bet pot, multiple physical deals, exact native returns.
        for k,b in [x for x in states.items() if not x[1].done][:2]:
            board=[40,41,42,43,44];aa=np.array([INDEX[(0,1)],INDEX[(2,3)]]);bb=np.array([INDEX[(4,5)],INDEX[(6,7)]])
            values,_=rollout(p,b,board,98117,time.monotonic()+30,[aa,bb])
            expected=np.zeros(169**2)
            class Deterministic:
                def row(self,o,average=False):
                    if o.round==0:
                        a=history_action(b.history[len(o.history)])
                    else:
                        ctx=p.context(p.state(o.history),o.board,p.ranges(o.history,o.board))
                        a=int(choices(p,ctx,98117,o.board,o.history)[INDEX[o.own]])
                    return [float(x==a) for x in o.actions]
            for a in aa:
                for c in bb:
                    deck=list(HOLES[a])+list(HOLES[c])+board
                    value=native_value(Deterministic(),p.native,NativeGame([100,100]),deck,0)*2
                    expected[CLASS[a]*169+CLASS[c]]+=value
            np.testing.assert_allclose(values,expected,atol=1e-12)
    def test_mixture_sampler_matches_every_bucket_probabilities(self):
        p=self.p;b=next(x for x in matched_states(p.rules,tree(p.rules)).values() if not x.done)
        board=(40,41,42);ctx=p.context(b,board,p.ranges(tuple(b.history),board));hist=tuple(b.history)
        # Enumerate pseudorandom coins; statistical tolerance >6 sigma.
        counts=np.zeros((p.buckets,len(ctx['available'])));representatives=[ctx['bucket'].index(k) for k in range(p.buckets)]
        for seed in range(4000):
            acts=choices(p,ctx,seed,board,hist)
            for k,i in enumerate(representatives):counts[k,ctx['available'].index(acts[i])]+=1
        for k,i in enumerate(representatives):np.testing.assert_allclose(counts[k]/4000,p.probs(ctx,i),atol=.045)

if __name__=='__main__':unittest.main()
