"""Late stop/liveness observations cannot authorize stale dispatch."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/automation')]
import test_prepared_host_boundary as fixture
class PreparedRace(unittest.TestCase):
 def check_race(self,mutation):
  f=fixture.PreparedBoundary();f.setUp()
  try:
   with f.guard() as g:
    f.prepare();calls=[]
    def observe():
     if not calls:calls.append(1);mutation(f)
     return 'stopped'
    with self.assertRaises(ValueError):f.call(g,observe=observe)
    self.assertEqual(f.calls,0,'dispatch crossed stale task boundary')
  finally:f.tearDown()
 def test_expiry_during_liveness_observation_refuses(self):
  self.check_race(lambda f:f.f.store.db.execute("update development_jobs set expires=0 where id='next-a'"))
 def test_context_corruption_during_liveness_observation_refuses(self):
  self.check_race(lambda f:f.f.store.db.execute("update development_jobs set evidence=NULL where id='next-a'"))
if __name__=='__main__':unittest.main()
