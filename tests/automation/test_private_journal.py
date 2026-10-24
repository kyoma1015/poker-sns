"""Owned temporary journal only; no real receipts or retained state."""
import fcntl,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
class JournalTests(unittest.TestCase):
 def setUp(self):
  from private_journal import PrivateJournal
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'private';self.j=PrivateJournal(self.root)
 def tearDown(self):self.tmp.cleanup()
 def test_roundtrip_private_and_immutable(self):
  digest=self.j.append({'phase':'saved'},expected_head=None)
  self.assertEqual(self.j.read(expected_head=digest),[{'phase':'saved'}]);self.assertEqual(self.root.stat().st_mode&0o777,0o700)
  with self.assertRaises(ValueError):self.j.append({'phase':'stale'},expected_head=None)
  self.assertEqual(len(self.j.read(expected_head=digest)),1)
 def test_tamper_rejected(self):
  digest=self.j.append({'phase':'saved'},expected_head=None);p=self.root/'0000000000000000.json';p.write_text(p.read_text().replace('saved','other'))
  with self.assertRaises(ValueError):self.j.read(expected_head=digest)
 def test_missing_reordered_and_truncated_rejected(self):
  a=self.j.append({'n':0},expected_head=None);b=self.j.append({'n':1},expected_head=a)
  p=self.root/'0000000000000000.json';original=p.read_bytes();p.unlink()
  with self.assertRaises(ValueError):self.j.read(expected_head=b)
  p.write_bytes(original);p.chmod(0o600);q=self.root/'0000000000000001.json';q.write_bytes(q.read_bytes()[:12])
  with self.assertRaises(ValueError):self.j.read(expected_head=b)
 def test_partial_publish_and_processdeath_leave_prior_head(self):
  digest=self.j.append({'n':0},expected_head=None)
  code="import os,sys;from pathlib import Path;p=Path(sys.argv[1])/'.pending-crash';f=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(f,b'{partial');os.fsync(f);os._exit(23)"
  r=subprocess.run([sys.executable,'-B','-c',code,str(self.root)],timeout=5);self.assertEqual(r.returncode,23)
  self.assertEqual(self.j.read(expected_head=digest),[{'n':0}]);self.assertTrue((self.root/'.pending-crash').exists())
 def test_processdeath_after_publish_requires_external_reconciliation(self):
  code="import os,sys;sys.path.insert(0,sys.argv[1]);from private_journal import PrivateJournal;j=PrivateJournal(sys.argv[2]);os.unlink=lambda *a,**k:os._exit(24);j.append({'n':1},expected_head=None)"
  result=subprocess.run([sys.executable,'-B','-c',code,str(ROOT/'scripts'),str(self.root)],timeout=5)
  self.assertEqual(result.returncode,24)
  with self.assertRaises(ValueError):self.j.read(expected_head=None)
  self.assertEqual(len(list(self.root.glob('[0-9]*.json'))),1)
  self.assertEqual(len(list(self.root.glob('.pending-*'))),1)
 def test_lock_timeout_is_bounded_and_permissions_rechecked(self):
  fd=os.open(self.root/'.lock',os.O_RDWR|os.O_CREAT,0o600);fcntl.flock(fd,fcntl.LOCK_EX)
  try:
   started=time.monotonic()
   with self.assertRaises(TimeoutError):self.j.append({'n':0},expected_head=None,lock_timeout=0.02)
   self.assertLess(time.monotonic()-started,0.5)
  finally:os.close(fd)
  self.root.chmod(0o755)
  with self.assertRaises(ValueError):self.j.read(expected_head=None)
  self.root.chmod(0o700)
 def test_crossprocess_same_head_one_winner(self):
  code="import sys;sys.path.insert(0,sys.argv[1]);from private_journal import PrivateJournal;j=PrivateJournal(sys.argv[2]);j.append({'n':1},expected_head=None)"
  workers=[subprocess.Popen([sys.executable,'-B','-c',code,str(ROOT/'scripts'),str(self.root)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) for _ in range(4)]
  self.assertEqual(sorted(p.wait(timeout=5) for p in workers),[0,1,1,1])
  self.assertEqual(len(list(self.root.glob('[0-9]*.json'))),1)
 def test_reordered_records_and_truncated_tail(self):
  a=self.j.append({'n':0},expected_head=None);b=self.j.append({'n':1},expected_head=a)
  p=self.root/'0000000000000000.json';q=self.root/'0000000000000001.json';x=p.read_bytes();y=q.read_bytes();p.write_bytes(y);q.write_bytes(x)
  with self.assertRaises(ValueError):self.j.read(expected_head=b)
  p.write_bytes(x);q.unlink()
  with self.assertRaises(ValueError):self.j.read(expected_head=b)
 def test_nonfinite_and_symlink_refused(self):
  with self.assertRaises(ValueError):self.j.append({'n':float('nan')},expected_head=None)
  link=Path(self.tmp.name)/'link';link.symlink_to(self.root,target_is_directory=True)
  from private_journal import PrivateJournal
  with self.assertRaises(ValueError):PrivateJournal(link)
if __name__=='__main__':unittest.main()
