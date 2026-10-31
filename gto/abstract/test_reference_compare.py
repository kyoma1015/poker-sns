import copy,json,math,unittest
from pathlib import Path
from gto.abstract.reference_compare import candidate,compare,condition_differences,target_condition,missing_report
from gto.abstract.precision_archive import unpack
from gto.abstract.precision_runouts import refinement_targets

class ReferenceCompare(unittest.TestCase):
 def setUp(self):
  self.ours=candidate('flop_controller');self.reference=copy.deepcopy(self.ours)
  self.reference.update(schema='pokerid-external-preflop-reference-v1',source={'url':'https://example.invalid/synthetic-test-only','solver':'SYNTHETIC ORACLE — NOT EXTERNAL GTO','retrieved_at':'2026-10-31','usage_permission':'synthetic test'})
 def test_identity_all169_and_action_permutation(self):
  for c in self.reference['contexts'].values():
   c['actions'].reverse()
   for row in c['hands'].values():row['frequencies'].reverse();row['action_ev_bb'].reverse()
  r=compare(self.ours,self.reference)
  self.assertEqual(r['frequency_rows'],676);self.assertEqual(r['ev_rows'],676)
  self.assertEqual(r['status'],'INPUT_MATCH_DESCRIPTIVE_ONLY');self.assertFalse(r['reference_accuracy_verified']);self.assertFalse(r['full_game_gto_verified'])
  for c in r['contexts'].values():self.assertEqual(c['combo_weighted_tv'],0);self.assertEqual(c['max_abs_ev_difference_bb'],0)
 def test_known_distance_and_predeclared_holdout(self):
  a=self.ours['contexts']['rfi']['hands']['AA'];b=self.reference['contexts']['rfi']['hands']['AA']
  a['frequencies']=[1.,0.,0.];b['frequencies']=[0.,1.,0.];a['ev_bb']=a['action_ev_bb'][0];b['ev_bb']=a['ev_bb']+2;b['action_ev_bb'][1]=b['ev_bb']
  r=compare(self.ours,self.reference);c=r['contexts']['rfi']
  self.assertEqual(c['hands']['AA']['total_variation'],1)
  self.assertAlmostEqual(c['combo_weighted_tv'],6/1326)
  self.assertEqual(c['hands']['AA']['ev_difference_bb'],-2)
  self.assertEqual(set(c['partition_tv']),{'audit_holdout','calibration'})
 def test_rake_stack_unknown_tree_and_nested_bool_never_exact(self):
  for key,value in [('equilibrium_concept','QRE'),('rake_rate',.04),('stacks_bb',[100.,100.]),('preflop_tree_sha256',None),('antes_bb',[False,False])]:
   ref=copy.deepcopy(self.reference);ref['condition'][key]=value;r=compare(self.ours,ref)
   self.assertEqual(r['status'],'REFERENCE_ONLY_CONDITION_MISMATCH');self.assertEqual(r['condition_differences'][0]['field'],key)
 def test_missing_ev_and_partial_coverage_are_not_zero(self):
  for c in self.reference['contexts'].values():
   c['hands'].pop('AA')
   for row in c['hands'].values():row.pop('ev_bb');row.pop('action_ev_bb')
  r=compare(self.ours,self.reference);self.assertEqual(r['frequency_rows'],672);self.assertEqual(r['ev_rows'],0)
  self.assertTrue(all(c['max_abs_ev_difference_bb'] is None for c in r['contexts'].values()))
 def test_incompatible_action_or_history_not_aligned(self):
  self.reference['contexts']['rfi']['actions'][2]='raise_to_6'
  self.reference['contexts']['vs_open']['history']=['raise_to_6']
  r=compare(self.ours,self.reference);self.assertEqual(r['frequency_rows'],338)
 def test_bad_frequencies_cost_basis_and_provenance_rejected(self):
  for field,value in [('ev_basis','incremental_from_node'),('source',{}),('schema','unknown')]:
   r=copy.deepcopy(self.reference);r[field]=value
   with self.assertRaises(ValueError):compare(self.ours,r)
  for values in ([.5,.5,.5],[float('nan'),0,1],[-.1,.1,1]):
   r=copy.deepcopy(self.reference);r['contexts']['rfi']['hands']['AA']['frequencies']=values
   with self.assertRaises(ValueError):compare(self.ours,r)
 def test_missing_reference_and_candidate_mismatch_fail_closed(self):
  self.assertIsNone(missing_report()['reference_difference']);self.assertEqual(missing_report()['frequency_rows'],0)
  self.ours['condition']['players']=6
  with self.assertRaises(ValueError):compare(self.ours,self.reference)
 def test_additional_exact_targets_depend_only_on_frozen_policy(self):
  _,p=unpack(json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text()))
  self.assertEqual(refinement_targets(p),('AA','KK','AKo','AKs','QQ','TT'))

if __name__=='__main__':unittest.main()
