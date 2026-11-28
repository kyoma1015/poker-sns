import importlib,os,sys,unittest
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.infoset_export import PolicySnapshot
from gto.native.feasible_response import CompletedPolicy
from gto.native.strict_continuation import evaluate,CheckpointPolicy,diagnose,reconstruct,unknown_envelope

class Strict(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR']);cls.native=importlib.import_module('pokerid_g12')
 def test_missing_rows_stop_without_completion_or_point_ev(self):
  policy=PolicySnapshot({'unrelated':{1:F(1)}});game=NativeGame([100,100])
  a=evaluate(self.native,game,policy,samples=32);b=evaluate(self.native,game,policy,samples=32)
  self.assertEqual(a,b);self.assertEqual(a['fallback_actions'],0);self.assertIsNone(a['point_ev_bb'])
  self.assertEqual(a['global']['ev_envelope_bb'],[-50,50]);self.assertEqual(sum(a['stopping_reasons'].values()),32)
  self.assertEqual(a['known_decisions'],{});self.assertFalse(a['full_game_convergence_verified'])
  with self.assertRaises(ValueError):evaluate(self.native,game,CompletedPolicy(policy,'uniform_legal_prior'),samples=32)
 def test_unknown_forced_blind_actions_form_envelope_not_assumed_showdown(self):
  game=NativeGame([2,2]);node=self.native.NativeState(game)
  cards=[48,49,0,1,8,17,26,32,35];cards +=[c for c in range(52) if c not in cards]
  for card in cards[:4]:node.apply_action(card)
  bounds,kind=unknown_envelope(node,cards,4,__import__('json').loads(game._public_config_json))
  self.assertEqual(kind,'terminal_only_envelope');self.assertEqual(bounds,(-1,2))
 def test_trained_postflop_keys_reconstruct_and_policy_remains_readonly(self):
  game=NativeGame([100,100]);solver=self.native.Solver(game,.6,29,True,True,.1)
  for _ in range(256):solver.run_iteration()
  result=diagnose(self.native,solver,game,per_street=4)
  self.assertTrue(result['solver_unchanged']);self.assertTrue(result['native_key_actions_average_roundtrip'])
  self.assertGreater(sum(v for k,v in result['roundtrip_owner_updated_rows'].items() if k!='0'),0)
  policy=CheckpointPolicy(self.native,solver,'0'*64)
  a=evaluate(self.native,game,policy,samples=32);b=evaluate(self.native,game,policy,samples=32)
  self.assertEqual(a,b);self.assertEqual(a['fallback_actions'],0)
  solver.run_iteration()
  with self.assertRaises(ValueError):policy.validate()
if __name__=='__main__':unittest.main()
