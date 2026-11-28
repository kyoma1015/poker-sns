import copy,itertools,json,math,os,unittest
from pathlib import Path
from gto.qualification.range_continuation import HOLES,INDEX,RangePolicy,kernel,load_kernel
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.native_mccfr import betting
from gto.qualification.public_response import observe
from gto.qualification.policy import act,legal
from gto.abstract import model

@unittest.skipUnless(os.environ.get('RANGE_BUILD'),'new range library required')
class PublicRanges(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=load_policy(os.environ['QUALIFICATION_BUILD'],'docs/qa/release-route-20261118/strategy.json.gz')
        cls.lib=load_kernel(Path(os.environ['RANGE_BUILD'])/'range.so')
    def test_joint_card_removal_rank_and_bucket_mass_matches_enumeration(self):
        for board in ([4,9,14],[4,9,14,19],[4,9,14,19,24]):
            r=[[0.]*1326,[0.]*1326]
            pairs=[(48,49),(0,48),(1,2),(0,2),(25,26)]
            for p in (0,1):
                for j,h in enumerate(pairs):r[p][INDEX[h]]=float(j+1+p)
            prob,sign,bucket,mass=kernel(self.lib,board,r,8);ps=[0.]*64;vs=[0.]*64;total=0
            def rank(h):
                cs=list(h)+board
                if len(cs)==6:return max(model.rank(self.lib,list(c)) for c in itertools.combinations(cs,5))
                return model.rank(self.lib,cs)
            for h0 in pairs:
                for h1 in pairs:
                    if set(h0).intersection(h1) or set(h0+h1).intersection(board):continue
                    w=r[0][INDEX[h0]]*r[1][INDEX[h1]];k=bucket[INDEX[h0]]*8+bucket[INDEX[h1]]
                    ps[k]+=w;vs[k]+=w*((rank(h0)>rank(h1))-(rank(h0)<rank(h1)));total+=w
            self.assertAlmostEqual(mass,total)
            for j in range(64):
                self.assertAlmostEqual(prob[j],ps[j]/total);self.assertAlmostEqual(sign[j],vs[j]/ps[j] if ps[j] else 0)
        with self.assertRaises(ValueError):kernel(self.lib,[0,0,1],r)
    def test_preflop_posterior_uses_likelihood_and_own_public_removal(self):
        policy=RangePolicy(self.base,self.lib);b=betting(self.base.rules);act(b,8);act(b,1)
        own=(48,49);board=(4,9,14);o=observe(b,own,board);post=policy.posterior(o)
        weights=[]
        for h in HOLES:
            if set(h).intersection(own+board):weights.append(0.);continue
            x=betting(self.base.rules)
            # BB actor's opponent is SB: only SB3BB open probability enters.
            weights.append(self.base.provider(observe(x,h,[]))[8])
        z=sum(weights)
        for a,w in zip(post,weights):self.assertAlmostEqual(a,w/z)
    def test_policy_normalized_and_cache_order_cannot_change_same_observation(self):
        p=RangePolicy(self.base,self.lib);b=betting(self.base.rules);act(b,8);act(b,1)
        board=[4,9,14];o=observe(b,[48,49],board);r=p.row(o,True)
        self.assertAlmostEqual(sum(r),1);self.assertTrue(all(x>0 for x in r));a=max(o.actions)
        act(b,a);child=observe(b,[0,1],board);expected=p.row(child,True)
        p.contexts.clear();p.range_cache.clear();actual=p.row(child,True)
        self.assertEqual(expected,actual)
        fresh=RangePolicy(self.base,self.lib);self.assertEqual(actual,fresh.row(child,True))
    def test_public_action_updates_range_and_unknown_raise_short_allin_legal(self):
        p=RangePolicy(self.base,self.lib);b=betting(self.base.rules);act(b,8);act(b,1)
        board=[4,9,14];o=observe(b,[48,49],board);before=p.posterior(o)
        act(b,7) # legal2.5chip? action7 is5chips: off-model exact observed size.
        x=observe(b,[0,1],board);r=p.row(x,True);self.assertAlmostEqual(sum(r),1)
        self.assertTrue(all(v>0 for v in r));self.assertEqual(len(r),len(legal(b)))
        # BB40, SB80, BB94 is a short all-in (14<last full40).
        c=betting(self.base.rules);act(c,8);act(c,1);act(c,42);act(c,82)
        self.assertEqual(c.price,80);self.assertEqual(c.last_full,40)
        rr=p.row(observe(c,[48,49],board),True);self.assertAlmostEqual(sum(rr),1)
        self.assertIn(96,legal(c));act(c,96)
        y=observe(c,[0,1],board);self.assertEqual(y.actions,(0,1));self.assertAlmostEqual(sum(p.row(y,True)),1)
    def test_selected_public_bet_updates_exact_conditional_likelihood(self):
        p=RangePolicy(self.base,self.lib);b=betting(self.base.rules);act(b,8);act(b,1)
        board=[4,9,14];own=(0,1);pre=copy.deepcopy(b);bbpre=betting(self.base.rules);act(bbpre,8)
        weights=[]
        for h in HOLES:
            if set(h).intersection(own+tuple(board)):weights.append(0.);continue
            call=self.base.provider(observe(bbpre,h,[]))[1]
            bet=p.provider(observe(pre,h,board))[8]
            weights.append(call*bet)
        act(b,8);post=p.posterior(observe(b,own,board));z=sum(weights)
        for a,w in zip(post,weights):self.assertAlmostEqual(a,w/z)
    def test_future_board_cache_never_contaminates_previous_street(self):
        p=RangePolicy(self.base,self.lib);b=betting(self.base.rules);act(b,8);act(b,1)
        flop=observe(b,[48,49],[4,9,14]);expected=p.row(flop,True)
        act(b,1);act(b,1)
        p.row(observe(b,[48,49],[4,9,14,19]),True)
        p.row(observe(b,[48,49],[4,9,14,20]),True)
        self.assertEqual(expected,p.row(flop,True))
    def test_one_chip_short_allin_marker_matches_actual_native(self):
        from gto.native.training import NativeGame
        p=RangePolicy(self.base,self.lib);b=betting(self.base.rules);state=self.base.native.NativeState(NativeGame([100,100]))
        for c in (48,49,0,1):state.apply_action(c)
        for a in (101,1):act(b,a);state.apply_action(a)
        for c in (4,9,14):state.apply_action(c)
        self.assertEqual(legal(b),state.legal_actions());self.assertIn(3,legal(b))
        act(b,3);state.apply_action(3);self.assertEqual(b.history[-1][2],-3)
        self.assertEqual([list(h) for h in b.history],state.audit()['history'])
        o=observe(b,[48,49],[4,9,14]);row=p.row(o,True)
        self.assertEqual(o.actions,tuple(state.legal_actions()));self.assertAlmostEqual(sum(row),1)
    def test_preflop_all169_remains_exactly_frozen_B(self):
        for n in self.base.nodes:
            if n['actor']<0:continue
            b=betting(self.base.rules)
            for h in n['native_prefix']:act(b,h[2] if h[2]<=1 else h[2]+2)
            p=RangePolicy(self.base,self.lib)
            for g in model.classes():
                o=observe(b,g[0],[]);self.assertEqual(p.row(o,True),self.base.row(o,True))

    def test_no_future_card_or_opponent_hand_argument(self):
        p=RangePolicy(self.base,self.lib);b=betting(self.base.rules);act(b,8);act(b,1)
        o=observe(b,[48,49],[4,9,14]);a=p.row(o,True);p.contexts.clear();p.range_cache.clear()
        self.assertEqual(a,p.row(o,True));self.assertEqual(o.board,(4,9,14));self.assertFalse(hasattr(o,'opponent'))

if __name__=='__main__':unittest.main()
