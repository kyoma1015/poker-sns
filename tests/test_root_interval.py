import ctypes as C,itertools,json,math,tempfile,unittest,copy
from pathlib import Path
from gto.abstract import root_interval as ri,root_br_study as study,street_tree as st,call_study as cs,call_reach as cr,model

class RootIntervalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name);cls.env=cs.setup(root/'env');cls.coeff=ri.build(root/'coeff');cls.native=model.load(model.build(root/'preflop'))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def small(self):
  from tests.test_street_coverage import StreetTests
  return StreetTests().small(fractions=(1/3,.5,.75))
 def test_behavioral_coefficients_equal_independent_path_cashflows(self):
  g=self.small();policy=st.uniform(g);a,b=ri.coefficients(self.coeff,g,policy)
  def walk(k,i,j,e):
   n=g['tree']['nodes'][k]
   if n['actor']<0:return n['c0']+n['c1']*e
   t=i if n['actor']==0 else j;off=g['offsets'][k]+t*len(n['actions']);return sum(policy[off+x]*walk(c,i,j,e) for x,c in enumerate(n['children']))
  for i in range(2):
   for j in range(2):
    for e in (0.,.2,1.):self.assertAlmostEqual(a[i*2+j]+e*b[i*2+j],walk(0,i,j,e),places=12)
  expected=sum(x*y+z*w for x,y,z,w in zip(a,g['mass'],b,g['equity']));self.assertAlmostEqual(expected,st.evaluate(self.env[-1],g,policy)['profile_hero_ev_bb'],places=12)
 def test_class_pair_unweighted_leaf_matches_reached_profile_and_support(self):
  r=cr.extract(self.env[3],['raise_to_5','call'],'open_call');m=study.exact.matrix(self.env[0],[8,13,18]);g=cs.prepared(self.env,m,r,json.loads(cs.P.read_text()));policy=st.uniform(g);value=st.evaluate(self.env[-1],g,policy)['profile_hero_ev_bb'];known,mass,error=ri.class_partial(self.env[1],self.coeff,m,g,policy,r['hero_actor'],r['hero_reach'],r['villain_reach'],value);self.assertLess(error,1e-10);self.assertEqual(len(known),169**2);self.assertTrue(all(0<=q<=1 for q in mass));self.assertTrue(any(q>0 for q in mass))
 def toy(self):
  nodes=[{'actor':0,'actions':['l','r'],'children':[1,4]},{'actor':1,'actions':['l','r'],'children':[2,3]},{'actor':-1,'actions':[],'children':[]},{'actor':-1,'actions':[],'children':[]},{'actor':1,'actions':['l','r'],'children':[5,6]},{'actor':-1,'actions':[],'children':[]},{'actor':-1,'actions':[],'children':[]}];pi=[0.]*(7*3*2)
  for k,n in enumerate(nodes):
   for a in range(len(n['actions'])):
    for t in range(2):pi[(k*3+a)*2+t]=.5
  A=[2.,-2.,-2.,2.];point=[0.]*(7*4)
  for k,v in [(2,[x+1 for x in A]),(3,[x-1 for x in A]),(5,[-x+.5 for x in A]),(6,[-x-.5 for x in A])]:point[k*4:(k+1)*4]=v
  return nodes,pi,point
 def test_preflop_BR_matches_exhaustive_own_info_policies_not_clairvoyance(self):
  nodes,pi,point=self.toy();chance=[.25]*4
  def value(policy):
   def walk(k,i,j):
    node=nodes[k]
    if node['actor']<0:return point[k*4+i*2+j]
    t=i if node['actor']==0 else j;return sum(policy[(k*3+a)*2+t]*walk(c,i,j) for a,c in enumerate(node['children']))
   return sum(chance[i*2+j]*walk(0,i,j) for i in range(2) for j in range(2))
  expected=[]
  for actor in (0,1):
   infos=[(k,t) for k,n in enumerate(nodes) if n['actor']==actor for t in range(2)];scores=[]
   for choices in itertools.product(range(2),repeat=len(infos)):
    p=list(pi)
    for (k,t),selected in zip(infos,choices):
     for a in range(2):p[(k*3+a)*2+t]=float(a==selected)
    scores.append(value(p))
   expected.append((max if actor==0 else min)(scores))
  result=ri.evaluate(self.native,nodes,pi,chance,point,point,2);self.assertAlmostEqual(result['profile_sb_ev_interval'][0],value(pi));self.assertEqual(result['sb_preflop_br_ev_interval'],[expected[0]]*2);self.assertEqual(result['bb_preflop_br_sb_ev_interval'],[expected[1]]*2);self.assertAlmostEqual(expected[0],0.);self.assertLess(expected[0],2.)
 def test_interval_monotonicity_and_inverted_bounds_rejected(self):
  nodes,pi,point=self.toy();chance=[.4,.1,.1,.4];lo=[x-.2 for x in point];hi=[x+.2 for x in point];a=ri.evaluate(self.native,nodes,pi,chance,point,point,2);b=ri.evaluate(self.native,nodes,pi,chance,lo,hi,2)
  for key in ('profile_sb_ev_interval','sb_preflop_br_ev_interval','bb_preflop_br_sb_ev_interval'):self.assertLessEqual(b[key][0],a[key][0]);self.assertGreaterEqual(b[key][1],a[key][1])
  with self.assertRaises(ValueError):ri.evaluate(self.native,nodes,pi,chance,hi,lo,2)
 def test_unknown_CALL_payoffs_are_not_zero_and_policy_is_readonly(self):
  pi=self.env[3];before=list(pi);out=ri.root_bounds(self.native,pi,[]);rows=cr.leaf_ledger(pi);fold=sum(x['probability']*x['fold_sb_payoff_bb'] for x in rows if not x['matched']);mass=sum(x['probability'] for x in rows if x['matched']);self.assertAlmostEqual(out['profile_sb_ev_interval'][0],fold-50*mass,places=6);self.assertAlmostEqual(out['profile_sb_ev_interval'][1],fold+50*mass,places=6);self.assertGreater(out['profile_sb_ev_interval'][1]-out['profile_sb_ev_interval'][0],50);self.assertEqual(before,pi);self.assertFalse(out['policy_updated'])
 def test_response_stops_at_first_registered_checkpoint(self):
  g=self.small();trace=ri.respond_until(self.env[-1],g,[8,16,32],1000.);self.assertEqual(len(trace),1);self.assertEqual(trace[0]['iterations'],8)
 def test_design_new_only_and_fresh674_suit_orbits(self):
  p=json.loads(study.P.read_text());d=study.select_events(p);self.assertEqual(len(d['selected_events']),256);self.assertEqual(len({(r['stage'],tuple(r['flop'])) for r in d['selected_events']}),256);old=json.loads((cs.ROOT/'population-results.json').read_text());excluded={tuple(b) for b in p['response']['excluded_previous_suit_orbits']};self.assertEqual(len(excluded),674);fresh={study.canonical(r['cards']) for r in p['response']['fresh_audit']};self.assertFalse(fresh&excluded)
  for s,v in old['stages'].items():
   used={tuple(r['flop']) for rows in v['sample_rows'].values() for r in rows};used.update(tuple(r['flop']) for r in v['priority_rows']);new=[r for r in d['selected_events'] if r['stage']==s];self.assertGreaterEqual(len(new),24);self.assertTrue(all(tuple(r['flop']) not in used and study.canonical(r['flop']) not in fresh for r in new))
 def test_changed_design_identity_rejected_before_evaluation(self):
  from unittest.mock import patch
  with patch.object(study,'sources',return_value={'changed':'yes'}):
   with self.assertRaises(ValueError):study.check()

if __name__=='__main__':unittest.main()
