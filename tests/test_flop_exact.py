import json,math,random,tempfile,unittest
from pathlib import Path
from gto.abstract import flop_exact as f
from gto.abstract.precision_runouts import build as runout_build,exact
from gto.abstract.precision_archive import unpack
from gto.abstract.flop_conditional import posterior,saved_controller,new_controller,Policy,Observation
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract import continuation_learning as learn

class ExactFlopTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.lib=f.build(Path(cls.tmp.name)/'exact');cls.fast=runout_build(Path(cls.tmp.name)/'reference');cls.m=f.matrix(cls.lib,(48,21,3))
  _,p=unpack(json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text()));cls.policy=p['flop_controller']
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_cached_matrix_matches_every_runout_oracle_for_selected_holes(self):
  pairs=[(44,45),(40,41),(0,4),(28,29),(32,36),(49,50)];m=f.matrix(self.lib,(48,21,3),pairs);n=len(pairs)
  self.assertEqual(m['labels'][0],f.CLASSES.index('KK'))
  for i,a in enumerate(pairs):
   for j,b in enumerate(pairs):
    if set(a)&set(b):continue
    w,t,l=exact(self.fast,a+b,(48,21,3));self.assertEqual(m['win'][i*n+j],w);self.assertEqual(m['tie'][i*n+j],t)
 def test_invalid_matrix_inputs(self):
  for ps in ([],[(48,49)],[(0,0)],[(0,1),(1,0)],[(0,52)]):
   with self.assertRaises(ValueError):f.matrix(self.lib,(48,21,3),ps)
 def test_full_exact_posterior_and_pair_counts(self):
  self.assertEqual(self.m['n'],1176)
  for stage in ('vs_3bet','vs_4bet'):
   r=f.evaluate(self.lib,self.m,self.policy,stage);reach=frozen_reach(stage,self.policy,after_call=True);_,p,c=posterior(self.m['flop'],reach['hero_reach'],reach['villain_reach'])
   self.assertEqual(sum(c),1271256)
   for a,b in zip(r['rows'],p):self.assertAlmostEqual(a['posterior_probability'],b,places=12)
   self.assertAlmostEqual(r['aggregate']['new']-r['aggregate']['old'],r['aggregate']['delta'],places=12)
   self.assertEqual(r['hole_sampling_error_bb'],0)
 def test_native_payoff_matches_independent_python_controller_class_sum(self):
  n=self.m['n'];pairs=self.m['pairs'];labels=self.m['labels']
  for stage,h in ((s,h) for s in ('vs_3bet','vs_4bet') for h in (0,f.CLASSES.index('KQo'),f.CLASSES.index('76s'))):
   r=f.evaluate(self.lib,self.m,self.policy,stage);reach=frozen_reach(stage,self.policy,after_call=True);mass=[];old=[];new=[]
   for i,a in enumerate(pairs):
    if labels[i]!=h:continue
    for j,b in enumerate(pairs):
     if set(a)&set(b):continue
     w=reach['hero_reach'][h]*reach['villain_reach'][labels[j]];e=(self.m['win'][i*n+j]+self.m['tie'][i*n+j]/2)/990
     mass.append(w);old.append(w*saved_controller(e,a,b,self.m['flop'],reach['hero_actor'],reach['matched_contribution_bb'],reach['remaining_stack_bb']))
     new.append(w*new_controller(e,a,b,self.m['flop'],reach['hero_actor'],reach['post_call_pot_bb'],reach['remaining_stack_bb'],lambda obs:Policy(1,1,1,1)))
   self.assertAlmostEqual(r['rows'][h]['old_ev_bb'],math.fsum(old)/math.fsum(mass),places=11)
   self.assertAlmostEqual(r['rows'][h]['new_ev_bb'],math.fsum(new)/math.fsum(mass),places=11)
 def test_matrix_seat_exchange_integer_identity(self):
  rng=random.Random(91);n=self.m['n']
  for _ in range(200):
   i,j=rng.randrange(n),rng.randrange(n)
   if set(self.m['pairs'][i])&set(self.m['pairs'][j]):continue
   self.assertEqual(self.m['win'][i*n+j]+self.m['win'][j*n+i]+self.m['tie'][i*n+j],990)
 def test_train_holdout_split_invariant_to_swapped_seats(self):
  a=(44,45);b=(0,4);f0=(48,21,3)
  self.assertEqual(learn.partition(a,b,f0),learn.partition(b,a,f0))
  reach=frozen_reach('vs_3bet',self.policy,after_call=True)
  tr=learn.draw_worlds(self.m,reach,count=100,seed=17,heldout=False);ev=learn.draw_worlds(self.m,reach,count=100,seed=29,heldout=True)
  def keys(xs):return {tuple(sorted((tuple(self.m['pairs'][i]),tuple(self.m['pairs'][j])))) for i,j,e in xs}
  self.assertFalse(keys(tr)&keys(ev))
 def test_learning_seed_reproducibility_and_observation_only_policy(self):
  reach=frozen_reach('vs_4bet',self.policy,after_call=True);worlds=learn.draw_worlds(self.m,reach,count=50,seed=55,heldout=False);data=learn.dataset(self.m,reach,worlds)
  a=learn.train(data,epochs=3,seed=17);b=learn.train(data,epochs=3,seed=17);self.assertEqual(a.table,b.table)
  for probs in a.table.values():self.assertAlmostEqual(sum(probs),1);self.assertTrue(all(0<=x<=1 for x in probs))
  obs=Observation((44,45),self.m['flop'],1,42,29);self.assertEqual(a(obs),a(obs));self.assertFalse(hasattr(obs,'opponent_holes'))
 def test_complete_plan_mixture_not_behavior_parameter_average(self):
  # Plans preserve within-hand action correlation. Average parameters can differ.
  e=.65;a,b=learn.ARMS[0],learn.ARMS[3];v=Policy(0,1,1,1)
  mixed=(learn.payoff(e,a,v,0,18,41)+learn.payoff(e,b,v,0,18,41))/2
  parameter_mean=Policy(*((getattr(a,k)+getattr(b,k))/2 for k in ('bet','raise_after_bet','call_bet','call_raise')))
  self.assertNotAlmostEqual(mixed,learn.payoff(e,parameter_mean,v,0,18,41))

if __name__=='__main__':unittest.main()
