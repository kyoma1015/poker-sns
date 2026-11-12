import copy,itertools,json,math,tempfile,unittest
from pathlib import Path
from gto.abstract import call_reach as cr,call_study as cs,street_tree as st,gap_models as gm,model,street_study as previous
from gto.abstract.range_study import initialize

class CallTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.env=cs.setup(Path(cls.tmp.name));cls.pi=cls.env[3];cls.p=json.loads(cs.P.read_text());cls.r={s:cr.extract(cls.pi,h,s) for s,h in cls.p['prefixes'].items()}
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_exact_public_prefixes_match_independent_manual_products(self):
  expected={'open_call':(18,1,5.,47.5,.2744880273807224,[(0,2,0),(16,1,1)]),'limp_check':(3,1,2.,49.,.17031083012224532,[(0,1,0),(2,0,1)]),'limp_raise_call':(6,0,5.,47.5,.10745708202408938,[(0,1,0),(2,1,1),(4,1,0)])};_,chance=model.chance(model.classes())
  for s,(leaf,actor,pot,remaining,mass,steps) in expected.items():
   r=self.r[s];self.assertEqual((r['leaf_index'],r['hero_actor'],r['post_call_pot_bb'],r['remaining_stack_bb']),(leaf,actor,pot,remaining));self.assertAlmostEqual(r['spr'],remaining/pot);self.assertAlmostEqual(r['conditional_mass'],mass,places=14);seat=[[1.]*169,[1.]*169]
   for node,action,a in steps:seat[a]=[seat[a][h]*self.pi[(node*3+action)*169+h] for h in range(169)]
   self.assertEqual(seat,r['seat_reach']);independent=sum(chance[i*169+j]*seat[0][i]*seat[1][j] for i in range(169) for j in range(169));self.assertAlmostEqual(independent,mass,places=13)
 def test_invalid_history_and_nonmatched_terminal_rejected(self):
  for history in ([],['fold'],['raise_to_100'],['call','fold'],['call','check','call']):
   with self.assertRaises(ValueError):cr.extract(self.pi,history,'invalid')
 def test_policy_readonly_and_leaf_mass_conservation(self):
  before=list(self.pi);rows=cr.leaf_ledger(self.pi);self.assertEqual(before,self.pi);self.assertAlmostEqual(sum(x['probability'] for x in rows),1,places=13);self.assertEqual(len({x['leaf'] for x in rows}),len(rows));self.assertAlmostEqual(sum(r['conditional_mass'] for r in self.r.values()),.5522559395270571,places=14)
 def test_limp_pot_minimum_bet_dedup_and_legal_raise(self):
  r=self.r['limp_check'];t=st.tree(r['post_call_pot_bb'],r['remaining_stack_bb'],r['hero_actor'],self.p['bet_fractions']);self.assertEqual(t['bet_amounts'],[1.,1.5]);self.assertEqual(t['nodes'][0]['seat'],1)
  for n in t['nodes']:
   for a in n['actions']:
    if a['kind']=='bet':self.assertGreaterEqual(a['amount'],1)
    if a['kind']=='raise':self.assertAlmostEqual(a['amount'],min(3*n['bet'],r['remaining_stack_bb']))
 def test_true_board_chance_and_independent_card_removal_mass(self):
  for s,r in self.r.items():
   c=gm.board_chance(self.env[5],r);self.assertEqual(len(c['flops']),22100);self.assertAlmostEqual(sum(c['probabilities']),1,places=12);self.assertAlmostEqual(c['raw_preflop_reach_mass']/1624350,r['conditional_mass'],places=13);lookup={tuple(b):v for b,v in zip(c['flops'],c['probabilities'])}
   for b in ([0,1,2],[8,13,18]):self.assertAlmostEqual(lookup[tuple(b)]*c['raw_preflop_reach_mass']*17296,gm.direct_mass(self.env[5],r,b),places=7)
 def test_generic_features_and_conditional_game_are_own_information_only(self):
  # Small known fixture, not a fresh unseen board or reported GTO range.
  from gto.abstract import flop_exact as exact
  m=exact.matrix(self.env[0],[8,13,18]);r=self.r['open_call'];book=cr.book(self.env[2],m,r);self.assertFalse(book['actual_opponent_cards_required']);other={**r,'hero_reach':[v*.5 for v in r['hero_reach']]};b=cr.book(self.env[2],m,other);self.assertEqual(book['by_actor'][r['hero_actor']],b['by_actor'][r['hero_actor']]);g=cs.prepared(self.env,m,r,self.p);self.assertAlmostEqual(sum(g['mass']),1,places=12);policy,metrics=st.trajectory(self.env[-1],g,st.uniform(g),[32])[0];self.assertFalse(metrics['full_game_gto_verified'])
 def test_preregistered_cohort_excludes410_and_suit_isomorphisms(self):
  canon=lambda b:min(tuple(sorted(c//4*4+q[c%4] for c in b)) for q in itertools.permutations(range(4)));seen={tuple(b) for b in self.p['excluded_previous_orbits']};self.assertEqual(len(seen),410)
  for split in ('train','validation','final_test'):
   self.assertEqual(len(self.p['split'][split]),7)
   for row in self.p['split'][split]:b=canon(row['cards']);self.assertNotIn(b,seen);seen.add(b)
 def test_priority_uses_root_weighted_width_and_fixed_tie_break(self):
  rows=[(2.,'z',[0,1,2],.2),(3.,'a',[0,1,3],.1),(3.,'b',[0,1,2],.9)];self.assertEqual(cs.select_priority(rows,2),[rows[1],rows[2]])
 def test_allocation_and_profile_radius_scaling(self):
  weights={'a':.9,'b':.1};counts=cs.allocation(weights,128);self.assertEqual(sum(counts.values()),128);self.assertTrue(all(x>=1 for x in counts.values()));row={'flop':[0,1,2],'board_probability':.01,'profile_hero_ev_bb':2.,'game_value_lower_bb':-.1,'game_value_upper_bb':.1};x=cs.profile_interval({'a':[row]},{'a':1},5,13.75,.01/12);self.assertAlmostEqual(x['profile_ev_estimate_bb'],2.);self.assertAlmostEqual(x['profile_sampling_radius_bb'],27.5*math.sqrt(math.log(1200)/2));self.assertEqual(x['registered_game_profile_absolute_bound_bb'],13.75)
 def test_deterministic_bound_uses_unique_probability_not_draw_multiplicity(self):
  row={'flop':[0,1,2],'board_probability':.01,'profile_hero_ev_bb':2};d=cs.deterministic([row,row]);self.assertEqual(d['unique_physical_boards'],1);self.assertAlmostEqual(d['known_profile_ev_contribution_bb'],.02);self.assertAlmostEqual(d['conservative50_profile_interval_bb'][1]-d['conservative50_profile_interval_bb'][0],99+2e-7)
 def test_root_signs_and_unknown_mass_match_independent_ledger(self):
  d={'ranges':self.r};fake={s:{'deterministic':{'conservative50_profile_interval_bb':[1.,2.],'evaluated_board_probability':.1},'sample_interval':{'uniform512_profile_ev_interval_bb':[1.,2.]}} for s in self.r};before=list(self.pi);out=cs.root_accounting(self.pi,fake,self.p,d);self.assertEqual(before,self.pi);self.assertAlmostEqual(out['other_call_probability_unknown'],.0102772112603418,places=12)
  for s,r in self.r.items():
   a,b=out['prefix_details'][s]['root_statistical_sb_contribution_interval_bb'];mass=r['conditional_mass'];self.assertEqual([a,b],[-2*mass,-mass] if r['hero_actor']==1 else [mass,2*mass])
 def test_cohort_precedes_population_and_source_lock_precedes_evaluation(self):
  from unittest.mock import patch
  with patch.object(cs,'setup',side_effect=AssertionError('evaluated')):
   with tempfile.TemporaryDirectory() as d,patch.object(cs,'ROOT',Path(d)):
    with self.assertRaises(ValueError):cs.population(Path(d),Path(d),self.p,{})

class AuditToleranceTests(unittest.TestCase):
 def test_only_raw_deal_roundoff_gets_native_guard_not_ev_or_identity(self):
  from gto.abstract.call_verify import verify
  a={'maximum_board_chance_mass_error':2e-10,'ev_bb':.1,'source':'fixed'};b={**a,'maximum_board_chance_mass_error':3e-10};verify(a,b)
  for other in ({**b,'maximum_board_chance_mass_error':1e-5},{**b,'ev_bb':.100001},{**b,'source':'changed'}):
   with self.assertRaises(ValueError):verify(a,other)
  self.assertIn('maximum_board_chance_mass_error',a)

if __name__=='__main__':unittest.main()
