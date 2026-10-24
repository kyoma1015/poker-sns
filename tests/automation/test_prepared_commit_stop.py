"""Cooperative stop must retain prepared work before actual local commit."""
from pathlib import Path
import sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/automation')]
import code_worker as w
import test_prepared_host_boundary as fixture
class CommitStop(unittest.TestCase):
 def run_stop(self,phase):
  f=fixture.PreparedBoundary();f.setUp()
  try:
   with f.guard() as g:
    f.prepare();original=w.validate_and_commit;command=w.command
    def stop():f.f.state.with_suffix('.stop').write_text('stop')
    def validate(*args,**kwargs):
     if phase=='entry':stop()
     return original(*args,**kwargs)
    def run(argv,*args,**kwargs):
     result=command(argv,*args,**kwargs)
     if phase=='tests' and 'unittest' in argv:stop()
     if phase=='staging' and argv[:2]==['git','add']:stop()
     return result
    with patch.object(w,'validate_and_commit',side_effect=validate),patch.object(w,'command',side_effect=run):
     with self.assertRaises(RuntimeError):f.call(g)
    self.assertEqual(command(['git','rev-parse','HEAD'],f.work),f.f.task()['base_sha'])
    status,raw=f.f.store.db.execute("select status,evidence from development_jobs where id='next-a'").fetchone()
    self.assertEqual(status,'running');self.assertIn('prepared_for',raw)
    self.assertEqual((f.work/'src/value.py').read_text(),'VALUE=2\n');self.assertEqual(len(f.saved),1)
  finally:f.tearDown()
 def test_stop_at_validation_entry(self):self.run_stop('entry')
 def test_stop_after_acceptance(self):self.run_stop('tests')
 def test_stop_after_staging_before_commit(self):self.run_stop('staging')
if __name__=='__main__':unittest.main()
