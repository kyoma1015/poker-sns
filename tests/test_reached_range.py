import copy,itertools,json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import range_features as r,range_game as rg,range_study as study
from gto.abstract import flop_exact as exact,continuation_game as base
from gto.abstract.generalization_features import uniform_strength
from gto.abstract.flop_conditional import Observation
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.precision_archive import unpack
from gto.hand169 import CLASSES

class ReachedRangeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name);cls.rank=exact.build(root/'rank');cls.lib=base.build(root/'game');cls.flib=r.build(root/'features');cls.m=exact.matrix(cls.rank,(48,21,3));cls.uniform=uniform_strength(cls.m);_,p=unpack(json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text()));cls.pi=p['flop_controller']
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_new_protocol_excludes_all_previous_orbits_and_disjoint_splits(self):
  p=json.loads(study.PROTOCOL.read_text())
  def canon(f):return min(tuple(sorted(c//4*4+perm[c%4] for c in f)) for perm in itertools.permutations(range(4)))
  seen={canon(f) for f in p['excluded_previous_flops']};self.assertEqual(len(seen),36)
  for split,n in (('train',24),('validation',6),('final_test',6)):
   self.assertEqual(len(p['split'][split]),n)
   for row in p['split'][split]:c=canon(row['cards']);self.assertNotIn(c,seen);seen.add(c)
  self.assertFalse(p['equal_board_weights_are_real_chance']);self.assertEqual(len(p['candidates']),12)
 def test_weighted_posterior_matches_independent_card_removal_sum(self):
  weights=[0.]*169
  for c,w in (('AA',.8),('KK',.2),('AKs',.4)):weights[CLASSES.index(c)]=w
  out=r.conditional(self.flib,self.m,weights);n=self.m['n']
  for i in (0,12,300,800):
   a=self.m['pairs'][i];rows=[]
   for j,b in enumerate(self.m['pairs']):
    if not set(a)&set(b):rows.append((weights[self.m['labels'][j]],(self.m['win'][i*n+j]+self.m['tie'][i*n+j]/2)/990,self.m['win'][i*n+j]/990,self.m['tie'][i*n+j]/990))
   z=math.fsum(x[0] for x in rows);v=out[tuple(sorted(a))];self.assertAlmostEqual(v['mass'],z,places=12)
   self.assertAlmostEqual(v['equity'],math.fsum(w*e for w,e,_,_ in rows)/z,places=12);self.assertAlmostEqual(v['win']+v['tie']/2,v['equity'],places=12)
 def test_uniform_limit_scale_cancellation_and_zero_range_are_explicit(self):
  a=r.conditional(self.flib,self.m,[.2]*169);b=r.conditional(self.flib,self.m,[.4]*169);zero=r.conditional(self.flib,self.m,[0.]*169)
  for p in self.m['pairs'][::100]:
   k=tuple(sorted(p));self.assertAlmostEqual(a[k]['equity'],self.uniform[k],places=12);self.assertAlmostEqual(a[k]['equity'],b[k]['equity'],places=12);self.assertAlmostEqual(2*a[k]['mass'],b[k]['mass'],places=12);self.assertIsNone(zero[k]['equity'])
  bad=[.1]*169;bad[0]=float('nan')
  with self.assertRaises(ValueError):r.conditional(self.flib,self.m,bad)
 def test_actual_frozen_history_role_mapping_includes_public_call(self):
  for stage in ('vs_3bet','vs_4bet'):
   before=copy.deepcopy(self.pi);book=r.books(self.flib,self.m,self.pi,stage,self.uniform);reach=frozen_reach(stage,self.pi,after_call=True);k=tuple(sorted(self.m['pairs'][100]));hero=r.conditional(self.flib,self.m,reach['villain_reach']);villain=r.conditional(self.flib,self.m,reach['hero_reach'])
   self.assertEqual(book['by_actor'][reach['hero_actor']][k],hero[k]);self.assertEqual(book['by_actor'][1-reach['hero_actor']][k],villain[k]);self.assertEqual(book['public_history'][-1],'call');self.assertFalse(book['actual_opponent_cards_required']);self.assertEqual(before,self.pi)
 def test_common_union_game_pure_plan_matches_preserved_world_evaluator(self):
  for stage in ('vs_3bet','vs_4bet'):
   book=r.books(self.flib,self.m,self.pi,stage,self.uniform);g=rg.game(self.lib,self.m,self.pi,stage,book);p=base.FrozenContinuation({k:(0.,0.,1.,0.) for k in g['hkeys']+g['vkeys']});self.assertAlmostEqual(base.evaluate(g,p)['profile_hero_ev_bb'],exact.evaluate(self.rank,self.m,self.pi,stage)['aggregate']['new'],places=11)
 def test_signal_only_uses_own_observation_and_public_posterior(self):
  book=r.books(self.flib,self.m,self.pi,'vs_3bet',self.uniform);o=Observation((49,50),self.m['flop'],0,18,41);k=r.signal(o,book);self.assertEqual(len(k),23);self.assertEqual(k,r.signal(o,book));self.assertFalse(hasattr(o,'opponent_holes'));self.assertEqual(k[22],1)
  change=copy.deepcopy(book);change['by_actor'][1][(49,50)]['equity']=.123;self.assertEqual(r.signal(o,change),k) # other seat's hypothetical feature does not enter own decision
 def test_uniform_ablation_ignores_range_fields_while_range_policy_uses_them(self):
  k=(0,18.,41.,0,0,0,*([0]*14),0,0,1);q=(*k[:20],15,3,1);rows=[{'key':list(k),'probabilities':[1.,0,0,0]},{'key':list(q),'probabilities':[0,0,0,1.]}];u={'name':'u','family':'uniform','method':'knn','neighbors':1,'private_weight':8,'board_weight':.5,'range_weight':0};v={**u,'name':'r','family':'range','range_weight':32};geom=r.Neighbors([u,v]);pu=r.RangePolicy(rows,u,geom);pv=r.RangePolicy(rows,v,geom)
  self.assertEqual(pu.probabilities(k),pu.probabilities(q));self.assertNotEqual(pv.probabilities(k),pv.probabilities(q));self.assertAlmostEqual(sum(pv.probabilities(q)),1)
 def test_geometry_cache_never_shares_policy_probabilities_between_seeds(self):
  k=(0,18.,41.,0,0,0,*([0]*14),8,2,1);a=[{'key':list(k),'probabilities':[1.,0,0,0]}];b=[{'key':list(k),'probabilities':[0,1.,0,0]}];cfg={'name':'r','family':'range','method':'kernel','neighbors':32,'bandwidth':.1,'private_weight':8,'board_weight':.5,'range_weight':16};geom=r.Neighbors([cfg]);self.assertNotEqual(r.RangePolicy(a,cfg,geom).probabilities(k),r.RangePolicy(b,cfg,geom).probabilities(k))
 def test_validation_worst_guard_and_ties_do_not_use_final_results(self):
  def c(name,family,mean,worst):return {'config':{'name':name,'family':family},'summary':{'mean_nashconv_bb':mean,'worst_nashconv_bb':worst},'final_score':-999 if name=='ineligible' else 999}
  cs=[c('u','uniform',1,2),c('ineligible','range',.1,3),c('eligible','range',.5,1),c('tie','range',.5,1)];u,v,ok=study.choose(cs);self.assertEqual(v['name'],'eligible');self.assertTrue(ok);u,v,ok=study.choose(cs[:2]);self.assertFalse(ok);self.assertEqual(v['name'],'ineligible')
 def test_lock_rejects_changed_sources_before_any_final_access(self):
  with patch.object(study,'initialize',side_effect=AssertionError('must not initialize')) as init:
   with self.assertRaises(ValueError):study.evaluate_locked(Path(self.tmp.name),{}, {'protocol_sha256':'bad','source_sha256':{}},Path('unused'),('final_test',))
   init.assert_not_called()

 def test_valid_locked_final_and_audit_never_fit_or_choose(self):
  h=(0,18.,41.,0,0,0,*([0]*14),8,2,1);v=(1,18.,41.,0,0,0,*([0]*14),8,2,1);fake={'hkeys':[h],'vkeys':[v],'tensor':[[[[0.]*4 for _ in range(4)]]]};records=[{'key':list(k),'probabilities':[.25]*4} for k in (h,v)];u={'name':'u','family':'uniform','method':'knn','neighbors':3,'private_weight':8,'board_weight':.5,'range_weight':0};c={**u,'name':'r','family':'range','range_weight':8}
  protocol={'split':{x:[{'cards':[48,21,3],'category':'UNIT_ORACLE'}] for x in ('train','validation','final_test')},'learning_initialization_seeds':[17],'final_acceptance':{'mean_reduction_vs_uniform_at_least':.2,'worst_must_not_increase':True,'absolute_max_nashconv_bb':.1}};pp=Path(self.tmp.name)/'fake-protocol.json';pp.write_text(json.dumps(protocol));lock=Path(self.tmp.name)/'fake-lock.json';lock.write_text('{}');selection={'protocol_sha256':study.sha(pp),'source_sha256':study.identities(),'accessed_splits':['train','validation'],'final_test_evaluated':False,'frozen_preflop_policy_digest':'d','selected_range':c,'selected_uniform':u,'models':{study.mk(s,17):{'records':records} for s in ('vs_3bet','vs_4bet')}}
  with patch.object(study,'PROTOCOL',pp),patch.object(study,'initialize',return_value=(None,None,None,None,'d')),patch.object(study.exact,'matrix',return_value={}),patch.object(study,'uniform_strength',return_value={}),patch.object(study.feature,'books',return_value={'public_history':['call'],'audits':[]}),patch.object(study,'game',return_value=fake),patch.object(study.base,'solve',side_effect=AssertionError('evaluation cannot fit')),patch.object(study,'choose',side_effect=AssertionError('evaluation cannot choose')):
   for splits in (('final_test',),('train','validation')):
    r0=study.evaluate_locked(Path(self.tmp.name),protocol,selection,lock,splits);self.assertFalse(r0['model_updated']);self.assertFalse(r0['selection_performed']);self.assertEqual(r0['evaluated_splits'],list(splits))

if __name__=='__main__':unittest.main()
