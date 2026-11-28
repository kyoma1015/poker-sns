import importlib,os,sys,math,tempfile,unittest
from fractions import Fraction as F
from itertools import permutations
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame,checkpoint
from gto.native.checkpoints import load_verified_checkpoint
from gto.native.infoset_export import PolicySnapshot

class Focused(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  root=Path(os.environ['GTO_FOCUSED_MODULE_DIR']);sys.path.insert(0,str(root));sys.path.insert(0,str(root.parent/'targeted'))
  cls.native=importlib.import_module('pokerid_focused');cls.original=importlib.import_module('pokerid_targeted')
 def test_exact_small_deck_probability_and_importance_oracle(self):
  target=[0,1];mass=weighted=F(0);actual_mass=actual_weighted=0.
  for world in permutations(range(6),4):
   p=F(1,360);q=F(1,10)*p+(F(9,10)*F(1,12) if list(world[2:])==target else 0)
   pp,qq=self.native.focused_hole_probabilities(6,list(world),target)
   self.assertAlmostEqual(pp,float(p),places=15);self.assertAlmostEqual(qq,float(q),places=15)
   self.assertGreater(qq,0);self.assertLessEqual(pp/qq,10+1e-12)
   value=world[0]-world[2];mass+=q;weighted+=q*(p/q)*value
   actual_mass+=qq;actual_weighted+=qq*(pp/qq)*value
  self.assertEqual(mass,1);self.assertEqual(weighted,0)
  self.assertAlmostEqual(actual_mass,1,places=12);self.assertAlmostEqual(actual_weighted,0,places=12)
 def test_production_draws_exclude_cards_reproduce_and_keep_uniform_support(self):
  draws=self.native.focused_hole_draws(17,6,[0,1],20000)
  self.assertEqual(draws,self.native.focused_hole_draws(17,6,[0,1],20000))
  count=0;weights=0
  for world in draws:
   self.assertEqual(len(set(world)),4);self.assertTrue(all(0<=c<6 for c in world))
   if world[2:]==[0,1]:count+=1
   p,q=self.native.focused_hole_probabilities(6,world,[0,1]);weights+=p/q
  self.assertAlmostEqual(count/len(draws),.9+.1/30,delta=.015)
  self.assertAlmostEqual(weights/len(draws),1,delta=.1)
  for n,w,t in ((3,[0,1,2,3],[0,1]),(6,[0,1,1,2],[0,1]),(6,[0,1,2,3],[0,0])):
   with self.assertRaises(RuntimeError):self.native.focused_hole_probabilities(n,w,t)
 def test_explicit_parent_migration_preserves_all_rows_and_rng_before_training(self):
  game=NativeGame([100,100]);old=self.original.Solver(game,.6,29,True,True,.1)
  for _ in range(64):old.run_iteration()
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'parent.bin';checkpoint(old,path,'migration-parent-test')
   new=self.native.Solver(game,.6,29,True,True,.1);load_verified_checkpoint(new,path,'migration-parent-test')
   self.assertEqual(old.iteration,new.iteration);self.assertEqual(old.rng_state(),new.rng_state());self.assertEqual(old.keys(),new.keys())
   for key in old.keys():self.assertEqual(old.row(key),new.row(key))
 def test_actual_native_focus_checkpoint_resume_is_exact(self):
  game=NativeGame([100,100]);a=self.native.Solver(game,.6,29,True,True,.1);b=self.native.Solver(game,.6,29,True,True,.1)
  for _ in range(128):a.run_iteration()
  for _ in range(64):b.run_iteration()
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'focused.bin';checkpoint(b,path,'focused-test')
   c=self.native.Solver(game,.6,29,True,True,.1);load_verified_checkpoint(c,path,'focused-test')
   for _ in range(64):c.run_iteration()
   self.assertEqual(a.rng_state(),c.rng_state());self.assertEqual(a.keys(),c.keys())
   for key in a.keys():self.assertEqual(a.row(key),c.row(key))
   self.assertEqual(PolicySnapshot.from_solver(self.native,a).digest,PolicySnapshot.from_solver(self.native,c).digest)
if __name__=='__main__':unittest.main()
