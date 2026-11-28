import copy,json,math,unittest
from pathlib import Path
from gto.abstract.model import tree
from gto.abstract.flop_tree_ablation import Policy,evaluate_flop
from gto.abstract.flop_reach_adapter import conditional_flop_ev
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.frozen_flop_ablation import evaluate_frozen_ablation
from gto.abstract.frozen_ablation_study import study,estimate,SIZE

class FrozenMeasurementTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.packet=json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text())
  cls.uniform=[0.]*(len(tree())*3*169)
  for v,node in enumerate(tree()):
   if node['actor']>=0:
    for a in range(len(node['actions'])):
     for h in range(169):cls.uniform[(v*3+a)*169+h]=1/len(node['actions'])
 def test_frozen_call_posterior_real_pot_and_remaining_stack(self):
  for stage,pot,stack,actor in [('vs_3bet',18,41,0),('vs_4bet',42,29,1)]:
   before=frozen_reach(stage,self.uniform);after=frozen_reach(stage,self.uniform,after_call=True)
   self.assertAlmostEqual(after['conditional_mass'],before['conditional_mass']/3)
   self.assertEqual(after['post_call_pot_bb'],pot);self.assertEqual(after['remaining_stack_bb'],stack);self.assertEqual(after['hero_actor'],actor)
 def test_unnormalized_frozen_decision_row_is_rejected(self):
  broken=self.uniform.copy();broken[0]=.2
  with self.assertRaises(ValueError):frozen_reach('vs_3bet',broken)
 def test_bb_is_oop_not_ip(self):
  p=[0.]*SIZE;p[0]=1.;r=[0.]*169;r[0]=1.;e=[.2]*SIZE
  hero=Policy(1,0,1,1);villain=Policy(1,0,0,0)
  result=conditional_flop_ev(stage='vs_4bet',class_probability=p,hero_reach=r,villain_reach=r,equity_by_pair=e,hero_policy=hero,villain_policy=villain,pot_bb=9)
  self.assertEqual(result['new_flop_tree_ev_bb'],9.) # OOP bets first; IP folds
  ip=conditional_flop_ev(stage='vs_3bet',class_probability=p,hero_reach=r,villain_reach=r,equity_by_pair=e,hero_policy=hero,villain_policy=villain,pot_bb=9)
  self.assertAlmostEqual(ip['new_flop_tree_ev_bb'],-.9)
 def test_stack_cap_and_no_raise_against_allin(self):
  always=Policy(1,1,1,1)
  self.assertAlmostEqual(evaluate_flop(1.,always,always,pot=42,effective_stack=29),71.)
  self.assertAlmostEqual(evaluate_flop(0.,always,always,pot=42,effective_stack=29),-29.)
  with self.assertRaises(ValueError):evaluate_flop(.5,always,always,pot=42,effective_stack=21)
 def test_oop_check_raise_fold_matches_independent_cash_ledger(self):
  p=[0.]*SIZE;p[0]=1.;r=[0.]*169;r[0]=1.
  hero=Policy(0,1,1,1);villain=Policy(1,0,1,0)
  result=conditional_flop_ev(stage='vs_4bet',class_probability=p,hero_reach=r,villain_reach=r,equity_by_pair=[.2]*SIZE,hero_policy=hero,villain_policy=villain,pot_bb=42,remaining_stack_bb=29)
  # BB checks; SB bets21; BB all-in raises29; SB folds. Net from
  # street start is the old pot42 plus SB bet21,regardless of equity.
  self.assertAlmostEqual(result['new_flop_tree_ev_bb'],63.)
 def test_pot_cannot_be_invented_when_conditioned_on_call(self):
  check=Policy(0,0,0,0);kernel={'mean':[0.]*(5*SIZE)}
  with self.assertRaises(ValueError):evaluate_frozen_ablation('vs_4bet',self.uniform,kernel,check,check,pot_bb=9,condition_on_call=True)
 def test_chance_must_be_normalized(self):
  p=[0.]*SIZE;p[0]=.5;r=[0.]*169;r[0]=1.
  with self.assertRaises(ValueError):conditional_flop_ev(stage='vs_3bet',class_probability=p,hero_reach=r,villain_reach=r,equity_by_pair=[.5]*SIZE,hero_policy=Policy(0,0,0,0),villain_policy=Policy(0,0,0,0),pot_bb=18)
 def test_paired_showdown_symmetry_is_not_counted_as_independent(self):
  k={'mean':[0.]*(5*SIZE),'samples_per_class_pair':256};c=[0.]*(5*SIZE);c[1]=c[169]=1.
  result=estimate(k,c,0.,.001)
  self.assertEqual(result['sampling_radius_bb'],0.)
 def test_real_archive_report_reproduces_and_preserves_inputs(self):
  before=json.dumps(self.packet,sort_keys=True);r=study(self.packet)
  self.assertEqual(r['compatible_combo_deals'],1624350);self.assertEqual(len(r['rows']),4)
  self.assertEqual(r['simultaneous_interval_count'],72);self.assertFalse(r['equity_is_conditioned_on_specific_flop']);self.assertFalse(r['full_game_gto_verified'])
  for row in r['rows']:
   self.assertLess(row['post_call_reach_mass'],row['before_call_reach_mass'])
   self.assertAlmostEqual(row['existing_card_flop_delta']['ev_bb'],row['existing_card_flop_net_before_blinds']['ev_bb']-row['old_checkdown_net_before_blinds']['ev_bb'],places=10)
   self.assertLessEqual(row['experimental_flop_tree']['raise_call']['raise_to_bb'],row['remaining_stack_bb'])
  self.assertEqual(before,json.dumps(self.packet,sort_keys=True))

 def test_full_facing_node_matches_independent_native_continuation_tree(self):
  import ctypes as C,os,tempfile
  from gto.abstract.model import build,load,ints,doubles,payoffs,chance,classes
  from gto.abstract.precision_archive import unpack
  from gto.abstract.frozen_ablation_study import decision_coefficients,PROTOCOLS
  k,policies=unpack(self.packet);policy=policies['flop_controller'];nodes=tree();n=169;m=len(nodes);_,p=chance(classes())
  with tempfile.TemporaryDirectory() as directory:
   lib=load(os.environ.get('GTO_ABSTRACT_LIBRARY') or build(directory))
   variants={'checkdown':(k,'checkdown'),'saved_card':(k,'flop_controller')}
   for name,proto in PROTOCOLS.items():
    means=list(k['mean'][:SIZE])
    for x in (2,5,18,42):
     low=evaluate_flop(0.,proto,proto,pot=2*x,effective_stack=100-x);high=evaluate_flop(1.,proto,proto,pot=2*x,effective_stack=100-x)
     intercept=low+(high-low)/2-x;slope=(high-low)/200
     means.extend(intercept+slope*value for value in k['mean'][:SIZE])
    variants[name]=({'mean':means},'flop_controller')
   expected={}
   for name,(kernel,mode) in variants.items():
    ev=(C.c_double*(m*3*n))();reach=(C.c_double*(m*n))();metrics=(C.c_double*4)()
    self.assertEqual(lib.abstract_evaluate(n,m,ints([x['actor'] for x in nodes]),ints([len(x['actions']) for x in nodes]),ints([c for x in nodes for c in (x['children']+[-1]*3)[:3]]),doubles(p),doubles(payoffs(kernel,mode,nodes)),doubles(policy),ev,reach,metrics),0)
    for stage in ('vs_3bet','vs_4bet'):
     v=frozen_reach(stage,policy)['node_index'];mass=math.fsum(reach[v*n+h] for h in range(n))
     expected[name,stage]=math.fsum(reach[v*n+h]*policy[(v*3+a)*n+h]*ev[(v*3+a)*n+h]/2 for h in range(n) for a in range(len(nodes[v]['actions'])))/mass
   for stage in ('vs_3bet','vs_4bet'):
    coeff,constant=decision_coefficients(policy,stage)
    for name in variants:self.assertAlmostEqual(estimate(k,coeff[name],constant[name],.001)['ev_bb'],expected[name,stage],places=10)

if __name__=='__main__':unittest.main()
