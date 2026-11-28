"""6/9-player offline profile tests; no equilibrium/strategy-acceptance claim."""
import os,unittest
from gto.qualification.build import load
from gto.qualification.multiplayer_scope import OfflineProfile,replay
from gto.native.training import NativeGame

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class MultiplayerScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rules,cls.native=load(os.environ['QUALIFICATION_BUILD'])
    def profile(self,g,p):return OfflineProfile(g,p,players=g.num_players(),provider_digest='a'*64)
    def deck(self,n,river):
        holes=[48,49,44,45,40,41]+[0,1,2,3,5,6,7,9,10,11,12,13][:2*(n-3)]
        prefix=holes+[8,17,26,32,river]
        return prefix+[c for c in range(52) if c not in prefix]
    @staticmethod
    def sidepot_policy(o):
        if o.actor>=3:return {0:1.}
        if o.actor==0 and o.round==0:return {12:1.} # raise-to10chips, all in.
        return {1:1.}
    def test_all_seats_own_cards_and_causal_public_board_only(self):
        for n in (6,9):
            g=NativeGame([100]*n);seen=set();deck=list(range(52))
            def p(o):
                seen.add(o.actor)
                self.assertEqual(o.own,tuple(deck[2*o.actor:2*o.actor+2]))
                self.assertEqual(o.board,tuple(deck[2*n:2*n+(0,3,4,5)[o.round]]))
                self.assertEqual(len(o.remaining),n);self.assertFalse(hasattr(o,'holes'))
                self.assertIn(1,o.actions);return {1:1.}
            r=replay(self.native,g,self.profile(g,p),deck=deck,seed=71)
            self.assertEqual(seen,set(range(n)));self.assertEqual(len(r['net_chips']),n)
            # Six: shared5555+6board tiesall; nine: seat8holds66+board66777,
            # quads6 beats other players' boardfullhouse77766. All seats eligible.
            self.assertEqual(r['net_chips'],[0]*6 if n==6 else [-2]*8+[16])
            self.assertEqual(sum(r['net_chips']),0);self.assertIsNone(r['NashConv'])
    def test_unequal_six_and_nine_player_sidepots_refund_hand_oracle(self):
        # Folded extra players contribute0, but their cards remain removed.
        # Contributions10/6/2: refund4 toAA, main6, side8.
        # AAwin=(+8,-6,-2); KKK=(-6,+8,-2); QQQ=(+2,-6,+4).
        for n in (6,9):
            g=NativeGame([10,6,2]+[10]*(n-3));p=self.profile(g,self.sidepot_policy)
            for river,expected in ((4,[8,-6,-2]),(46,[-6,8,-2]),(42,[2,-6,4])):
                r=replay(self.native,g,p,deck=self.deck(n,river),seed=72)
                self.assertEqual(r['net_chips'],expected+[0]*(n-3))
                self.assertEqual(r['refund_chips'],[4]+[0]*(n-1))
                self.assertEqual([x['amount'] for x in r['pots']],[6,8])
                self.assertEqual(r['rake_chips'],0)
    def test_ante_rake_sidepot_vector_is_not_zero_sum(self):
        # BB6 spends ante2+live4. Main8(includingante), side4, refund6.
        # Whole-hand10%floor rake1 is removed from main first.
        for n in (6,9):
            g=NativeGame([10,6,2]+[10]*(n-3),bba=2,rake_num=1,rake_den=10)
            p=self.profile(g,self.sidepot_policy)
            for river,expected in ((4,[7,-6,-2]),(46,[-4,5,-2]),(42,[0,-6,5])):
                r=replay(self.native,g,p,deck=self.deck(n,river),seed=73)
                self.assertEqual(r['net_chips'],expected+[0]*(n-3))
                self.assertEqual(r['rake_chips'],1);self.assertEqual(sum(r['net_chips']),-1)
                self.assertEqual([x['amount'] for x in r['pots']],[8,4])
                self.assertEqual(r['refund_chips'],[6]+[0]*(n-1))
    def test_no_flop_no_drop_with_bb_ante(self):
        for n in (6,9):
            g=NativeGame([100]*n,bba=2,rake_num=1,rake_den=10)
            p=self.profile(g,lambda o:{0:1.} if 0 in o.actions else {1:1.})
            r=replay(self.native,g,p,deck=list(range(52)),seed=74)
            self.assertEqual(r['board'],[]);self.assertEqual(r['rake_chips'],0)
            self.assertEqual(r['net_chips'],[-1,1]+[0]*(n-2))
    def test_hu_contract_and_mutated_rules_cannot_label_multiplayer(self):
        g=NativeGame([10]*6)
        with self.assertRaises(ValueError):OfflineProfile(g,lambda o:{1:1.},players=2,provider_digest='a'*64)
        p=self.profile(g,lambda o:{1:1.})
        with self.assertRaises(ValueError):replay(self.native,NativeGame([12]*6),p,deck=list(range(52)),seed=1)
        g._native_rules['rate_num']=1
        with self.assertRaises(ValueError):p.validate_game(g)
    def test_missing_illegal_and_invalid_inputs_fail_without_partial_ev(self):
        g=NativeGame([10]*9)
        for provider in (lambda o:None,lambda o:{99999:1.},lambda o:{1:.5},lambda o:{1:float('nan')}):
            with self.assertRaises(ValueError):replay(self.native,g,self.profile(g,provider),deck=list(range(52)),seed=1)
        p=self.profile(g,lambda o:{1:1.})
        for deck in ([0]*52,list(range(51)),[False]+list(range(1,52))):
            with self.assertRaises(ValueError):replay(self.native,g,p,deck=deck,seed=1)
        with self.assertRaises(ValueError):replay(self.native,g,p,deck=list(range(52)),seed=1,max_steps=1)

if __name__=='__main__':unittest.main()
