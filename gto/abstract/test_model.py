import math,os,random,unittest
from itertools import combinations
from gto.abstract.model import load,rank,classes,chance,tree,solve,kernel,payoffs,ranges
from gto.native.ev_audit import rank_five

class Model(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.lib=load(os.environ['GTO_ABSTRACT_LIBRARY'])
 def test_reused_rank_against_independent_oracle(self):
  rng=random.Random(17)
  for n in (5,7):
   for _ in range(250):
    cards=rng.sample(range(52),n);expected=max(rank_five(list(c)) for c in combinations(cards,5));encoded=0
    for i in range(6):encoded=encoded*15+(expected[i] if i<len(expected) else 0)
    self.assertEqual(rank(self.lib,cards),encoded)
  with self.assertRaises(ValueError):rank(self.lib,[1]*7)
 def test_exact_blocker_joint_matches_direct_enumeration_and_marginal(self):
  groups=classes();counts,p=chance(groups);self.assertEqual(sum(counts),1326*1225)
  for i in range(169):self.assertAlmostEqual(sum(p[i*169:(i+1)*169]),len(groups[i])/1326,places=14)
  for i,j in ((0,0),(1,1),(0,168),(100,101),(168,168)):
   exact=sum(not set(a)&set(b) for a in groups[i] for b in groups[j]);self.assertEqual(counts[i*169+j],exact)
 def test_legal_tree_blinds_and_allin_terminal(self):
  nodes=tree();self.assertEqual(nodes[0]['contributions'],[1,2]);self.assertEqual(nodes[nodes[0]['children'][0]]['value'],-1)
  for node in nodes:
   if node['actor']>=0:
    self.assertLessEqual(len(node['actions']),3)
    if node['raises']==4:self.assertNotIn('raise_to_100',node['actions'])
   elif node['matched']:self.assertIn(node['value'],(2,5,18,42,100))
 def test_best_response_cannot_condition_on_opponent_private_hand(self):
  # Player0 chooses a matching-pennies action, sees own type only; hidden
  # opponent type is fair. Clairvoyant response would score1, lawful BR scores0.
  nodes=[{'actor':0,'actions':['a','b'],'children':[1,2]},
         {'actor':-1,'actions':[],'children':[]},{'actor':-1,'actions':[],'children':[]}]
  leaf=[0]*4+[1,-1,1,-1]+[-1,1,-1,1]
  r=solve(self.lib,leaf,[.25]*4,nodes,iterations=100,n=2)
  self.assertEqual(r['br_sb_ev_bb'],0);self.assertEqual(r['abstract_nashconv_bb'],0)
 def test_cfr_converges_in_hidden_action_zero_sum_game_and_repeats(self):
  # A single private type at each seat: player0's hidden action would be
  # observable if made a public tree node, so use a Bayesian opponent type
  # encoding two fixed alternatives; player0 should select the higher mean.
  nodes=[{'actor':0,'actions':['a','b'],'children':[1,2]},
         {'actor':-1,'actions':[],'children':[]},{'actor':-1,'actions':[],'children':[]}]
  leaf=[0]*4+[2,0,2,0]+[0,-2,0,-2]
  a=solve(self.lib,leaf,[.25]*4,nodes,iterations=10,n=2);b=solve(self.lib,leaf,[.25]*4,nodes,iterations=1000,n=2)
  c=solve(self.lib,leaf,[.25]*4,nodes,iterations=1000,n=2)
  self.assertLess(b['abstract_nashconv_bb'],a['abstract_nashconv_bb']);self.assertLess(b['abstract_nashconv_bb'],.001)
  self.assertEqual(b['strategy'],c['strategy']);self.assertEqual(b['action_ev_chips'],c['action_ev_chips'])
 def test_both_player_best_responses_match_exhaustive_private_policies(self):
  from itertools import product
  nodes=[{'actor':0,'actions':['a','b'],'children':[1,4]},
   {'actor':1,'actions':['x','y'],'children':[2,3]},
   {'actor':-1,'actions':[],'children':[]},{'actor':-1,'actions':[],'children':[]},
   {'actor':1,'actions':['x','y'],'children':[5,6]},
   {'actor':-1,'actions':[],'children':[]},{'actor':-1,'actions':[],'children':[]}]
  matrices=[[3,-2,1,-4],[-1,4,-3,2],[-2,1,4,-3],[4,-3,-1,2]]
  leaf=[0.]*28
  for v,values in zip((2,3,5,6),matrices):leaf[v*4:(v+1)*4]=values
  p=[.4,.1,.1,.4];r=solve(self.lib,leaf,p,nodes,iterations=4000,n=2)
  sigma=r['strategy']
  def value(s0=None,s1=None):
   out=0
   for i,j in product(range(2),repeat=2):
    for a,b in product(range(2),repeat=2):
     x=(a==s0[i]) if s0 is not None else sigma[a*2+i]
     y=(b==s1[a*2+j]) if s1 is not None else sigma[((1 if a==0 else 4)*3+b)*2+j]
     out+=p[i*2+j]*x*y*matrices[a*2+b][i*2+j]
   return out/2
  self.assertAlmostEqual(r['br_sb_ev_bb'],max(value(s0=x) for x in product(range(2),repeat=2)),places=12)
  self.assertAlmostEqual(r['br_bb_min_sb_ev_bb'],min(value(s1=x) for x in product(range(2),repeat=4)),places=12)
  self.assertAlmostEqual(r['profile_sb_ev_bb'],value(),places=12)
  self.assertLess(r['abstract_nashconv_bb'],.03)
 def test_actual_kernel_replays_and_allin_has_swap_symmetry(self):
  a=kernel(self.lib,samples=2,seed=7001);b=kernel(self.lib,samples=2,seed=7001)
  self.assertEqual(a['mean'],b['mean']);self.assertEqual(a['variance'],b['variance'])
  self.assertTrue(all(-100<=v<=100 for v in a['mean']))
  self.assertTrue(all(v>=0 and math.isfinite(v) for v in a['variance']))
  for i in range(169):
   for j in range(169):self.assertEqual(a['mean'][i*169+j],-a['mean'][j*169+i])
 def test_controllers_only_read_own_cards_and_public_flop(self):
  from gto.abstract.model import ints,IP,ROOT
  import ctypes as C,subprocess,tempfile
  from pathlib import Path
  with tempfile.TemporaryDirectory() as directory:
   source=Path(directory)/'controller.cc'
   source.write_text('#include "'+str(ROOT/'gto/abstract/core.cc')+'"\nextern "C" int decision(const int*h,const int*b){V hole(h,h+2),flop(b,b+3);return int(strong(hole,flop))+2*int(probe(hole,flop));}')
   target=Path(directory)/'controller.so'
   subprocess.run(['c++','-std=c++17','-O2','-shared','-fPIC',str(source),'-I'+str(Path(os.environ['GTO_ABSTRACT_LIBRARY']).parent),'-o',str(target)],check=True)
   controller=C.CDLL(str(target));controller.decision.argtypes=[IP,IP];controller.decision.restype=C.c_int
  rng=random.Random(99)
  for _ in range(200):
   cards=rng.sample(range(52),5);hole=cards[:2];flop=cards[2:]
   strong=rank_five(cards)[0]>=1 or max(sum(c%4==s for c in cards) for s in range(4))>=4
   probe=strong or min(c//4 for c in hole)>max(c//4 for c in flop)
   self.assertEqual(controller.decision(ints(hole),ints(flop)),int(strong)+2*int(probe))
if __name__=='__main__':unittest.main()
