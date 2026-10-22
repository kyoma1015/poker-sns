"""Invalid invocation clocks must not consume the finite retained run budget."""
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from code_worker import Leases
from continuation_recovery import Continuation
class InvocationClock(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'leases.sqlite'
  t={'id':'seed','lane':'A','base_sha':'a'*40,'base_branch':'main','branch':'codex/seed','instruction':'test','allowed_paths':['source.py'],'protected_tests':['test.py'],'test_profile':'python'}
  lease=Leases(self.path);token=lease.claim(t,now=1);lease.finish('seed',token,'implemented',{},now=2)
  anchor={'seed':lease.db.execute('SELECT spec_hash FROM development_jobs WHERE id=?',('seed',)).fetchone()[0]};lease.close();self.store=Continuation(self.path,anchor)
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def reject(self,value):
  with self.assertRaises(ValueError):self.store.reserve_run('bad',now=value)
  self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM continuation_runs').fetchone()[0],0)
  self.assertTrue(self.store.reserve_run('bad',now=2))
 def test_generated_nonfinite_clock_rejected(self):
  with patch('continuation_recovery.time.time',return_value=float('inf')):self.reject(None)
 def test_finite_clocks_keep_existing_contract(self):
  for n,value in enumerate((0,-1,1.25,1e308)):self.assertTrue(self.store.reserve_run('finite-'+str(n),now=value))
  self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM continuation_runs').fetchone()[0],4)
for name,value in [('nan',float('nan')),('positive_inf',float('inf')),('negative_inf',-float('inf')),('true',True),('false',False),('string','100'),('huge_integer',10**400)]:
 def check(self,value=value):self.reject(value)
 setattr(InvocationClock,'test_reject_'+name,check)
