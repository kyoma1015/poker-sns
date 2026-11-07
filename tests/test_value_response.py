import copy,itertools,json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import value_response as vr,value_study as study,continuation_game as base
from gto.abstract.continuation_learning import FrozenContinuation
from gto.abstract.factorial_transfer import Transfer,category


def chance_game():
 mass=[[.4,.1],[.2,.3]];return {'hkeys':[(0,0),(0,1)],'vkeys':[(1,0),(1,1)],'chance_mass':[x for row in mass for x in row],'tensor':[[[[mass[i][j]*(2*x-2*y+i-j) for y in range(4)] for x in range(4)] for j in range(2)] for i in range(2)]}
def prior(g):return FrozenContinuation({k:(.1,.2,.3,.4) for k in g['hkeys']+g['vkeys']})
def python_response(g,initial,n):
 keys=g['hkeys']+g['vkeys'];r={k:[0.]*4 for k in keys};avg={k:[0.]*4 for k in keys}
 for t in range(n):
  p={k:tuple(initial.table[k]) if t==0 else tuple(max(0.,x)/sum(max(0.,v) for v in r[k]) for x in r[k]) if max(r[k])>0 else (.25,)*4 for k in keys}
  targets=vr.conditional_targets(g,FrozenContinuation(p))
  for k in keys:
   row=targets[k]
   for a in range(4):r[k][a]+=row['conditional_regret_bb'][a]*row['own_marginal_mass'];avg[k][a]+=p[k][a]/n
 return avg


