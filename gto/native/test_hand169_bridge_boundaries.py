"""Fixed malformed-format and exact chance-weight oracle boundaries."""
import test_hand169_bridge as fixtures
from fractions import Fraction
import json
import unittest
from gto.native.hand169_bridge import context_of,export_context
from gto.native.poker_oracle import exact_policy_value

class NewBoundaries(unittest.TestCase):
    setUpClass=classmethod(fixtures.BridgeTests.setUpClass.__func__)
    game=fixtures.BridgeTests.game
    state=fixtures.BridgeTests.state

    def test_unhashable_cards_rejected_as_value_error(self):
        d=json.loads(self.state().information_state_string(0)); d['hand']=[[48],49]
        with self.assertRaises(ValueError):context_of(json.dumps(d))

    def test_unhashable_board_rejected_as_value_error(self):
        d=json.loads(self.state().information_state_string(0));d['board']=[[0],1,2]
        with self.assertRaises(ValueError):context_of(json.dumps(d))

    def test_oracle_exact_uniform_river_chance(self):
        s=self.state()
        for a in [1,1,8,17,26,1,1,32,1,1]:s.apply_action(a)
        self.assertTrue(s.is_chance_node())
        report=exact_policy_value(s,lambda node:{1:Fraction(1)},max_nodes=1000)
        self.assertEqual(report['values'],[Fraction(20,11),Fraction(-20,11)])
        self.assertEqual(report['terminal_nodes'],44)

if __name__=='__main__':unittest.main()
