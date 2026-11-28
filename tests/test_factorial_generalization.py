import copy,itertools,json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import factorial_game as fg, factorial_study as fs,continuation_game as base
from gto.abstract.factorial_transfer import Transfer,category
from gto.abstract.continuation_learning import FrozenContinuation


def toy():
 # Nature chooses OWN hero signal with probabilities .9,.1; one villain type.
 a=[[[[.9*(1 if x==0 else -1) for y in range(4)] for x in range(4)]],[[[.1*(-1 if x==0 else 1) for y in range(4)] for x in range(4)]]]
 return {'hkeys':[(0,0),(0,1)],'vkeys':[(1,0)],'tensor':a,'chance_mass':[.9,.1]}

class Factorial(unittest.TestCase):
 def test_new_suit_orbits_and_structure_balance(self):
  p=json.loads(fs.PROTOCOL.read_text())
  def canon(b):return min(tuple(sorted((c//4)*4+q[c%4] for c in b)) for q in itertools.permutations(range(4)))
  used={canon(b) for b in p['excluded_previous_flops']};self.assertEqual(len(used),72)
  for split,n in [('train',21),('validation',7),('final_test',7)]:
   self.assertEqual(len(p['split'][split]),n)
   cats={}
   for row in p['split'][split]:
    c=canon(row['cards']);self.assertNotIn(c,used);used.add(c);self.assertEqual(category(row['cards']),row['category']);cats[row['category']]=cats.get(row['category'],0)+1
   self.assertEqual(len(cats),7);self.assertEqual(set(cats.values()),{3 if split=='train' else 1})
 def test_projection_is_chance_weighted_not_latent_count(self):
  g=toy();p=FrozenContinuation({(0,0):(1,0,0,0),(0,1):(0,1,0,0),(1,0):(.25,)*4});q=fg.project(g,p,lambda k:k[:1]);self.assertEqual(q.table[(0,)],(.9,.1,0,0));self.assertNotEqual(q.table[(0,)],(.5,.5,0,0))
 def test_reindex_preserves_every_lifted_profile_payoff(self):
  g=toy();c=fg.reindex(g,lambda k:k[:1]);self.assertEqual(c['chance_mass'],[1.])
  for x in range(4):
   p=FrozenContinuation({k:tuple(float(a==x) for a in range(4)) for k in g['hkeys']+g['vkeys']});q=FrozenContinuation({k:tuple(float(a==x) for a in range(4)) for k in c['hkeys']+c['vkeys']});self.assertAlmostEqual(base.evaluate(g,p)['profile_hero_ev_bb'],base.evaluate(c,q)['profile_hero_ev_bb'])
 def test_mixture_preserves_chance_and_zero_sum_value(self):
  g=toy();c=fg.mix([g,g]);self.assertEqual(g['tensor'],c['tensor']);self.assertEqual(g['chance_mass'],c['chance_mass'])
 def test_shared_selection_ignores_projected_diagnostic(self):
  rows=[]
  for m,u,r in [('a',1.,.8),('b',.9,.95)]:
   for c,x in [('uniform20',u),('range23',r),('projected_uniform20',-100)]:rows.append({'method':m,'cell':c,'summary':{'mean_nashconv_bb':x,'worst_nashconv_bb':x}})
  self.assertEqual(fs.choose(rows,['a','b']),('a',True))
 def test_structure_key_retains_own_and_public_nonrank_information(self):
  k=tuple(range(23));q=fg.structure_key(k);self.assertEqual(q[9:12],(0,0,0));self.assertEqual(q[:9],k[:9]);self.assertEqual(q[12:],k[12:])
 def test_uniform_transfer_cannot_read_range_only_fields(self):
  k=(0,18,41,0,0,0,1,1,1,3,8,13,.4,0,0,0,0,0,2,3,1,1,1)
  records=[{'key':list(k[:20]),'probabilities':[1,0,0,0],'training_flop':[0,5,10],'category':'rainbow'}]
  p=Transfer(records,'global_knn9',False);self.assertEqual(p.probabilities(k,[0,5,10]),p.probabilities((*k[:20],15,3,0),[0,5,10]))
 def test_structure_expert_gates_category(self):
  k=(0,18,41,0,0,0,1,1,1,0,0,0,.4,0,0,0,0,0,2,3)
  records=[{'key':list(k),'probabilities':[1,0,0,0],'training_flop':[0,0,0],'category':'rainbow'},{'key':list(k),'probabilities':[0,1,0,0],'training_flop':[0,0,0],'category':'monotone'}]
  p=Transfer(records,'structure_expert_knn9',False);self.assertEqual(p.probabilities(k,[0,5,10]),(1,0,0,0));self.assertEqual(p.probabilities(k,[0,4,8]),(0,1,0,0))
 def test_interpolation_mixes_complete_plans_normalized(self):
  k=(0,18,41,0,0,0,1,1,1,3,8,13,.4,0,0,0,0,0,2,3)
  records=[{'key':list(k),'probabilities':[float(a==i) for a in range(4)],'training_flop':b,'category':'rainbow'} for i,b in enumerate(([0,5,10],[0,9,18],[4,13,22]))]
  p=Transfer(records,'board_interpolation3x5',False);out=p.probabilities(k,[0,5,10]);self.assertAlmostEqual(sum(out),1);self.assertAlmostEqual(out[0],1/3);self.assertEqual(out[3],0)
 def test_information_floor_bracket_has_known_positive_value(self):
  # Rich hero always wins own-state payoff1. Coarse hero best payoff .8.
  g=toy();coarse=fg.reindex(g,lambda k:k[:1])
  with tempfile.TemporaryDirectory() as root:
   lib=base.build(Path(root));r=fg.information_floor(lib,g,coarse,1000,17)
  self.assertLessEqual(r['minimum_richer_reference_nashconv_lower_bb'],.2);self.assertGreaterEqual(r['constructive_upper_bb'],.2);self.assertTrue(r['absolute_0_1_impossible_in_reference']);self.assertLess(r['constructive_upper_bb'],.21)
 def test_native_full_chance_matches_existing_range_game(self):
  from gto.abstract import range_game,flop_exact,range_features
  from gto.abstract.generalization_features import uniform_strength
  with tempfile.TemporaryDirectory() as root:
   rank,lib,flib,pi,_=fs.initialize(Path(root));m=flop_exact.matrix(rank,[0,5,10]);book=range_features.books(flib,m,pi,'vs_4bet',uniform_strength(m));g=fg.game(lib,m,pi,'vs_4bet',book);old=range_game.game(lib,m,pi,'vs_4bet',book)
  self.assertEqual(g['tensor'],old['tensor']);self.assertEqual(g['hkeys'],old['hkeys']);self.assertAlmostEqual(sum(g['chance_mass']),1,places=12)
  coarse=fg.reindex(g,lambda k:k[:20]);self.assertAlmostEqual(sum(coarse['chance_mass']),1,places=12)
 def test_error_attribution_sums_to_exact_nashconv(self):
  from gto.abstract.factorial_audit import deviations
  g=toy();p=FrozenContinuation({k:(.25,)*4 for k in g['hkeys']+g['vkeys']});before=copy.deepcopy(p.table);d=deviations(g,p);self.assertAlmostEqual(d['total_deviation_bb'],base.evaluate(g,p)['restricted_nashconv_bb'],places=12);self.assertEqual(before,p.table)
 def test_final_never_fits_or_selects_before_identity_validation(self):
  with patch.object(fs,'initialize',side_effect=AssertionError('fit/evaluate accessed')),patch.object(fs,'choose',side_effect=AssertionError('selection')):
   with self.assertRaises(ValueError):fs.final(Path('/tmp/no'),{}, {},Path('/tmp/no'))
 def test_diagnostics_are_separate_and_need_completed_final(self):
  p=json.loads(fs.PROTOCOL.read_text())
  with patch.object(fs,'validate'),patch.object(Path,'exists',return_value=False),patch.object(fs,'initialize',side_effect=AssertionError('oracle accessed before final')):
   with self.assertRaises(ValueError):fs.diagnose(Path('/tmp/no'),p,{})

if __name__=='__main__':unittest.main()