class ValueResponse(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.temp=tempfile.TemporaryDirectory();cls.lib=vr.build(Path(cls.temp.name))
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_fresh_board_suit_disjoint_registration(self):
  p=json.loads(study.PROTOCOL.read_text())
  def canon(b):return min(tuple(sorted(c//4*4+q[c%4] for c in b)) for q in itertools.permutations(range(4)))
  used={canon(b) for b in p['excluded_previous_flops']};self.assertEqual(len(used),107)
  for split,n in [('train',21),('validation',7),('final_test',7)]:
   self.assertEqual(len(p['split'][split]),n)
   for row in p['split'][split]:self.assertNotIn(canon(row['cards']),used);used.add(canon(row['cards']));self.assertEqual(category(row['cards']),row['category'])
  self.assertEqual(p['learning_initialization_seeds'],[31,43]);self.assertEqual(len(p['candidates']),7)
 def test_conditional_ev_uses_own_marginal_and_opponent_posterior(self):
  g=chance_game();p=FrozenContinuation({k:(.25,)*4 for k in g['hkeys']+g['vkeys']});t=vr.conditional_targets(g,p)
  for a in range(4):
   self.assertAlmostEqual(t[(0,0)]['conditional_arm_ev_bb'][a],2*a-3.2);self.assertAlmostEqual(t[(0,1)]['conditional_arm_ev_bb'][a],2*a-2.6);self.assertAlmostEqual(t[(1,0)]['conditional_arm_ev_bb'][a],2*a-3-1/3);self.assertAlmostEqual(t[(1,1)]['conditional_arm_ev_bb'][a],2*a-2.75)
 def test_own_ev_regret_and_zero_sum_conservation(self):
  g=chance_game();p=prior(g);t=vr.conditional_targets(g,p);metrics=base.evaluate(g,p);gain=sum(v['own_marginal_mass']*max(v['conditional_regret_bb']) for v in t.values());self.assertAlmostEqual(gain,metrics['restricted_nashconv_bb'],places=12)
  values=[sum(v['own_marginal_mass']*sum(a*b for a,b in zip(v['conditional_arm_ev_bb'],v['probabilities'])) for k,v in t.items() if k[0]==seat) for seat in (0,1)];self.assertAlmostEqual(sum(values),0,places=12)
 def test_zero_mass_has_no_fabricated_conditional_target(self):
  g=chance_game();g['hkeys'].append((0,2));g['tensor'].append([[[0.]*4 for _ in range(4)] for _ in range(2)]);g['chance_mass']+=[0.,0.];t=vr.conditional_targets(g,prior(g));self.assertIsNone(t[(0,2)]['conditional_arm_ev_bb']);self.assertIsNone(t[(0,2)]['conditional_regret_bb'])
 def test_one_update_reuses_prior_without_mutation(self):
  g=chance_game();p=prior(g);before=copy.deepcopy(p.table);q,m=vr.respond(self.lib,g,p,1);self.assertEqual(before,p.table)
  for k in before:
   for x,y in zip(before[k],q.table[k]):self.assertAlmostEqual(x,y,places=14)
  self.assertLessEqual(m['restricted_nashconv_bb'],m['positive_external_regret_bound_bb']+1e-7)
 def test_native_matches_independent_posterior_python_updates(self):
  g=chance_game();p=prior(g);expected=python_response(g,p,32);q,_=vr.respond(self.lib,g,p,32)
  for k,v in expected.items():
   for x,y in zip(v,q.table[k]):self.assertAlmostEqual(x,y,places=12)
 def test_response_converges_in_restricted_game_and_replays(self):
  g=chance_game();p=prior(g);q,m=vr.respond(self.lib,g,p,512);r,n=vr.respond(self.lib,g,p,512);self.assertEqual(q.table,r.table);self.assertEqual(m,n);self.assertLess(m['restricted_nashconv_bb'],.1);self.assertFalse(m['full_game_gto_verified'])
 def test_response_rejects_missing_prior_and_nonfinite_game(self):
  g=chance_game();p=prior(g)
  with self.assertRaises(ValueError):vr.respond(self.lib,g,FrozenContinuation({}),10)
  g['tensor'][0][0][0][0]=float('nan')
  with self.assertRaises(ValueError):vr.respond(self.lib,g,p,10)
  with self.assertRaises(ValueError):vr.respond(self.lib,chance_game(),prior(chance_game()),True)
 def records(self):
  k=(0,18,41,1,0,0,1,1,1,3,8,13,.4,0,0,0,0,0,2,3,7,1,1)
  return k,[{'key':list(k),'training_flop':[0,5,10],'category':'rainbow','own_marginal_mass':.5,'probabilities':[.1,.2,.3,.4],'conditional_arm_ev_bb':[-2,-1,1,2],'conditional_regret_bb':[-3,-2,0,1]}]
 def test_probability_control_reuses_existing_transfer(self):
  k,rows=self.records();new=vr.TargetTransfer(rows,{'family':'probability'});old=Transfer(rows,'global_knn9',True)
  self.assertEqual(new.probabilities(k),old.probabilities(k,[0,5,10]))
 def test_value_choices_are_normalized_and_ev_shift_invariant(self):
  k,rows=self.records();cfg={'family':'value','target':'conditional_arm_ev_bb','temperature_bb':.1};a=vr.TargetTransfer(rows,cfg).probabilities(k);self.assertAlmostEqual(sum(a),1);self.assertGreater(a[3],.999)
  changed=copy.deepcopy(rows);changed[0]['conditional_arm_ev_bb']=[x+100 for x in rows[0]['conditional_arm_ev_bb']];b=vr.TargetTransfer(changed,cfg).probabilities(k)
  for x,y in zip(a,b):self.assertAlmostEqual(x,y,places=12)
 def test_regret_policy_and_nonpositive_fallback(self):
  k,rows=self.records();cfg={'family':'value','target':'conditional_regret_bb'};self.assertEqual(vr.TargetTransfer(rows,cfg).probabilities(k),(0,0,0,1));rows[0]['conditional_regret_bb']=[-1]*4;self.assertEqual(vr.TargetTransfer(rows,cfg).probabilities(k),(.1,.2,.3,.4))
 def test_zeroshot_inference_cannot_read_opponent_tensor(self):
  k,rows=self.records();p=vr.TargetTransfer(rows,{'family':'value','target':'conditional_arm_ev_bb','temperature_bb':0});g={'hkeys':[k],'vkeys':[],'tensor':'no realized opponent cards or utilities exposed'};self.assertEqual(p.materialize(g).table[k],(0,0,0,1))
 def test_selection_enforces_both_stage_noninferiority(self):
  def stats(x,y):return {'overall':{'mean_nashconv_bb':(x+y)/2,'worst_nashconv_bb':max(x,y)},'by_stage':{'vs_3bet':{'mean_nashconv_bb':x,'worst_nashconv_bb':x},'vs_4bet':{'mean_nashconv_bb':y,'worst_nashconv_bb':y}}}
  rows=[{'config':{'name':'control','family':'probability'},'summary':stats(1,1)},{'config':{'name':'bad_stage','family':'value'},'summary':stats(1.1,0)},{'config':{'name':'safe','family':'response'},'summary':stats(.8,.8)}];self.assertEqual(study.choose(rows),({'name':'safe','family':'response'},True))
 def test_final_rejects_identity_change_before_training_or_selection(self):
  with patch.object(study,'initialize',side_effect=AssertionError('initialized')),patch.object(study,'choose',side_effect=AssertionError('selected')):
   with self.assertRaises(ValueError):study.final(Path('/tmp/no'),{}, {},Path('/tmp/no'),[])

if __name__=='__main__':unittest.main()
