"""Opt-in whole-invocation exclusion, existing budget and cooperative stop."""
from pathlib import Path
import importlib.util,json,subprocess,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
from code_worker import Leases
from continuation_recovery import Continuation
SOURCE=ROOT/'scripts/invocation_guard.py'
def guard_class():
 spec=importlib.util.spec_from_file_location('invocation_guard',SOURCE);m=importlib.util.module_from_spec(spec);sys.modules['invocation_guard']=m;spec.loader.exec_module(m);return m.InvocationGuard
class InvocationGuardTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.sqlite';t={'id':'seed','lane':'A','base_sha':'a'*40,'base_branch':'main','branch':'codex/seed','instruction':'test','allowed_paths':['source.py'],'protected_tests':['test.py'],'test_profile':'python'}
  l=Leases(self.path);token=l.claim(t,now=1);l.finish('seed',token,'implemented',{},now=2);self.anchor={'seed':l.db.execute('SELECT spec_hash FROM development_jobs WHERE id=?',('seed',)).fetchone()[0]};l.close();self.c=Continuation(self.path,self.anchor)
 def tearDown(self):self.c.close();self.tmp.cleanup()
 def guard(self,ident='run-1',**kwargs):return guard_class()(self.c,ident,'/root/host',**kwargs)
 def child(self,ident,crash=False):
  code='''import sys,os,json
sys.path.insert(0,sys.argv[1])
from continuation_recovery import Continuation
from invocation_guard import InvocationGuard
c=Continuation(sys.argv[2],json.loads(sys.argv[3]))
try:
 with InvocationGuard(c,sys.argv[4],'/fixture',enabled=True):
  print('ENTERED',flush=True)
  if sys.argv[5]=='crash':os._exit(0)
except TimeoutError:print('BUSY')
finally:c.close()
'''
  return subprocess.run([sys.executable,'-B','-c',code,str(ROOT/'scripts'),str(self.path),json.dumps(self.anchor),ident,'crash' if crash else 'normal'],text=True,capture_output=True,timeout=5)
 def test_default_disabled_has_no_reservation(self):
  with self.assertRaises(ValueError):
   with self.guard():self.fail('disabled body executed')
  self.assertEqual(self.c.public_checkpoint()['run_count'],0)
 def test_entry_and_duplicate_run_id(self):
  with self.guard(enabled=True) as g:g.check()
  self.assertEqual(self.c.public_checkpoint()['run_count'],1)
  with self.assertRaises(ValueError):
   with self.guard(enabled=True):self.fail('replayed body')
 def test_cross_process_exclusion(self):
  with self.guard(enabled=True):
   r=self.child('run-2');self.assertEqual(r.returncode,0,r.stderr);self.assertIn('BUSY',r.stdout);self.assertNotIn('ENTERED',r.stdout)
  self.assertEqual(self.c.public_checkpoint()['run_count'],1)
 def test_process_death_releases_os_lock_not_old_budget(self):
  guard_class();r=self.child('crashed',crash=True);self.assertEqual(r.returncode,0,r.stderr);self.assertIn('ENTERED',r.stdout)
  with self.guard('next',enabled=True):pass
  self.assertEqual(self.c.public_checkpoint()['run_count'],2)
  with self.assertRaises(ValueError):
   with self.guard('crashed',enabled=True):self.fail('replayed crashed run')
 def test_running_job_even_expired_blocks_new_invocation(self):
  self.c.db.execute("UPDATE development_jobs SET status='running',expires=0 WHERE id='seed'")
  with self.assertRaises(ValueError):
   with self.guard(enabled=True):self.fail('stole unknown-live job')
  self.assertEqual(self.c.public_checkpoint()['run_count'],0)
 def test_emergency_stop_before_and_during_invocation(self):
  stop=self.path.with_suffix('.stop');stop.write_text('stop')
  with self.assertRaises(RuntimeError):
   with self.guard(enabled=True):self.fail('ignored stop')
  self.assertEqual(self.c.public_checkpoint()['run_count'],0);stop.unlink()
  with self.assertRaises(RuntimeError):
   with self.guard(enabled=True) as g:stop.write_text('stop');g.check()
  stop.unlink()
  with self.guard('recovered',enabled=True):pass
 def test_monotonic_deadline(self):
  G=guard_class()
  with patch('invocation_guard.time.monotonic',return_value=100) as clock:
   with self.assertRaises(TimeoutError):
    with G(self.c,'bounded','/root/host',enabled=True,max_seconds=1) as g:clock.return_value=101;g.check()
 def test_invalid_budgets_and_inactive_check(self):
  G=guard_class()
  for value in (0,-1,1801,float('inf'),float('nan'),True):
   with self.subTest(value=value),self.assertRaises(ValueError):
    with G(self.c,'bad','/root/host',enabled=True,max_seconds=value):self.fail('invalid budget')
  with self.assertRaises(ValueError):G(self.c,'inactive','/root/host',enabled=True).check()
  self.assertEqual(self.c.public_checkpoint()['run_count'],0)
 def test_original_finite_limit_reused(self):
  self.c.restrict_remaining_runs(1)
  with self.guard('first',enabled=True):pass
  with self.assertRaises(ValueError):
   with self.guard('second',enabled=True):self.fail('extended original cap')
  self.assertEqual(self.c.public_checkpoint()['run_count'],1)
