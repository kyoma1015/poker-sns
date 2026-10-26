"""EXPECTED LIMITATION: cooperative precommit check is not atomic with Git."""
from pathlib import Path
import sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/automation')]
import code_worker as w
import test_prepared_host_boundary as fixture
class GitStopRaceLimit(unittest.TestCase):
 def test_stop_after_final_check_can_still_commit_expected_limitation(self):
  f=fixture.PreparedBoundary();f.setUp()
  try:
   with f.guard() as guard:
    f.prepare();command=w.command;seen=[]
    def boundary(argv,*args,**kwargs):
     if argv and argv[0]=='git' and 'commit' in argv:
      f.f.state.with_suffix('.stop').write_text('owned race injection');seen.append(True)
     return command(argv,*args,**kwargs)
    with patch.object(w,'command',side_effect=boundary):result=f.call(guard)
    self.assertEqual(seen,[True]);self.assertEqual(result['status'],'implemented_local')
    self.assertNotEqual(command(['git','rev-parse','HEAD'],f.work),f.f.task()['base_sha'])
    self.assertTrue(f.f.state.with_suffix('.stop').exists())
    self.assertFalse(result['real_ai_implementation'])
  finally:f.tearDown()
if __name__=='__main__':unittest.main()
