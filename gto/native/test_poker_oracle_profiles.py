"""Hand-derived known-card ante/rake/side-pot exact policy expectations."""
import importlib
import os
from pathlib import Path
import sys
import unittest
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from gto.native.training import NativeGame
from gto.native.poker_oracle import exact_policy_value

class Profiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
        cls.native=importlib.import_module('pokerid_g12')

    def turn(self,stacks,holes,actions,*,bba=0,rake_num=0,rake_den=1):
        g=NativeGame(stacks,bb=2,bba=bba,rake_num=rake_num,rake_den=rake_den)
        s=self.native.NativeState(g)
        for a in holes+actions+[8,17,26,32]:s.apply_action(a)
        self.assertTrue(s.is_chance_node())
        return s

    def test_bb_ante_known_card_oracle(self):
        # BB is all-in after ante2+blind2; SB calls another1, retaining2.
        # Main pot6: AA wins42 rivers -> net(+4,-4), loses2 ->(-2,+2).
        s=self.turn([4,4],[48,49,0,1],[1],bba=2)
        r=exact_policy_value(s,lambda node:{1:Fraction(1)},max_nodes=1000)
        self.assertEqual(r['terminal_nodes'],44)
        self.assertEqual(r['values'],[Fraction(41,11),Fraction(-41,11)])

    def test_cash_rake_known_card_oracle(self):
        # Both shove10. Pot20, terminal floor rake2 after flop.
        # AA wins42 rivers ->(+8,-10), loses2 ->(-10,+8).
        s=self.turn([10,10],[48,49,0,1],[12,1],rake_num=1,rake_den=10)
        r=exact_policy_value(s,lambda node:{1:Fraction(1)},max_nodes=1000)
        self.assertEqual(r['values'],[Fraction(79,11),Fraction(-101,11)])
        self.assertEqual(sum(r['values']),-2)

    def test_three_way_unequal_stack_side_pots(self):
        # AA/KK/QQ with contributions10/6/2: refund4 to AA, pots6+8.
        # 38 rivers AA wins ->(+8,-6,-2); 2 kings ->(-6,+8,-2);
        # 2 queens: QQ gets main6, AA gets side8 ->(+2,-6,+4).
        s=self.turn([10,6,2],[48,49,44,45,40,41],[1,12,1])
        r=exact_policy_value(s,lambda node:{1:Fraction(1)},max_nodes=1000)
        self.assertEqual(r['terminal_nodes'],42)
        self.assertEqual(r['values'],[Fraction(148,21),Fraction(-112,21),Fraction(-12,7)])
        self.assertEqual(sum(r['values']),0)

if __name__=='__main__':unittest.main()
