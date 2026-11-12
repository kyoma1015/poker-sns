from fractions import Fraction as F
import importlib,os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.belief_observation import compare_hero_actions
from gto.native.infoset_export import PolicySnapshot,evaluate_combo,export_action_classes,report_json

class Export(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR']);cls.n=importlib.import_module('pokerid_g12')
 def setUp(self):
  self.game=NativeGame([4,4]);self.hero=[0,5];self.board=[1,8,17,26,35]
  self.history=[1,1,1,8,17,1,1,26,1,1,35,1];self.deals=[([48,49],F(1,4)),([40,45],F(3,4))]
  rows={}
  def collect(s):
   actions=s.legal_actions();chosen=0 if s.audit()['round']==3 and s.current_player()==1 and 0 in actions else 1
   p={a:F(a==chosen) for a in actions};rows[s.information_state_string(s.current_player())]=p;return p
  compare_hero_actions(self.n,self.game,self.hero,self.deals,self.board,self.history,[1,4],collect)
  self.rows=rows;self.policy=PolicySnapshot(rows)
 def record(self,**kw):
  args=dict(native=self.n,game=self.game,hero_cards=self.hero,deals=self.deals,public_cards=self.board,history=self.history,actions=[1,4],policy=self.policy,hero_mass=F(1,1326));args.update(kw);return evaluate_combo(**args)
 def test_real_native_combo_and_partial_class(self):
  r=self.record();report=export_action_classes([r]);self.assertEqual(report['concrete_combinations'],1)
  hand=next(v for v in report['hands'].values() if v['observed_combinations']);self.assertEqual(hand['observed_action_values'],[F(1),F(2)])
  self.assertIsNone(hand['complete_class_action_values']);self.assertIsNone(report['hand169_ev']);self.assertIsNone(report['native_infoset_ev'])
 def test_snapshot_immutable_from_input_and_stable_digest(self):
  digest=self.policy.digest;key=next(iter(self.rows));self.rows[key].clear();self.assertEqual(self.policy.digest,digest);self.assertEqual(self.record().action_values,(F(1),F(2)))
 def test_snapshot_unknown_and_invalid_probabilities_refused(self):
  with self.assertRaises(ValueError):PolicySnapshot({'key':{1:F(1,2)}})
  with self.assertRaises(ValueError):PolicySnapshot({'key':{True:F(1)}})
  with self.assertRaises(ValueError):self.record(policy=PolicySnapshot({'key':{1:F(1)}}))
 def test_callback_without_snapshot_refused(self):
  with self.assertRaises(ValueError):self.record(policy=lambda s:{1:F(1)})
 def test_duplicate_combo_and_empty_export_refused(self):
  r=self.record()
  with self.assertRaises(ValueError):export_action_classes([r,r])
  with self.assertRaises(ValueError):export_action_classes([])
 def test_observation_and_policy_identity_required(self):
  from dataclasses import replace
  r=self.record()
  for field in ['observation_digest','policy_digest','config_digest']:
   with self.subTest(field=field),self.assertRaises(ValueError):export_action_classes([r,replace(r,cards=(2,6),**{field:'a'*64})])
 def test_action_identity_required(self):
  from dataclasses import replace
  r=self.record()
  with self.assertRaises(ValueError):export_action_classes([r,replace(r,cards=(2,6),actions=(4,1))])
 def test_zero_mass_remains_unknown(self):
  r=self.record(hero_mass=F(0));v=next(x for x in export_action_classes([r])['hands'].values() if x['observed_combinations']);self.assertIsNone(v['observed_action_values'])
 def test_invalid_mass_refused(self):
  for weight in [True,1.0,F(-1)]:
   with self.subTest(weight=weight),self.assertRaises(ValueError):self.record(hero_mass=weight)
 def test_record_frozen_and_explicit_support_provenance(self):
  from dataclasses import FrozenInstanceError
  r=self.record();self.assertEqual(r.support_size,2);self.assertFalse(r.support_complete)
  with self.assertRaises(FrozenInstanceError):r.hero_mass=F(2)
 def test_board_blocks_expected_coverage(self):
  report=export_action_classes([self.record()]);self.assertEqual(sum(x['eligible_combinations'] for x in report['hands'].values()),1081)
 def test_observed_native_snapshot_and_checkpoint_digest(self):
  from tempfile import TemporaryDirectory
  from gto.native.training import train_batch
  game=NativeGame([4,4]);a=self.n.Solver(game,.6,17,True,True,.1);b=self.n.Solver(game,.6,17,True,True,.1)
  with TemporaryDirectory() as d:
   train_batch(a,game,4000,Path(d)/'all');train_batch(b,game,2000,Path(d)/'half')
   c=self.n.Solver(game,.6,17,True,True,.1);train_batch(c,game,2000,Path(d)/'resumed',resume=Path(d)/'half')
   one=PolicySnapshot.from_solver(self.n,a);two=PolicySnapshot.from_solver(self.n,c)
   self.assertEqual(one.digest,two.digest);a.run_iteration();self.assertEqual(one.digest,two.digest)
   with self.assertRaises(ValueError):PolicySnapshot.from_solver(self.n,a,max_rows=1)
 def test_complete_class_requires_every_eligible_combination(self):
  from dataclasses import replace
  from itertools import combinations
  from gto.hand169 import hand_class
  from gto.native.hand169_bridge import card_name
  r=self.record();label=hand_class([card_name(c) for c in r.cards]);rows=[]
  for cards in combinations([c for c in range(52) if c not in self.board],2):
   if hand_class([card_name(c) for c in cards])==label:rows.append(replace(r,cards=cards))
  value=export_action_classes(rows)['hands'][label]
  self.assertTrue(value['coverage_complete']);self.assertEqual(value['complete_class_action_values'],[F(1),F(2)])
  self.assertIsNone(export_action_classes(rows[:-1])['hands'][label]['complete_class_action_values'])
 def test_exact_json_transport_keeps_null_and_separates_reach(self):
  import json
  r=self.record();out=json.loads(report_json(export_action_classes([r])))
  self.assertIsNone(out['hand169_ev']);self.assertIsNone(out['native_infoset_ev'])
  p=out['combo_provenance'][0];self.assertEqual(p['explicit_hero_mass'],{'rational':{'numerator':'1','denominator':'1326'}})
  self.assertNotEqual(p['observation_evidence_mass'],p['explicit_hero_mass']);self.assertFalse(p['support_complete'])
 def test_action_order_is_identity_not_position_guess(self):
  r=self.record(actions=[4,1]);self.assertEqual(r.action_values,(F(2),F(1)));self.assertEqual(export_action_classes([r])['actions'],[4,1])

if __name__=='__main__':unittest.main()
