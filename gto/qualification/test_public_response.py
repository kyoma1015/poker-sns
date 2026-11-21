"""Response completeness and native legality only; no EV or GTO certification."""
import os
import random
import unittest
from fractions import Fraction
from gto.qualification.build import load
from gto.qualification.policy import act, legal
from gto.qualification.public_response import MissingResponse, PublicResponse, observe
from gto.abstract.model import classes
from gto.native.training import NativeGame


@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'), 'native build required')
class PublicResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules, cls.native = load(os.environ['QUALIFICATION_BUILD'])

    def betting(self, stacks=(100, 100)):
        r = self.rules.Rules(bb=2, ante_order='ante_first', stack_basis='before_ante',
            dead_eligibility='all_live', rake_rate=Fraction(0), rake_cap=None,
            no_flop_no_drop=True, cap_scope='whole_hand', rounding='floor', rake_ante=True)
        return self.rules.Betting(list(stacks), r)

    def response(self, provider):
        return PublicResponse(provider, game_digest='a'*64, provider_digest='b'*64)

    def test_unknown_is_error_not_fold(self):
        with self.assertRaises(MissingResponse):
            self.response(lambda o: None).row(self.betting(), [0, 1], [])

    def test_invalid_rows_rejected(self):
        for weights in ({}, {999: 1}, {0: float('nan')}, {0: -1, 1: 2},
                        {0: .2}, {True: 1}, {0: True}, {0: '1'}):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                self.response(lambda o: weights).row(self.betting(), [0, 1], [])

    def test_every_root_size_and_169_classes_have_exact_response(self):
        keys = set()
        for action in legal(self.betting()):
            b = self.betting(); act(b, action)
            if b.done or b.actor is None:
                continue
            keys.add(observe(b, [0, 1], []).key)
            # Explicit call fixture is a transport regression, not a GTO policy.
            p = self.response(lambda o: {1: 1})
            for group in classes():
                row = p.row(b, group[0], [])
                self.assertEqual(sum(w for _, w in row), 1)
                self.assertEqual(dict(row)[1], 1)
        self.assertEqual(len(keys), 98)

    def test_full_history_not_just_price_and_cards(self):
        b = self.betting(); act(b, 7)
        c = self.betting(); act(c, 1); act(c, 7)
        # Even the same raise-to requires a different seat/history response.
        self.assertNotEqual(observe(b, [0, 1], []).key, observe(c, [0, 1], []).key)
        self.assertEqual(observe(b, [1, 0], []).key, observe(b, [0, 1], []).key)

    def test_bad_cards_and_terminal_rejected(self):
        for own, board in (([0, 0], []), ([0, 52], []), ([0, 1], [2, 3, 4])):
            with self.assertRaises(ValueError): observe(self.betting(), own, board)
        b = self.betting(); act(b, 0)
        with self.assertRaises(ValueError): observe(b, [0, 1], [])

    def test_bounded_native_paths_all_streets_and_short_allin(self):
        rng = random.Random(1201117); rounds = set(); decisions = 0
        # Uniform provider is ONLY a legality coverage fixture.
        p = self.response(lambda o: {a: Fraction(1, len(o.actions)) for a in o.actions})
        for stacks in ((3, 3), (100, 100)):
            for trial in range(128):
                b = self.betting(stacks)
                s = self.native.NativeState(NativeGame(list(stacks)))
                deck = rng.sample(range(52), 9)
                for card in deck[:4]: s.apply_action(card)
                steps = 0
                while not b.done:
                    while s.is_chance_node():
                        i = len(s.audit().get('board', []))
                        s.apply_action(deck[4+i])
                    board = deck[4:4+(0, 3, 4, 5)[b.round]]
                    own = deck[2*b.actor:2*b.actor+2]
                    row = p.row(b, own, board)
                    self.assertEqual([a for a, _ in row], s.legal_actions())
                    rounds.add(b.round); decisions += 1
                    # Half paths check/call to exercise later streets; others all sizes.
                    action = 1 if trial % 2 == 0 else rng.choice([a for a, _ in row])
                    act(b, action); s.apply_action(action)
                    steps += 1
                    self.assertLess(steps, 256)
                while s.is_chance_node():
                    i = len(s.audit().get('board', [])); s.apply_action(deck[4+i])
                self.assertTrue(s.is_terminal())
                self.assertEqual(s.audit()['history'], [list(h) for h in b.history])
        self.assertEqual(rounds, {0, 1, 2, 3})
        self.assertGreater(decisions, 256)


if __name__ == '__main__': unittest.main()
