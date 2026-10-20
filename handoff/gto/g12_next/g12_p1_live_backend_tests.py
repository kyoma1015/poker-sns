import hashlib,os,pathlib,sqlite3,tempfile,unittest
from g12_p1_live_backend import LiveBackend
class LiveTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=pathlib.Path(self.t.name)/'store.db';self.b=LiveBackend(self.p)
 def tearDown(self):self.b.close();self.t.cleanup()
 def test_initial_and_resume(self):
  self.assertIsNone(self.b.initialize('game1'))
  self.b.begin();self.b.commit([(b'a',b'payload')],'rngtext',7,21)
  self.assertEqual(self.b.initialize('game1'),(7,21,'rngtext'))
  self.assertEqual(self.b.get(b'a'),b'payload')
 def test_mismatch_rejected(self):
  self.b.initialize('game1')
  with self.assertRaises(ValueError):self.b.initialize('game2')
 def test_rollback(self):
  self.b.initialize('game1');self.b.begin();self.b.commit([(b'a',b'original')],'rng',1,3)
  self.b.begin();self.b.db.execute('UPDATE rows SET data=? WHERE k=?',(b'wrong',b'a'));self.b.rollback()
  self.assertEqual(self.b.get(b'a'),b'original')
 def test_corrupt_row(self):
  self.b.initialize('game1');self.b.begin();self.b.commit([(b'a',b'original')],'rng',1,3)
  self.b.db.execute('UPDATE rows SET data=? WHERE k=?',(b'wrong',b'a'))
  with self.assertRaises(ValueError):self.b.get(b'a')
 def test_incomplete_meta(self):
  self.b.initialize('game1')
  self.assertIsNone(self.b.initialize('game1'))
  self.b.db.execute('INSERT INTO meta VALUES (?,?)',('iteration','5'))
  with self.assertRaises(ValueError):self.b.initialize('game1')
 def test_no_partial_commit(self):
  self.b.initialize('game1');self.b.begin()
  self.b.db.execute('INSERT INTO rows VALUES (?,?,?)',(b'a',b'bad',hashlib.sha256(b'bad').digest()))
  self.b.rollback();self.assertEqual(self.b.count(),0)
 def test_empty_get(self):self.assertIsNone(self.b.get(b'none'))
 def test_no_nested(self):
  self.b.begin()
  with self.assertRaises(RuntimeError):self.b.begin()
 def test_double_commit(self):
  self.b.begin();self.b.commit([],'rng',1,0)
  with self.assertRaises(RuntimeError):self.b.commit([],'rng',2,0)
if __name__=='__main__':unittest.main(verbosity=2)
