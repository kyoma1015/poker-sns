import ctypes as C,json,math,tempfile,unittest
from pathlib import Path
from gto.abstract import continuation_audit as a,street_tree as st
from gto.abstract.continuation_audit_br import independent
class ContinuationAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.lib=a.build(Path(cls.tmp.name)/'new');cls.legacy=st.build(Path(cls.tmp.name)/'old');cls.r={'post_call_pot_bb':18.,'remaining_stack_bb':41.}
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def pi(self,g):return [1/len(n['actions']) for n in g['tree']['nodes'] if n['actor']>=0 for t in range(g['h'] if n['actor']==0 else g['v']) for x in n['actions']]
 def test_reused_base_algorithm_matches_legacy_and_independent_evaluator(self):
  for owner in (0,1):
   g=a.game(self.r,[1/3,.5,.75],owner);pi=self.pi(g);m=[1/64]*64;e=[((i*17)%61)/61/64 for i in range(64)];new=a.evaluate(self.lib,g,pi,m,e);old=st.evaluate(self.legacy,{**g,'mass':m,'equity':e},pi);reference=independent(g,pi,m,e)
   for k,v in reference.items():self.assertAlmostEqual(new[k],v,places=11);self.assertAlmostEqual(new[k],old[k],places=11)
 def test_own_private_refinement_preserves_profile_but_changes_available_BR(self):
  base=a.game(self.r,[.5],0);rich=a.game(self.r,[.5],0,h=16);pi=self.pi(base);expanded=a.expand(rich,pi);m=[1/128]*128;e=[(.05 if i<8 else .95)/128 for i in range(16) for j in range(8)];coarse=a.evaluate(self.lib,base,pi,[1/64]*64,[.5/64]*64);fine=a.evaluate(self.lib,rich,expanded,m,e)
  self.assertAlmostEqual(coarse['profile_hero_ev_bb'],fine['profile_hero_ev_bb'],places=12);self.assertGreater(fine['hero_br_ev_bb'],coarse['hero_br_ev_bb'])
 def test_expanded_sizes_and_two_raises_are_legal_and_capped(self):
  p=json.loads(a.P.read_text())
  for pot,rem in ((18,41),(42,29)):
   g=a.game({'post_call_pot_bb':pot,'remaining_stack_bb':rem},p['union_fractions'],0,expanded=True);self.assertGreater(len(g['tree']['bet_amounts']),3);self.assertIn(rem,g['tree']['bet_amounts'])
   for node in g['tree']['nodes']:
    self.assertLessEqual(len(node['actions']),12)
    for action in node['actions']:self.assertLessEqual(action.get('amount',0),rem)
    if node['actor']<0:self.assertLessEqual(node['c1'],100)
   m=[1/64]*64;e=[.4/64]*64;pi=self.pi(g);x=a.evaluate(self.lib,g,pi,m,e);ref=independent(g,pi,m,e)
   for k,v in ref.items():self.assertAlmostEqual(x[k],v,places=10)
 def test_future_envelope_does_not_treat_unplayed_turnriver_as_known(self):
  g=a.game(self.r,[.5],0);pi=self.pi(g);env=a.future_envelope(g,pi,[1/64]*64,[.4/64]*64);value=a.evaluate(self.lib,g,pi,[1/64]*64,[.4/64]*64)['profile_hero_ev_bb'];self.assertGreater(env['unresolved_showdown_probability'],0);self.assertLessEqual(env['root_lower'],value);self.assertGreaterEqual(env['root_upper'],value)
 def test_BR_does_not_choose_actions_using_actual_opponent_private_type(self):
  g={'h':1,'v':2,'offsets':[0,2,2,2],'tree':{'nodes':[{'actor':0,'actions':[0,1],'children':[1,2],'c0':0,'c1':0},{'actor':-1,'actions':[],'children':[],'c0':-1,'c1':2},{'actor':-1,'actions':[],'children':[],'c0':1,'c1':-2}]}}
  for x in (a.evaluate(self.lib,g,[.5,.5],[.5,.5],[.5,0]),independent(g,[.5,.5],[.5,.5],[.5,0])):self.assertAlmostEqual(x['hero_br_ev_bb'],0.,places=12)
 def test_public_information_can_be_revealed_without_hole_card_oracle(self):
  import inspect
  code=inspect.getsource(a.expand);self.assertIn('t%8',code);self.assertNotIn('opponent_cards',code)
  p=json.loads(a.P.read_text());self.assertFalse(p['normal_GTO_registration']);self.assertEqual(p['formal_acceptance'],0);self.assertIn('actualflop_own169class_and3flags',p['information_levels'])
 def test_design_retains_original_population_and_real_frozen_preflop_reach(self):
  d=a.design();self.assertEqual(len(d['orbits']),1755);self.assertEqual(sum(x['multiplicity'] for x in d['orbits']),22100);self.assertEqual(len(d['configs']),4)
  for r in d['configs'].values():self.assertGreater(r['conditional_mass'],0);self.assertEqual(r['history'][-1],'call');self.assertEqual(len(r['seat_reach'][0]),169)

if __name__=='__main__':unittest.main()
