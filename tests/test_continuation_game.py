import ctypes as C,itertools,math,tempfile,unittest,json,copy
from pathlib import Path
from gto.abstract import continuation_game as g
from gto.abstract import flop_exact as f
from gto.abstract.model import doubles
from gto.abstract.precision_archive import unpack
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.continuation_learning import FrozenContinuation,match
H=(0,18.,41.,0,0,0);V=(1,18.,41.,0,0,0)

def toy():return {'hkeys':[H],'vkeys':[V],'tensor':[[[[1. if a%2==b%2 else -1. for b in range(4)] for a in range(4)]]]}
def pure(a):return tuple(float(i==a) for i in range(4))

class ContinuationGameTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name);cls.lib=g.build(root/'game');cls.rank=f.build(root/'rank');cls.m=f.matrix(cls.rank,(48,21,3));_,p=unpack(json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text()));cls.pi=p['flop_controller']
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_known_zero_sum_best_responses_and_convention(self):
  a=toy();uniform=FrozenContinuation({});r=g.evaluate(a,uniform);self.assertAlmostEqual(r['restricted_nashconv_bb'],0)
  r=g.evaluate(a,FrozenContinuation({H:pure(0),V:pure(0)}));self.assertEqual(r['profile_hero_ev_bb'],1);self.assertEqual(r['hero_br_ev_bb'],1);self.assertEqual(r['villain_br_hero_ev_bb'],-1);self.assertEqual(r['restricted_exploitability_bb'],1)
 def test_response_cannot_observe_opponent_private_type(self):
  v2=(1,18.,41.,1,0,0);a={'hkeys':[H],'vkeys':[V,v2],'tensor':[[[[.5 if x%2==0 else -.5 for y in range(4)] for x in range(4)],[[-.5 if x%2==0 else .5 for y in range(4)] for x in range(4)]]]}
  self.assertEqual(g.evaluate(a,FrozenContinuation({}))['hero_br_ev_bb'],0) # clairvoyance would yield1
 def test_exact_br_matches_bruteforce_type_contingent_policies(self):
  import random
  rng=random.Random(91);h2=(0,18.,41.,1,0,0);a={'hkeys':[H,h2],'vkeys':[V],'tensor':[[[[rng.uniform(-1,1) for b in range(4)] for x in range(4)]] for h in range(2)]};p=FrozenContinuation({V:(.1,.2,.3,.4)});r=g.evaluate(a,p)
  values=[g.evaluate(a,FrozenContinuation({H:pure(x),h2:pure(y),V:p.table[V]}))['profile_hero_ev_bb'] for x,y in itertools.product(range(4),repeat=2)]
  self.assertAlmostEqual(r['hero_br_ev_bb'],max(values))
 def test_uniform_time_average_matches_first_two_full_sweeps(self):
  a=toy();flat=[x for row in a['tensor'] for m in row for arm in m for x in arm];avg=(C.c_double*8)();reg=(C.c_double*8)();self.assertEqual(self.lib.type_solve(1,1,doubles(flat),1,17,avg,reg),0)
  expected=[(avg[i]+match(reg[(i//4)*4:(i//4)*4+4])[i%4])/2 for i in range(8)];p,_=g.solve(self.lib,a,2,17)
  for x,y in zip(expected,(*p.table[H],*p.table[V])):self.assertAlmostEqual(x,y,places=12)
 def test_restricted_regret_bound_convergence_seed_and_scale(self):
  a=toy();_,start=g.solve(self.lib,a,1,17);p,end=g.solve(self.lib,a,10000,17);p2,end2=g.solve(self.lib,a,10000,17)
  self.assertEqual(p.table,p2.table);self.assertLess(end['restricted_nashconv_bb'],start['restricted_nashconv_bb']);self.assertLess(end['restricted_nashconv_bb'],.1);self.assertLessEqual(end['restricted_nashconv_bb'],end['positive_external_regret_bound_bb']+1e-10)
  scaled=toy();scaled['tensor']=[[[[3*x for x in arm] for arm in m] for m in row] for row in a['tensor']];_,s=g.solve(self.lib,scaled,10000,17);self.assertAlmostEqual(s['restricted_nashconv_bb'],3*end['restricted_nashconv_bb'],places=10)
 def test_exact_chance_marginals_against_private_blocker_inclusion_exclusion(self):
  stage='vs_3bet';a=g.game(self.lib,self.m,self.pi,stage);r=frozen_reach(stage,self.pi,after_call=True);pairs=self.m['pairs'];labels=self.m['labels'];v=[r['villain_reach'][h] for h in labels];cm=[0.]*52;by_pair={}
  for p,w in zip(pairs,v):
   for c in p:cm[c]+=w
   by_pair[tuple(sorted(p))]=w
  total=math.fsum(v);weights=[r['hero_reach'][h]*(total-cm[p[0]]-cm[p[1]]+by_pair[tuple(sorted(p))]) for p,h in zip(pairs,labels)];keys,_=g.observations(self.m,r);mass=math.fsum(weights);bv=len(a['vkeys'])
  self.assertAlmostEqual(sum(a['chance_mass']),1,places=12)
  for i,k in enumerate(a['hkeys']):self.assertAlmostEqual(sum(a['chance_mass'][i*bv:(i+1)*bv]),math.fsum(w for w,t in zip(weights,keys) if t==k)/mass,places=11)
 def test_exact_type_payoffs_match_independent_frozen_world_evaluator(self):
  for stage in ('vs_3bet','vs_4bet'):
   a=g.game(self.lib,self.m,self.pi,stage);ref=f.evaluate(self.rank,self.m,self.pi,stage);p=FrozenContinuation({k:pure(2) for k in a['hkeys']+a['vkeys']});ev=g.evaluate(a,p)
   self.assertAlmostEqual(ev['profile_hero_ev_bb'],ref['aggregate']['new'],places=11)
 def test_leaf_reconciles_chance_and_sb_chip_transposition(self):
  for stage in ('vs_3bet','vs_4bet'):
   a=g.game(self.lib,self.m,self.pi,stage);p,_=g.solve(self.lib,a,100,17);leaf=g.research_leaf(self.lib,self.m,self.pi,stage,p);r=frozen_reach(stage,self.pi,after_call=True);weights=[leaf['compatible_hole_counts'][i*169+j]*r['hero_reach'][i]*r['villain_reach'][j] for i in range(169) for j in range(169)];value=math.fsum(x*w for x,w in zip(leaf['hero_net_bb_by_class_pair'],weights))/math.fsum(weights)
   self.assertAlmostEqual(value,g.evaluate(a,p)['profile_hero_ev_bb'],places=10)
   i,j=0,1;target=i*169+j if r['hero_actor']==0 else j*169+i;sign=1 if r['hero_actor']==0 else -1
   self.assertAlmostEqual(leaf['sb_net_chips_by_class_pair'][target],sign*2*leaf['hero_net_bb_by_class_pair'][i*169+j]);self.assertFalse(leaf['full_game_gto_verified'])
 def test_fixed_opponents_and_unknown_type_evaluation_do_not_train(self):
  a=toy();p,_=g.solve(self.lib,a,100,29);before=copy.deepcopy(p.table);rows=g.fixed_opponents(a,p);self.assertEqual(len(rows),6)
  for row in rows:self.assertGreaterEqual(row['hero_improvement_bb'],-1e-10);self.assertGreaterEqual(row['villain_improvement_bb'],-1e-10)
  unknown=toy();unknown['hkeys']=[(0,18.,41.,1,1,1)];g.evaluate(unknown,p);self.assertEqual(p.table,before)

if __name__=='__main__':unittest.main()
