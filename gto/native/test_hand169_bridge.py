"""Native format fixture/oracle and actual-engine bridge acceptance."""
import importlib
import json
import os
from pathlib import Path
import sys
import unittest
from fractions import Fraction

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from gto.native.hand169_bridge import context_of, export_context, card_name
from gto.native.poker_oracle import exact_policy_value
from gto.native.training import NativeGame


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
        cls.native=importlib.import_module('pokerid_g12')

    def game(self): return NativeGame([4,4],bb=2,bba=0,rake_num=0,rake_den=1)

    def state(self):
        s=self.native.NativeState(self.game())
        for a in [48,49,0,1]: s.apply_action(a)
        return s

    def test_card_encoding_from_native_header(self):
        self.assertEqual([card_name(x) for x in (0,1,2,3,48,49,50,51)],
            ['2c','2d','2h','2s','Ac','Ad','Ah','As'])

    def test_actual_trained_native_context_export(self):
        g=self.game(); solver=self.native.Solver(g,.6,17,True,True,.1)
        for _ in range(200): solver.run_iteration()
        context=context_of(self.state().information_state_string(0))
        selected=[k for k in solver.keys() if context_of(k)==context]
        self.assertGreater(len(selected),0)
        report=export_context(solver,context,{k:1 for k in selected})
        self.assertEqual(len(report['hands']),169)
        self.assertGreater(report['concrete_combinations'],0)
        self.assertFalse(report['complete'])
        self.assertEqual(report['weight_provenance'],'explicit caller-supplied infoset reach weights')
        for row in report['hands'].values():
            self.assertIsNone(row['ev'])
            if row['frequencies'] is not None: self.assertAlmostEqual(sum(row['frequencies']),1)

    def test_ordered_holes_merge_by_explicit_mass(self):
        context=context_of(self.state().information_state_string(0))
        infos=[]
        for hand in ([48,49],[49,48]):
            d=dict(context,hand=hand); infos.append(json.dumps(d,sort_keys=True))
        class FixtureRows:
            def keys(self): return infos
            def row(self,k): return {'actions':[0,1],'average':[1,0] if k==infos[0] else [0,1]}
        report=export_context(FixtureRows(),context,{infos[0]:1,infos[1]:3})
        self.assertEqual(report['hands']['AA']['frequencies'],[.25,.75])
        self.assertEqual(report['hands']['AA']['combinations'],1)
        self.assertEqual(report['hands']['AA']['reach_mass'],4)

    def test_reach_not_invented(self):
        context=context_of(self.state().information_state_string(0))
        class Rows:
            def keys(self): return [json.dumps(dict(context,hand=[48,49]))]
        with self.assertRaises(ValueError): export_context(Rows(),context,{})

    def test_context_does_not_mix_board_or_betting_history(self):
        context=context_of(self.state().information_state_string(0))
        other=dict(context,betting_history=[[0,0,1,2,2]])
        a=json.dumps(dict(context,hand=[48,49]));b=json.dumps(dict(other,hand=[50,51]))
        class Rows:
            def keys(self):return [a,b]
            def row(self,k):return {'actions':[0,1],'average':[1,1]}
        r=export_context(Rows(),context,{a:1})
        self.assertEqual(r['concrete_combinations'],1)
        with self.assertRaises(ValueError): export_context(Rows(),dict(context,board=[2,3,4]),{})

    def test_action_identity_mismatch_rejected(self):
        context=context_of(self.state().information_state_string(0))
        a=json.dumps(dict(context,hand=[48,49]));b=json.dumps(dict(context,hand=[48,50]))
        class Rows:
            def keys(self):return [a,b]
            def row(self,k):return {'actions':[0,1] if k==a else [0,6],'average':[1,1]}
        with self.assertRaises(ValueError):export_context(Rows(),context,{a:1,b:1})

    def test_real_poker_fold_oracle(self):
        s=self.state()
        report=exact_policy_value(s,lambda node:{0:Fraction(1)},max_nodes=10)
        self.assertEqual(report['values'],[Fraction(-1),Fraction(1)])
        self.assertEqual(report['terminal_nodes'],1)

    def test_real_poker_river_oracle(self):
        s=self.state()
        # Call/check preflop; board 4c 6d 8h Tc Qd, check to river.
        for a in [1,1,8,17,26,1,1,32,1,1,41]: s.apply_action(a)
        self.assertFalse(s.is_chance_node())
        report=exact_policy_value(s,lambda node:{1:Fraction(1)},max_nodes=10)
        self.assertEqual(report['values'],[Fraction(2),Fraction(-2)])
        self.assertEqual(report['terminal_nodes'],1)

    def test_oracle_node_budget_and_policy_normalization(self):
        s=self.state()
        with self.assertRaises(ValueError):exact_policy_value(s,lambda node:{0:Fraction(1,2)},max_nodes=10)
        with self.assertRaises(ValueError):exact_policy_value(s,lambda node:{1:Fraction(1)},max_nodes=1)

if __name__=='__main__':unittest.main()
