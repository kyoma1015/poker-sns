import itertools,json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import flop_conditional as f
from gto.abstract.model import build,load,rank,classes
from gto.abstract.precision_runouts import build as build_precision,exact
from gto.abstract.precision_archive import unpack
from gto.native.ev_audit import rank_five

class ConditionalFlopTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.lib=build_precision(Path(cls.temp.name)/'precision');cls.reference=load(build(Path(cls.temp.name)/'reference'))
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_all990_against_independent_rank_and_swapped_seat(self):
  holes=(48,49,44,45);flop=(0,17,30);counts=[0,0,0]
  deck=[c for c in range(52) if c not in holes+flop]
  for tr in itertools.combinations(deck,2):
   a=rank(self.reference,holes[:2]+flop+tr);b=rank(self.reference,holes[2:]+flop+tr);counts[0 if a>b else 1 if a==b else 2]+=1
  self.assertEqual(exact(self.lib,holes,flop),tuple(counts));self.assertEqual(sum(counts),990)
  self.assertEqual(exact(self.lib,holes[2:]+holes[:2],flop),tuple(reversed(counts)))
 def test_exact_uniform_combo_mass_after_public_blockers(self):
  groups,w,counts=f.posterior((48,21,3),[1.]*169,[1.]*169)
  self.assertEqual(sum(map(len,groups)),math.comb(49,2))
  self.assertEqual(sum(counts),math.comb(49,2)*math.comb(47,2))
  self.assertAlmostEqual(sum(w),1)
  for a,b in zip(w,counts):self.assertAlmostEqual(a,b/sum(counts))
 def test_nonuniform_history_and_private_removal(self):
  v=[0.]*169;v[0]=.8;v[1]=.2;hero=[1.]*169;flop=(48,21,3)
  groups,w,_=f.posterior(flop,hero,v);m=[]
  for group in groups:
   m.append(sum(v[j] for a in group for j in (0,1) for b in groups[j] if not set(a)&set(b)))
  z=sum(m)
  for a,b in zip(w,m):self.assertAlmostEqual(a,b/z)
 def test_invalid_flops_and_zero_reach(self):
  for flop in ((0,0,1),(0,1),(0,1,52),(0,1,True)):
   with self.assertRaises(ValueError):f.legal_groups(flop)
  with self.assertRaises(ValueError):f.posterior((0,1,2),[0.]*169,[1.]*169)
  with self.assertRaises(ValueError):exact(self.lib,(0,1,2,3),(3,4,5))
 def test_strength_predicate_independent_five_card_evaluator(self):
  import random
  rng=random.Random(22)
  for _ in range(200):
   cs=tuple(rng.sample(range(52),5));expected=rank_five(cs)[0]>=1 or max(sum(c%4==s for c in cs) for s in range(4))>=4
   self.assertEqual(f.strong(cs[:2],cs[2:]),expected)
 def test_provider_observes_only_own_holes_and_legal_bankroll(self):
  observed=[]
  def provider(obs):observed.append(obs);return f.Policy(1,1,1,1)
  value=f.new_controller(.7,(48,49),(44,45),(0,17,30),1,42,29,provider)
  self.assertTrue(-50<=value<=50);self.assertEqual(observed[0].holes,(48,49));self.assertEqual(observed[1].holes,(44,45))
  self.assertFalse(hasattr(observed[0],'opponent_holes'))
 def test_seed_reproducibility_actual_frozen_policy_and_sampling_scope(self):
  packet=json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text());_,policies=unpack(packet)
  a=f.evaluate(self.lib,policies['flop_controller'],'vs_4bet',(35,31,27),samples=2,seed=66)
  b=f.evaluate(self.lib,policies['flop_controller'],'vs_4bet',(35,31,27),samples=2,seed=66)
  self.assertEqual(a,b);self.assertEqual(len(a['rows']),169);self.assertEqual(a['runout_sampling_error'],0)
  self.assertTrue(a['equity_is_conditioned_on_specific_flop']);self.assertFalse(a['full_game_gto_verified'])
  self.assertAlmostEqual(sum(r['posterior_probability'] for r in a['rows']),1)
  self.assertAlmostEqual(sum(r['posterior_probability']*r.get('delta_bb',0) for r in a['rows']),a['aggregate']['delta']['ev_bb'])
 def test_exact_single_pair_posterior_sampling_and_known_tie(self):
  # Fix actual concrete cards via groups; exact enumeration replaces any MC runout.
  groups=[[] for _ in range(169)];groups[0]=[(48,49)];groups[1]=[(44,45)]
  deals,cdf,total=f.candidates(groups,0,[0.,1.]+[0.]*167)
  self.assertEqual(deals,[(48,49,44,45)]);self.assertEqual(cdf,[1]);self.assertEqual(total,1)
  # Royal-flush board runout subset is a tie regardless of private cards.
  for a,b in (((0,1),(4,5)),):
   self.assertEqual(rank(self.reference,a+(32,36,40,44,48)),rank(self.reference,b+(32,36,40,44,48)))

if __name__=='__main__':unittest.main()
