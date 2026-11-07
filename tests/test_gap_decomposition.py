import copy,ctypes as C,itertools,json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import gap_models as gm,gap_calibration as cal,gap_adapter as adapter,gap_study as study
from gto.abstract import continuation_game as base,flop_exact as exact,value_response as old_response,model
from gto.abstract.continuation_learning import ARMS,payoff,FrozenContinuation
from gto.abstract.generalization_features import uniform_strength
from gto.abstract.model import ints
from gto.hand169 import CLASSES

class GapTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name);cls.lib=gm.build(root/'ref');cls.base=base.build(root/'base');cls.rank=exact.build(root/'rank');cls.response=old_response.build(root/'response')
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def small(self,variant=None):
  m=exact.matrix(self.rank,[8,13,18],holes=[(0,4),(1,5),(2,6),(3,7)]);uniform={tuple(sorted(pair)):math.fsum((m['win'][i*m['n']+j]+m['tie'][i*m['n']+j]/2)/990 for j in range(m['n']) if j!=i)/(m['n']-1) for i,pair in enumerate(m['pairs'])};book={'uniform':uniform,'by_actor':{a:{tuple(sorted(p)):{'equity':uniform[tuple(sorted(p))],'ahead_probability':.5} for p in m['pairs']} for a in (0,1)}};reach={'stage':'vs_3bet','hero_actor':0,'post_call_pot_bb':18,'remaining_stack_bb':41,'hero_reach':[1.]*169,'villain_reach':[1.]*169};v=variant or {'name':'base','arms':4,'bet_fraction':.5,'stack_scale':1,'range':'actual'};g=gm.make_game(self.base,self.lib,m,reach,book,v);p=FrozenContinuation({k:(.1,.2,.3,.4) for k in g['hkeys']+g['vkeys']});return m,reach,book,g,p
 def test_preregistered_suit_orbits_exclude142(self):
  p=json.loads(study.PROTOCOL.read_text())
  def canon(b):return min(tuple(sorted(c//4*4+q[c%4] for c in b)) for q in itertools.permutations(range(4)))
  seen={canon(b) for b in p['excluded_previous_flops']};self.assertEqual(len(seen),142)
  for split,n in [('train',21),('validation',7),('final_test',7)]:
   self.assertEqual(len(p['split'][split]),n)
   for r in p['split'][split]:self.assertNotIn(canon(r['cards']),seen);seen.add(canon(r['cards']))
 def test_independent_ledger_matches_preserved_legal_base_plans(self):
  for actor in (0,1):
   for pot,rem in ((18,41),(42,29)):
    f=gm.forms(self.lib,4,actor,pot,rem,.5)
    for i,a in enumerate(ARMS):
     for j,b in enumerate(ARMS):
      lo,hi=f[i*4+j]
      for e in (0,.2,.5,1):self.assertAlmostEqual(lo+e*(hi-lo),payoff(e,a,b,actor,pot,rem),places=12)
 def test_allin_bet_disables_raise_and_check_fold_is_legal(self):
  f=gm.forms(self.lib,5,0,42,14.5,.75);lo,hi=f[2*5+1];self.assertAlmostEqual(lo,-35.5);self.assertAlmostEqual(hi,35.5);self.assertEqual(f[4*5+1],(-21,-21))
 def test_cash_ledger_zero_sum_for_every_variant(self):
  p=json.loads(study.PROTOCOL.read_text())
  for v in p['sensitivity_variants']:
   A=v['arms'];a=gm.forms(self.lib,A,0,42,29*v['stack_scale'],v['bet_fraction']);b=gm.forms(self.lib,A,1,42,29*v['stack_scale'],v['bet_fraction'])
   for i in range(A):
    for j in range(A):self.assertAlmostEqual(a[i*A+j][0]+b[j*A+i][1],0,places=12);self.assertAlmostEqual(a[i*A+j][1]+b[j*A+i][0],0,places=12)
 def test_independent_rank_full990_counts_match_cache(self):
  m,_,_,_,_=self.small();rows=gm.rank_checks(self.lib,m,17881,2);self.assertFalse(any(r['mismatch'] for r in rows));self.assertTrue(all(sum(r['reference_counts'])==990 for r in rows))
 def test_royal_flush_reference_is_always_winner(self):
  out=(C.c_uint64*3)();status=self.lib.gap_exact_reference(ints([36,32,29,30]),ints([48,44,40]),out);self.assertEqual(status,0);self.assertEqual(tuple(out),(990,0,0))
 def test_reference_rejects_overlapping_cards(self):
  out=(C.c_uint64*3)();self.assertNotEqual(self.lib.gap_exact_reference(ints([0,1,2,3]),ints([0,4,5]),out),0)
 def test_uniform_board_chance_is_exactly_uniform_over22100(self):
  r={'hero_reach':[1.]*169,'villain_reach':[1.]*169,'history':[]};c=gm.board_chance(self.lib,r);self.assertEqual(len(c['probabilities']),22100);self.assertAlmostEqual(c['sum'],1,places=14);self.assertAlmostEqual(c['raw_preflop_reach_mass'],1624350);self.assertLess(max(abs(p-1/22100) for p in c['probabilities']),1e-15);self.assertEqual(gm.direct_mass(self.lib,r,[0,1,2]),1271256)
 def test_card_removal_chance_matches_independent_direct_sum(self):
  h=[0.]*169;v=[0.]*169;h[CLASSES.index('AA')]=1;v[CLASSES.index('KK')]=1;r={'hero_reach':h,'villain_reach':v,'history':['test']};c=gm.board_chance(self.lib,r);ps={tuple(b):x for b,x in zip(c['flops'],c['probabilities'])};self.assertAlmostEqual(c['raw_preflop_reach_mass'],36);self.assertAlmostEqual(ps[(48,49,50)],0,places=15)
  for flop in ([0,5,10],[44,48,49]):self.assertAlmostEqual(ps[tuple(flop)]*36*17296,gm.direct_mass(self.lib,r,flop),places=10)
 def test_concrete_pair_reference_matches_type_ev_and_br(self):
  m,r,b,g,p=self.small();ref=gm.reference(self.lib,m,g,p);targets=old_response.conditional_targets(g,p);metrics=gm.evaluate(g,p)
  for k,t in ref['targets'].items():
   self.assertAlmostEqual(t['mass'],targets[k]['own_marginal_mass'],places=12)
   for x,y in zip(t['ev'],targets[k]['conditional_arm_ev_bb']):self.assertAlmostEqual(x,y,places=12)
  for k,v in ref['metrics'].items():self.assertAlmostEqual(v,metrics[k],places=12)
 def test_generic4_response_matches_preserved_kernel(self):
  _,_,_,g,p=self.small();a,ma=gm.solve(self.lib,g,p,128);b,mb=old_response.respond(self.response,g,p,128)
  for k,v in a.table.items():
   for x,y in zip(v,b.table[k]):self.assertAlmostEqual(x,y,places=12)
  self.assertAlmostEqual(ma['restricted_nashconv_bb'],mb['restricted_nashconv_bb'],places=12)
 def test_expanded_action_can_expose_gap_despite_base_equilibrium(self):
  a=[[float(i==4) for j in range(5)] for i in range(5)];g={'actions':5,'hkeys':[(0,)],'vkeys':[(1,)],'tensor':[[a]],'chance_mass':[1.]};p=FrozenContinuation({(0,):(.25,.25,.25,.25,0),(1,):(.25,.25,.25,.25,0)});self.assertEqual(gm.evaluate(g,p)['restricted_nashconv_bb'],1);q,m=gm.solve(self.lib,g,p,512);self.assertLess(m['restricted_nashconv_bb'],.01)
 def test_spr_rename_retains_private_partition_and_prior(self):
  m,r,b,g,p=self.small();v={'name':'half','arms':5,'bet_fraction':.5,'stack_scale':.5,'range':'actual'};other=gm.make_game(self.base,self.lib,m,r,b,v);lifted=gm.lift(p,other);self.assertEqual(len(g['hkeys']),len(other['hkeys']))
  for k,v in lifted.table.items():self.assertEqual(k[2],20.5);self.assertEqual(v,(.1,.2,.3,.4,0))
 def test_calibration_learns_only_public_seat_arm_affine(self):
  rows=[]
  for x in (0.,1.,2.):
   k=(0,18,41);rows.append({'stage':'vs_3bet','reference':{'targets':{k:{'mass':1.,'ev':[2*(x+a)+3 for a in range(4)]}}},'predictions':{k:[x+a for a in range(4)]}})
  coeff=cal.fit(rows);pred=cal.predict([3,4,5,6],(0,18,41),'vs_3bet','affine',coeff);self.assertEqual(pred,(9,11,13,15))
 def test_validation_selector_rejects_strategy_loss_regression(self):
  def summary(mae,loss):return {'overall':{'mean_action_mae_bb':mae,'maximum_action_error_bb':10},'by_stage':{s:{'mean_action_mae_bb':mae,'mean_one_sided_greedy_regret_loss_bb':loss} for s in ('vs_3bet','vs_4bet')}}
  c=[{'method':'raw','summary':summary(2,1)},{'method':'bias','summary':summary(1.5,.9)},{'method':'affine','summary':summary(1,1.1)}];self.assertEqual(cal.choose(c),'bias')
 def test_readonly_class_leaf_matches_preserved_kernel(self):
  m,r,b,g,p=self.small();before=copy.deepcopy(p.table);reference=gm.reference(self.lib,m,g,p);error=adapter.leaf_check(self.base,self.lib,m,g,p,reference);self.assertLess(error,1e-12);self.assertEqual(before,p.table)
 def test_readonly_root_attribution_one_known_physical_flop(self):
  from gto.abstract.range_study import initialize
  from gto.abstract.frozen_flop_reach import frozen_reach
  from gto.abstract import range_features
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);_,_,flib,pi,_=initialize(root/'old');reach=frozen_reach('vs_4bet',pi,after_call=True);m=exact.matrix(self.rank,[8,13,18]);book=range_features.books(flib,m,pi,'vs_4bet',uniform_strength(m));variant={'name':'base','arms':4,'bet_fraction':.5,'stack_scale':1,'range':'actual'};g=gm.make_game(self.base,self.lib,m,reach,book,variant);p=FrozenContinuation({k:(.25,)*4 for k in g['hkeys']+g['vkeys']});reference=gm.reference(self.lib,m,g,p);full,_=model.chance(model.classes());accum=[0.]*(169*169);adapter.add_partial(accum,reference,full);prob=gm.direct_mass(self.lib,reach,m['flop'])/(reach['conditional_mass']*1624350*17296);lib=model.load(model.build(root/'root'));before=list(pi);result=adapter.root_attribution(lib,pi,reach,accum,prob*reference['metrics']['profile_hero_ev_bb']);self.assertLess(result['absolute_error_bb'],1e-10);self.assertEqual(pi,before);self.assertTrue(result['not_full_game_ev'])
 def test_final_identity_guard_precedes_evaluation_or_selection(self):
  with patch.object(study,'setup',side_effect=AssertionError('evaluated')),patch.object(cal,'choose',side_effect=AssertionError('selected')):
   with self.assertRaises(ValueError):study.final(Path('/tmp/no'),{}, {},Path('/tmp/no'))

if __name__=='__main__':unittest.main()
