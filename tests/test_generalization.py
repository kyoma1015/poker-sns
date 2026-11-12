import itertools,json,math,tempfile,unittest,copy
from pathlib import Path
from unittest.mock import patch
from gto.abstract import generalization_features as f
from gto.abstract import generalization_game as gg
from gto.abstract import generalization_study as s
from gto.abstract import continuation_game as base,flop_exact as exact
from gto.abstract.flop_conditional import Observation
from gto.abstract.continuation_learning import FrozenContinuation
from gto.abstract.precision_archive import unpack

class GeneralizationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name);cls.rank=exact.build(root/'rank');cls.lib=base.build(root/'game');cls.m=exact.matrix(cls.rank,(48,21,3));cls.strength=f.uniform_strength(cls.m);_,p=unpack(json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text()));cls.pi=p['flop_controller']
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_preregistered_splits_have_no_suit_orbit_or_previous_overlap(self):
  p=json.loads(s.PROTOCOL.read_text())
  def canon(flop):return min(tuple(sorted(c//4*4+perm[c%4] for c in flop)) for perm in itertools.permutations(range(4)))
  seen={canon(f) for f in p['excluded_previous_flops']}
  for name,n in (('train',18),('validation',6),('final_test',6)):
   self.assertEqual(len(p['split'][name]),n)
   for row in p['split'][name]:
    k=canon(row['cards']);self.assertNotIn(k,seen);seen.add(k)
  self.assertFalse(p['equal_board_weights_are_real_chance'])
 def test_uniform_strength_is_unknown_opponent_average_not_actual_private_pair(self):
  self.assertAlmostEqual(math.fsum(self.strength.values())/1176,.5,places=12)
  self.assertGreater(self.strength[(49,50)],self.strength[(32,36)])
  obs=Observation((49,50),(48,21,3),0,18,41);a=f.signal(obs,self.strength);self.assertEqual(len(a),20);self.assertEqual(a,f.signal(obs,self.strength));self.assertFalse(hasattr(obs,'opponent_holes'))
 def test_features_are_invariant_to_suit_renaming(self):
  obs=Observation((49,50),(48,21,3),0,18,41);expected=f.signal(obs,self.strength);e=self.strength[(49,50)]
  for perm in itertools.permutations(range(4)):
   cv=lambda cards:tuple(c//4*4+perm[c%4] for c in cards);h=cv(obs.holes);o=Observation(h,cv(obs.flop),0,18,41);self.assertEqual(f.signal(o,{tuple(sorted(h)):e}),expected)
 def test_exact_rich_game_matches_same_pure_plan_payoff_as_previous_game(self):
  for stage in ('vs_3bet','vs_4bet'):
   g=gg.game(self.lib,self.m,self.pi,stage,self.strength);p=FrozenContinuation({k:(0.,0.,1.,0.) for k in g['hkeys']+g['vkeys']});actual=base.evaluate(g,p)['profile_hero_ev_bb'];expected=exact.evaluate(self.rank,self.m,self.pi,stage)['aggregate']['new'];self.assertAlmostEqual(actual,expected,places=11)
 def test_same_rich_information_game_for_coarse_and_feature_policies(self):
  g=gg.game(self.lib,self.m,self.pi,'vs_3bet',self.strength);coarse=FrozenContinuation({k[:6]:(1.,0.,0.,0.) for k in g['hkeys']+g['vkeys']});p=f.TransferPolicy([],{'kind':'coarse'},coarse).materialize(g)
  self.assertEqual(set(p.table),set(g['hkeys']+g['vkeys']));self.assertTrue(all(v==(1.,0.,0.,0.) for v in p.table.values()));before=copy.deepcopy(p.table);base.evaluate(g,p);self.assertEqual(p.table,before)
 def test_nearest_mixture_is_normalized_role_separated_and_not_hidden_conditioned(self):
  k=f.signal(Observation((49,50),(48,21,3),0,18,41),self.strength);other=(1,*k[1:]);records=[{'key':list(k),'probabilities':[1.,0,0,0]},{'key':list(other),'probabilities':[0,0,0,1]}];cfg={'kind':'knn','neighbors':3,'private_weight':4,'board_weight':1};p=f.TransferPolicy(records,cfg)
  self.assertEqual(p.probabilities(k),(1.,0,0,0));self.assertEqual(p.probabilities(other),(0,0,0,1.));self.assertEqual(f.distance_parts(k,k),(0.,0.));self.assertEqual(f.distance_parts(k,other),(math.inf,math.inf))
 def test_selection_uses_validation_only_and_stable_ties(self):
  candidates=[{'config':{'name':'first'},'summary':{'mean_nashconv_bb':1.},'final_score':0},{'config':{'name':'second'},'summary':{'mean_nashconv_bb':.5},'final_score':999}];self.assertEqual(s.choose_candidate(candidates)['name'],'second');candidates[0]['summary']['mean_nashconv_bb']=.5;self.assertEqual(s.choose_candidate(candidates)['name'],'first')
 def test_changed_source_or_protocol_blocks_final_before_any_data_access(self):
  with patch.object(s,'initialize',side_effect=AssertionError('must not build')) as init:
   with self.assertRaises(ValueError):s.final_test(Path(self.tmp.name),{}, {'protocol_sha256':'tampered','source_sha256':{}},Path('unused'))
   init.assert_not_called()
 def test_final_phase_cannot_train_or_reselect(self):
  h=(0,18.,41.,0,0,0,*([0]*14));v=(1,18.,41.,0,0,0,*([0]*14));g={'hkeys':[h],'vkeys':[v],'tensor':[[[[0.]*4 for _ in range(4)]]]};rows=[{'key':list(k[:6]),'probabilities':[.25]*4} for k in (h,v)];model={'coarse':rows,'legacy':rows,'records':[]};selection={'protocol_sha256':s.sha(s.PROTOCOL),'source_sha256':s.identities(),'final_test_evaluated':False,'accessed_board_splits':['train','validation'],'frozen_preflop_policy_digest':'d','selected_config':{'kind':'coarse'},'models':{s.model_key(t,17):model for t in ('vs_3bet','vs_4bet')}};protocol={'split':{'final_test':[{'cards':[48,21,3],'category':'unit_oracle'}]},'learning_initialization_seeds':[17],'final_acceptance':{'mean_reduction_vs_retrained_coarse_at_least':.2,'worst_nashconv_must_not_increase':True,'absolute_max_nashconv_bb':.1}}
  lock=Path(self.tmp.name)/'unit-lock.json';lock.write_text('{}')
  with patch.object(s,'initialize',return_value=(None,None,None,'d')),patch.object(s.exact,'matrix',return_value={}),patch.object(s,'uniform_strength',return_value={}),patch.object(s,'game',return_value=g),patch.object(s.base,'solve',side_effect=AssertionError('final must not train')),patch.object(s,'choose_candidate',side_effect=AssertionError('final must not choose')):
   r=s.final_test(Path(self.tmp.name),protocol,selection,lock)
  self.assertFalse(r['final_test_used_for_selection']);self.assertEqual(r['selection_file_sha256'],s.sha(lock))

 def test_post_lock_training_audit_cannot_fit_choose_or_access_final(self):
  from gto.abstract import generalization_audit as audit
  h=(0,18.,41.,0,0,0,*([0]*14));v=(1,18.,41.,0,0,0,*([0]*14));fake={'hkeys':[h],'vkeys':[v],'tensor':[[[[0.]*4 for _ in range(4)]]]};rows=[{'key':list(k[:6]),'probabilities':[.25]*4} for k in (h,v)];model={'coarse':rows,'records':[]}
  protocol={'split':{x:[{'cards':[48,21,3]}] for x in ('train','validation')},'learning_initialization_seeds':[17]};path=Path(self.tmp.name)/'audit-protocol.json';path.write_text(json.dumps(protocol));lock=Path(self.tmp.name)/'audit-lock.json';lock.write_text('{}')
  selection={'protocol_sha256':s.sha(path),'source_sha256':s.identities(),'selected_config':{'kind':'coarse'},'models':{s.model_key(t,17):model for t in ('vs_3bet','vs_4bet')}}
  with patch.object(audit.study,'PROTOCOL',path),patch.object(audit.study,'initialize',return_value=(None,None,None,'d')),patch.object(audit.exact,'matrix',return_value={}),patch.object(audit,'uniform_strength',return_value={}),patch.object(audit,'game',return_value=fake),patch.object(audit.base,'solve',side_effect=AssertionError('audit must not train')),patch.object(audit.study,'choose_candidate',side_effect=AssertionError('audit must not select')):
   r=audit.audit(Path(self.tmp.name),selection,lock)
  self.assertFalse(r['policy_updated']);self.assertFalse(r['selection_performed']);self.assertFalse(r['final_boards_accessed'])

if __name__=='__main__':unittest.main()
