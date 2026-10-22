"""Fixed acceptance for durable non-executable discovery metadata."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from code_worker import Leases
from continuation_recovery import Continuation

class DiscoveryStore(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/'state.sqlite'
  task={'id':'seed','lane':'A','base_sha':'a'*40,'base_branch':'main','branch':'codex/seed','allowed_paths':['source.py'],'protected_tests':['test.py'],'test_profile':'python','instruction':'fixture'}
  lease=Leases(self.path); token=lease.claim(task,now=1); lease.finish('seed',token,'implemented',{},now=2)
  self.anchor={'seed':lease.db.execute('SELECT spec_hash FROM development_jobs WHERE id=?',('seed',)).fetchone()[0]}; lease.close()
  self.store=Continuation(self.path,self.anchor)
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def src(self,lane='A',title='Reproduce queue edge',ref='issue22'):
  return {'lane':lane,'reference':ref,'text':'- [ ] '+title}
 def test_persistence_and_stable_id(self):
  first=self.store.discover([self.src()]); self.assertEqual(len(first),1)
  self.assertRegex(first[0]['id'],r'^[a-f0-9]{64}$'); self.assertEqual(first[0]['status'],'review_required');self.assertIsNone(first[0]['owner'])
  self.store.close();self.store=Continuation(self.path,self.anchor)
  self.assertEqual(self.store.discoveries(),first);self.assertEqual(self.store.discover([self.src()]),first)
 def test_duplicate_batch_and_four_lanes(self):
  rows=self.store.discover([self.src(lane) for lane in 'ABCD']+[self.src()]);self.assertEqual(len(rows),4)
  self.assertEqual(len(self.store.discoveries('C')),1);self.assertEqual(self.store.discoveries('C')[0]['lane'],'C')
 def test_owner_status_survive_rediscovery(self):
  row=self.store.discover([self.src()])[0];self.store.set_discovery(row['id'],owner='/root/a',status='blocked')
  self.store.discover([self.src()]);self.assertEqual(self.store.discoveries()[0]['owner'],'/root/a');self.assertEqual(self.store.discoveries()[0]['status'],'blocked')
  self.store.set_discovery(row['id'],owner=None,status='dismissed');self.assertEqual(self.store.discoveries()[0]['status'],'dismissed')
 def test_untrusted_promotion_and_metadata_ignored(self):
  src=self.src();src.update(owner='attacker',status='implemented',reviewed=True,task={'id':'run'})
  row=self.store.discover([src])[0];self.assertIsNone(row['owner']);self.assertEqual(row['status'],'review_required')
  self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM development_jobs').fetchone()[0],1)
  self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM continuation_runs').fetchone()[0],0)
 def test_invalid_updates_are_atomic(self):
  row=self.store.discover([self.src()])[0]
  for status in ('ready','running','implemented','',None):
   with self.subTest(status=status),self.assertRaises(ValueError):self.store.set_discovery(row['id'],owner='host',status=status)
  for owner in ('x'*81,'bad\nowner','owner name',7):
   with self.subTest(owner=owner),self.assertRaises(ValueError):self.store.set_discovery(row['id'],owner=owner,status='blocked')
  with self.assertRaises(ValueError):self.store.set_discovery('f'*64,owner='host',status='blocked')
  self.assertEqual(self.store.discoveries(),[row])
 def test_missing_state_remains_missing(self):
  missing=self.path.parent/'missing'
  with self.assertRaises(ValueError):Continuation(missing,self.anchor)
  self.assertFalse(missing.exists())
  with self.assertRaises(ValueError):Continuation(self.path,{'seed':'f'*64})
 def test_invalid_lane_filter_rejected(self):
  self.store.discover([self.src()])
  with self.assertRaises(ValueError):self.store.discoveries('unknown')
 def test_concurrent_deduplication(self):
  def run(_):
   other=Continuation(self.path,self.anchor)
   try:return other.discover([self.src()])
   finally:other.close()
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,range(4)))
  self.assertTrue(all(x==rows[0] for x in rows));self.assertEqual(len(self.store.discoveries()),1)
 def test_resource_cap_atomic_batch(self):
  for batch in range(10):self.store.discover([self.src(title=str(batch*100+n)) for n in range(100)])
  self.assertEqual(len(self.store.discoveries()),1000)
  self.assertEqual(len(self.store.discover([self.src(title='0')])),1)
  with self.assertRaises(ValueError):self.store.discover([self.src(title='1000'),self.src(title='1001')])
  self.assertEqual(len(self.store.discoveries()),1000)
 def test_empty_and_bounded_untrusted_extraction(self):
  self.assertEqual(self.store.discover([]),[])
  self.assertEqual(self.store.discover([{'lane':'X','text':'- [ ] nope'}]),[])
  rows=self.store.discover([self.src(title='x'*400,ref='r'*400)]);self.assertEqual(len(rows[0]['title']),200);self.assertEqual(len(rows[0]['reference']),300)
