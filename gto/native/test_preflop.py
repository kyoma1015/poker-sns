"""Real native preflop legality; no equilibrium claim."""
import importlib
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame, contract_for
from gto.native.preflop import decision, describe


class Preflop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.environ['GTO_NATIVE_MODULE_DIR'])
        cls.native = importlib.import_module('pokerid_g12')

    def test_fourbet_and_response_every_table_size(self):
        for n in range(2, 10):
            game = NativeGame([200]*n)
            for history, stage, size in (([], 'rfi', 6), ([8], 'vs_open', 18),
                    ([8,20], 'vs_3bet', 42), ([8,20,44], 'vs_4bet', 90)):
                with self.subTest(n=n, stage=stage):
                    row = describe(decision(self.native, game, history))
                    self.assertEqual(row['stage'], stage)
                    actions = {a['id']:a for a in row['legal_actions']}
                    self.assertEqual(actions[0]['kind'], 'fold')
                    self.assertEqual(actions[1]['kind'], 'call')
                    self.assertEqual(actions[size+2]['raise_to_chips'], size)

    def test_short_allin_does_not_reopen_raise(self):
        game = NativeGame([200,200,20])
        state = decision(self.native, game, [8,20,1,22])
        self.assertEqual([a['id'] for a in describe(state)['legal_actions']], [0,1])

    def test_limped_pot_is_not_rfi(self):
        self.assertEqual(describe(decision(self.native, NativeGame([200]*6), [1]))['stage'], 'limped_pot')

    def test_fivebet_response_remains_available(self):
        game = NativeGame([400,400])
        self.assertEqual(describe(decision(self.native, game, [8,20,44,92]))['stage'], 'vs_5bet_plus')

    def test_unvisited_policy_cannot_be_fabricated(self):
        from gto.native.preflop import frequencies
        state = decision(self.native, NativeGame([200,200]), [])
        key = state.information_state_string(0)
        class Rows:
            def keys(self): return [key]
            def row(self, _): return {'actions':state.legal_actions(), 'average':[0]*len(state.legal_actions())}
        with self.assertRaisesRegex(ValueError, 'unvisited'):
            frequencies(Rows(), state, {key:1})

    def test_actual_trained_frequency_query_preserves_partial_status(self):
        from gto.native.preflop import frequencies
        from gto.native.hand169_bridge import context_of
        game = NativeGame([4,4])
        solver = self.native.Solver(game,.6,17,True,True,.1)
        for _ in range(200): solver.run_iteration()
        state = decision(self.native,game,[])
        context = describe(state)['context']
        # Synthetic mass tests transport only; it is never claimed as true reach.
        weights = {key:1 for key in solver.keys() if context_of(key)==context}
        report = frequencies(solver,state,weights)
        self.assertEqual(report['decision']['stage'],'rfi')
        self.assertFalse(report['complete'])
        for hand in report['hands'].values():
            self.assertIsNone(hand['ev'])
            if hand['frequencies'] is not None:
                self.assertAlmostEqual(sum(hand['frequencies']),1)

    def test_invalid_and_postflop_history_rejected(self):
        game = NativeGame([200,200])
        for history in ([2], [5], [1,1], [0], [True]):
            with self.subTest(history=history), self.assertRaises((ValueError, RuntimeError)):
                decision(self.native, game, history)

    def test_seven_rake_profiles_and_ante(self):
        profiles = [(0,1,None)] + [(1,den,cap) for den in (20,10) for cap in (None,10,20)]
        contracts = set()
        for num, den, cap in profiles:
            game = NativeGame([200]*6, bba=2, rake_num=num,rake_den=den,rake_cap=cap)
            self.assertEqual(describe(decision(self.native,game,[8,20,44]))['stage'], 'vs_4bet')
            contracts.add(contract_for(game))
        self.assertEqual(len(contracts),7)

    def test_unsupported_native_rules_fail_before_solver(self):
        for kwargs in ({'bba':1},{'rake_num':1,'rake_den':3},{'rake_cap':True},{'rake_cap':2}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                NativeGame([200,200], **kwargs)


if __name__ == '__main__': unittest.main()
