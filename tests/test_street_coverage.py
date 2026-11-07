import copy,itertools,json,math,tempfile,unittest
from pathlib import Path
from gto.abstract import street_tree as st,chance_coverage as cov,street_study as study,gap_models as gm
from gto.abstract.continuation_learning import FrozenContinuation

class StreetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.lib=st.build(Path(cls.tmp.name)/'street');cls.ref=gm.build(Path(cls.tmp.name)/'ref')
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def small(self,actor=0,fractions=(.5,),pot=18,rem=41):
  t=st.tree(pot,rem,actor,fractions);offsets=[0]
  for n in t['nodes']:offsets.append(offsets[-1]+(0 if n['actor']<0 else 2*len(n['actions'])))
  return {'tree':t,'h':2,'v':2,'offsets':offsets,'mass':[.4,.1,.1,.4],'equity':[.2,.08,.02,.2],'game':{'hkeys':['h0','h1'],'vkeys':['v0','v1']}}
 def metric(self,p,policy):return st.evaluate(self.lib,p,policy)
 def test_preregistered_orbits_and_population_not_unseen(self):
  p=json.loads(study.PROTOCOL.read_text());canon=lambda b:min(tuple(sorted(c//4*4+q[c%4] for c in b)) for q in itertools.permutations(range(4)));seen={canon(b) for b in p['excluded_previous_flops']};self.assertEqual(len(seen),177)
  for split,n in [('train',14),('validation',7),('final_test',7)]:
   self.assertEqual(len(p['split'][split]),n)
   for r in p['split'][split]:self.assertNotIn(canon(r['cards']),seen);seen.add(canon(r['cards']))
  for stage,config in p['population']['allocations'].items():
   self.assertEqual(len(config['stratum_probability']),8);previous={}
   for cp in config['checkpoints']:
    self.assertEqual(sum(cp['by_stratum'].values()),cp['total_draws'])
    for k,n in cp['by_stratum'].items():self.assertGreaterEqual(n,previous.get(k,0));self.assertGreaterEqual(len(p['population']['draws'][stage][k]),n)
    previous=cp['by_stratum']
 def test_legal_caps_no_raise_after_allin(self):
  p=self.small(fractions=(1/3,.5,.75),pot=42,rem=14.5)
  for n in p['tree']['nodes']:
   self.assertTrue(all(a.get('amount',0)<=14.5 for a in n['actions']))
   if n['kind']=='face_bet' and n['bet']==14.5:self.assertEqual([a['kind'] for a in n['actions']],['fold','call'])
   if n['kind']=='face_raise':self.assertEqual([a['kind'] for a in n['actions']],['fold','call'])
  with self.assertRaises(ValueError):st.tree(18,41,0,[])
 def test_legacy_mixture_preserves_independent_cash_ledger(self):
  for actor in (0,1):
   p=self.small(actor);policy=FrozenContinuation({k:(.1,.2,.3,.15,.25) for k in ['h0','h1','v0','v1']});actual=self.metric(p,st.lift_legacy(policy,p));forms=gm.forms(self.ref,5,actor,18,41,.5);weights=(.1,.2,.3,.15,.25);expected=sum(weights[a]*weights[b]*sum(p['mass'][k]*forms[a*5+b][0]+p['equity'][k]*(forms[a*5+b][1]-forms[a*5+b][0]) for k in range(4)) for a in range(5) for b in range(5));self.assertAlmostEqual(actual['profile_hero_ev_bb'],expected,places=12)
 def test_br_matches_exhaustive16_private_plans(self):
  p=self.small();prior=st.uniform(p);actual=self.metric(p,prior);plans=list(itertools.product((0,1),repeat=4));best=[]
  # Each player has one decision of each kind along any history in this tree.
  for owner in (0,1):
   values=[]
   for t in range(2):
    candidates=[]
    for plan in plans:
     q=list(prior)
     for i,n in enumerate(p['tree']['nodes']):
      if n['actor']!=owner:continue
      off=p['offsets'][i]+t*len(n['actions']);q[off:off+len(n['actions'])]=[float(a==st.legacy_action(plan,n,p['tree'])) for a in range(len(n['actions']))]
     candidates.append(self.metric(p,q)['profile_hero_ev_bb'])
    values.append((max if owner==0 else min)(candidates))
   baseline=actual['profile_hero_ev_bb'];best.append(sum(values)-baseline)
  self.assertAlmostEqual(best[0],actual['hero_br_ev_bb'],places=12);self.assertAlmostEqual(best[1],actual['villain_br_hero_ev_bb'],places=12)
 def test_cfr_incremental_and_regret_certificate(self):
  p=self.small(fractions=(1/3,.5,.75));prior=st.uniform(p);a=st.trajectory(self.lib,p,prior,[16,128,2048]);b=st.trajectory(self.lib,p,prior,[2048]);self.assertEqual(a[-1],b[-1]);self.assertLess(a[-1][1]['restricted_nashconv_bb'],a[0][1]['restricted_nashconv_bb']);self.assertLessEqual(a[-1][1]['restricted_nashconv_bb'],a[-1][1]['positive_counterfactual_regret_bound_bb']+1e-7)
 def test_invalid_equity_or_strategy_rejected(self):
  p=self.small();q=st.uniform(p);p['equity'][0]=1
  with self.assertRaises(ValueError):self.metric(p,q)
  p=self.small();q[0]=float('nan')
  with self.assertRaises(ValueError):self.metric(p,q)
 def test_half_extension_preserves_profile_but_not_br(self):
  for actor in (0,1):
   p=self.small(actor);m=self.small(actor,(1/3,.5,.75));q=st.trajectory(self.lib,p,st.uniform(p),[128])[0][0];extended=st.extend_half(q,p,m);self.assertAlmostEqual(self.metric(p,q)['profile_hero_ev_bb'],self.metric(m,extended)['profile_hero_ev_bb'],places=12)
 def test_safe_game_value_bounds_hold(self):
  for actor in (0,1):
   p=self.small(actor,(1/3,.5,.75));m=st.trajectory(self.lib,p,st.uniform(p),[512])[0][1];r=cov.sample_row(m,18);self.assertLessEqual(r['game_value_lower_bb'],r['game_value_upper_bb']);self.assertGreaterEqual(r['game_value_lower_bb'],-9);self.assertLessEqual(r['game_value_upper_bb'],9)

class CoverageTests(unittest.TestCase):
 def row(self,b,p,v=0):return {'flop':b,'board_probability':p,'profile_hero_ev_bb':v,'game_value_lower_bb':v-.1,'game_value_upper_bb':v+.1}
 def test_duplicate_draws_do_not_duplicate_probability_coverage(self):
  r=self.row([0,1,2],.001);x=cov.interval({'a':[r,r],'b':[self.row([0,1,3],.002)]},{'a':.9,'b':.1},18,.01/24);self.assertEqual(x['draw_count'],3);self.assertEqual(x['unique_physical_boards'],2);self.assertAlmostEqual(x['evaluated_board_probability'],.003);self.assertAlmostEqual(x['weighted_hoeffding_variance_factor'],.9**2/2+.1**2)
 def test_hoeffding_scaling_and_explicit_unknown_bounds(self):
  x=cov.interval({'a':[self.row([0,1,2],.01)]},{'a':1},18,.01/24);self.assertAlmostEqual(x['game_value_sampling_radius_bb'],18*math.sqrt(math.log(2400)/2));self.assertEqual(x['uncomputed_profile_ev_contribution_bounds_bb'],[-49.5,49.5]);self.assertEqual(x['model_approximation_error'],'UNKNOWN')
 def test_nested_intersection_preserves_failures(self):
  rows={'a':[self.row([0,1,2],.01)]};x=cov.interval(rows,{'a':1},18,.001);previous={**x,'restricted_game_value_interval_bb':[100,101]};y=cov.interval(rows,{'a':1},18,.001,previous);self.assertTrue(y['empty_intersection_failure'])
 def test_cache_atomic_identity_and_checksum(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'cache.json';identity={'seed':1};row=self.row([0,1,2],.01);self.assertIsNone(cov.cache_load(path,identity));cov.cache_write(path,identity,row);self.assertEqual(cov.cache_load(path,identity),row)
   with self.assertRaises(ValueError):cov.cache_load(path,{'seed':2})
   data=json.loads(path.read_text());data['row']['profile_hero_ev_bb']=5;path.write_text(json.dumps(data))
   with self.assertRaises(ValueError):cov.cache_load(path,identity)
 def test_all_strata_required_and_inconsistent_duplicate_rejected(self):
  with self.assertRaises(ValueError):cov.interval({'a':[]},{'a':1},18,.01)
  with self.assertRaises(ValueError):cov.interval({'a':[self.row([0,1,2],.01),self.row([0,1,2],.01,1)]},{'a':1},18,.01)
 def test_validation_only_selection_uses_cheapest_acceptable(self):
  c=lambda n,w,m:{'iterations':n,'summary':{'overall':{'worst_nashconv_bb':w,'mean_nashconv_bb':m}}};self.assertEqual(study.choose([c(512,.2,.1),c(2048,.09,.04),c(8192,.01,.01)]),(2048,True));self.assertEqual(study.choose([c(512,.2,.1),c(2048,.15,.06)]),(2048,False))


class RootBoundsTests(unittest.TestCase):
 def test_frozen_root_reach_and_readonly_interval_conservation(self):
  from gto.abstract import street_root_bounds as rb
  # Reuse frozen input decoder without modifying the policy or payoff archive.
  from gto.abstract.range_study import initialize
  with tempfile.TemporaryDirectory() as d:
   _,_,_,pi,_=initialize(Path(d));before=list(pi);population={'family_confidence':.99,'stages':{s:{'checkpoints':[{'uniform512_profile_ev_interval_bb':[-50.,50.],'evaluated_board_probability':.01,'empty_intersection_failure':False}]} for s in ('vs_3bet','vs_4bet')}};out=rb.root_bounds(pi,population);self.assertEqual(pi,before);self.assertGreater(out['computed_root_board_probability'],0);self.assertLessEqual(out['root_sb_ev_interval_bb'][0],out['root_sb_ev_interval_bb'][1]);self.assertAlmostEqual(out['computed_root_board_probability'],.01*out['two_profile_call_probability']);self.assertLessEqual(out['other_call_probability_unknown']+out['two_profile_call_probability'],1+1e-12)
   population['stages']['vs_3bet']['checkpoints'][0]['uniform512_profile_ev_interval_bb']=[-1.,2.];population['stages']['vs_4bet']['checkpoints'][0]['uniform512_profile_ev_interval_bb']=[3.,4.];asym=rb.root_bounds(pi,population);entry=asym['conditional_prefixes']['vs_4bet'];mass=entry['call_leaf_probability'];self.assertEqual(entry['root_sb_contribution_interval_bb'],[-4*mass,-3*mass])
 def test_invalid_conditional_interval_rejected(self):
  from gto.abstract import street_root_bounds as rb
  from gto.abstract.range_study import initialize
  with tempfile.TemporaryDirectory() as d:
   _,_,_,pi,_=initialize(Path(d));p={'family_confidence':.99,'stages':{s:{'checkpoints':[{'uniform512_profile_ev_interval_bb':[-1,1],'evaluated_board_probability':.01,'empty_intersection_failure':True}]} for s in ('vs_3bet','vs_4bet')}}
   with self.assertRaises(ValueError):rb.root_bounds(pi,p)

if __name__=='__main__':unittest.main()
