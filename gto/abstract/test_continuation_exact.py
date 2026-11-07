import ctypes as C,itertools,os,random,tempfile,unittest
from pathlib import Path
from gto.abstract.continuation_exact import build,LP
from gto.abstract.model import ints,rank,load

class ExactController(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.directory=tempfile.TemporaryDirectory();cls.lib=build(Path(cls.directory.name));cls.oracle=load(os.environ['GTO_ABSTRACT_LIBRARY'])
 @classmethod
 def tearDownClass(cls):cls.directory.cleanup()
 def test_board_all10_flops_match_independent_preserved_rank_and_policy(self):
  rng=random.Random(1137)
  def strength(h,f):
   # independent five-card category from preserved native rank encoding
   category=self.oracle.abstract_rank(ints(h+f),5)//15**5
   return category>=1 or max(sum(c%4==s for c in h+f) for s in range(4))>=4
  def lead(h,f):return self.oracle.abstract_rank(ints(h+f),5)//15**5>=2
  for _ in range(50):
   cards=rng.sample(range(52),9);h=cards[:4];board=cards[4:];want=[0]*4
   for flop in itertools.combinations(board,3):
    f=list(flop)
    for variant in (0,1):
     for d in (0,1):
      sb=h[2*d:2*d+2];bb=h[2*(1-d):2*(1-d)+2];bbbet=lead(bb,f) if variant else strength(bb,f);sbcall=strength(sb,f);probe=strength(sb,f) or min(c//4 for c in sb)>max(c//4 for c in f);bbcall=strength(bb,f)
      sign=(rank(self.oracle,sb+board)>rank(self.oracle,bb+board))-(rank(self.oracle,sb+board)<rank(self.oracle,bb+board))
      value=-1 if bbbet and not sbcall else 1 if not bbbet and probe and not bbcall else sign*(2 if bbbet or probe else 1)
      want[variant*2+d]+=value
   actual=(C.c_int64*4)();self.lib.precision_controller_board(ints(h),ints(board),actual);self.assertEqual(list(actual),want)
 def test_complete_board_counts_swap_and_pocket_pair_closed_form(self):
  from gto.abstract.precision_runouts import exact,load as fast_load
  fast=fast_load(os.environ['GTO_PRECISION_LIBRARY'])
  for h in ([48,49,44,45],[48,49,44,40]):
   actual=(C.c_int64*5)();other=(C.c_int64*5)()
   self.assertEqual(self.lib.precision_controller_exact(ints(h),actual),0)
   self.assertEqual(self.lib.precision_controller_exact(ints(h[2:]+h[:2]),other),0)
   w,t,l=exact(fast,h);self.assertEqual(actual[0],w-l);self.assertEqual(other[0],-actual[0]);self.assertEqual(list(actual)[1::2],list(other)[2::2]);self.assertEqual(list(actual)[2::2],list(other)[1::2])
   if h[2]//4==h[3]//4:
    self.assertEqual(actual[1],20*actual[0]);self.assertEqual(actual[2],-20*actual[0]);self.assertEqual(actual[3],actual[1]);self.assertEqual(actual[4],actual[2])

 def test_policy_only_allocation_covers20_suited_types_against_all6_targets(self):
  import json
  from gto.abstract.precision_archive import unpack
  from gto.abstract.continuation_exact import select_cells
  from gto.hand169 import CLASSES
  _,policy=unpack(json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text()))
  cells=select_cells(policy)
  self.assertEqual(len(cells),120);self.assertEqual(len(set(cells)),120)
  self.assertTrue(all(i<=j for i,j in cells))
  targets={'AA','KK','AKo','AKs','QQ','TT'}
  self.assertTrue(all(CLASSES[i] in targets or CLASSES[j] in targets for i,j in cells))
 def test_same_suited_class_has_exact_paired_world_symmetry(self):
  h=[48,44,49,45];actual=(C.c_int64*5)()
  self.assertEqual(self.lib.precision_controller_exact(ints(h),actual),0)
  self.assertEqual(actual[0],0)
  self.assertEqual(actual[1],actual[2]);self.assertEqual(actual[3],actual[4])

if __name__=='__main__':unittest.main()
