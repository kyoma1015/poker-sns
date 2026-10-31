"""Real original NativeState vs separate compiled complete-game helper."""
import importlib
from itertools import permutations
import os
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.onebb_certificate import representative
from gto.hand169 import CLASSES


class OneBBNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path[:0]=[os.environ['GTO_NATIVE_MODULE_DIR'],os.environ['GTO_ONEBB_MODULE_DIR']]
        cls.native=importlib.import_module('pokerid_g12');cls.helper=importlib.import_module('pokerid_onebb')

    def test_all169roots_are_fold_call_and_real_postflop_has_no_decisions(self):
        game=NativeGame([2,2])
        for label in CLASSES:
            hero=representative(label);opponent=[c for c in range(52) if c not in hero][:2]
            state=self.native.NativeState(game)
            for card in hero+opponent:state.apply_action(card)
            self.assertEqual(state.legal_actions(),[0,1]);self.assertEqual(state.current_player(),0)
            state.apply_action(1)
            while not state.is_terminal():
                self.assertTrue(state.is_chance_node());state.apply_action(state.chance_outcomes()[0][0])
            self.assertEqual(sum(state.returns()),0)

    def test_cpp_sampler_reproducible_and_terminal_counts_conserved(self):
        game=NativeGame([2,2])
        a=self.helper.sample(game,[48,49],256,17);b=self.helper.sample(game,[48,49],256,17)
        self.assertEqual(a,b);self.assertEqual(a['wins']+a['losses']+a['ties'],256)

    def test_complete_native_payout_suit_order_and_seat_exchange_symmetries(self):
        game=NativeGame([2,2]);rng=random.Random(17)
        for _ in range(20):
            cards=rng.sample(range(52),9);state=self.native.NativeState(game)
            for card in cards[:4]:state.apply_action(card)
            state.apply_action(1)
            for card in cards[4:]:state.apply_action(card)
            expected=state.returns();self.assertEqual(self.helper.settle_deal(game,cards),expected)
            for permutation in permutations(range(4)):
                mapped=[4*(c//4)+permutation[c%4] for c in cards]
                self.assertEqual(self.helper.settle_deal(game,mapped),expected)
            reversed_hero=[cards[1],cards[0],*cards[2:]]
            self.assertEqual(self.helper.settle_deal(game,reversed_hero),expected)
            swapped=cards[2:4]+cards[:2]+cards[4:]
            self.assertEqual(self.helper.settle_deal(game,swapped),[-v for v in expected])
            self.assertEqual(self.helper.settle_deal(game,cards,True),[-1,1])

    def test_noncalibration_games_and_invalid_holes_are_refused(self):
        for game in (NativeGame([4,4]),NativeGame([2,2],bba=2),NativeGame([2,2],rake_num=1,rake_den=10)):
            with self.assertRaises(ValueError):self.helper.sample(game,[48,49],1,17)
        with self.assertRaises(ValueError):self.helper.sample(NativeGame([2,2]),[48,48],1,17)


if __name__=='__main__':unittest.main()
