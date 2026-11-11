import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from gto.native.checkpoints import load_verified_checkpoint, verified_snapshot


def uint(n): return struct.pack('<Q', n)
def text(s):
    raw=s.encode(); return uint(len(raw))+raw

def checkpoint(contract='fixture', flags=(1,1,1,1,1), alpha=.1, epsilon=.6, rows=0):
    raw=b'PIDG12S1'+text(contract)+b''.join(uint(i) for i in flags)+struct.pack('<d',alpha)+uint(3)+uint(9)+struct.pack('<d',epsilon)+text('synthetic RNG, not native-valid')+uint(rows)
    return raw+hashlib.sha256(raw).digest()


class Checkpoints(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.path=Path(self.directory.name)/'original.bin'
        self.path.write_bytes(checkpoint())
    def tearDown(self): self.directory.cleanup()
    def test_snapshot_is_separate_and_removed(self):
        before=self.path.read_bytes()
        with verified_snapshot(self.path,'fixture') as (copy,meta):
            self.assertNotEqual(copy,self.path);self.assertEqual(copy.read_bytes(),before)
            self.assertEqual((meta['iteration'],meta['visits'],meta['rows']),(3,9,0))
        self.assertFalse(copy.exists());self.assertEqual(self.path.read_bytes(),before)
    def test_digest_tamper_never_reaches_native(self):
        for index in (10,-1):
            raw=bytearray(checkpoint());raw[index]^=1;self.path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'SHA-256'): load_verified_checkpoint(None,self.path,'fixture')
    def test_contract_mismatch(self):
        with self.assertRaisesRegex(ValueError,'contract'): load_verified_checkpoint(None,self.path,'wrong')
    def test_size_limit(self):
        with self.assertRaisesRegex(ValueError,'size limit'): load_verified_checkpoint(None,self.path,'fixture',max_bytes=1)
    def test_invalid_header_after_valid_digest(self):
        for kwargs in ({'flags':(1,1,1,1,0)},{'flags':(2,1,1,1,1)},{'alpha':float('nan')},{'epsilon':0.},{'rows':1000001}):
            with self.subTest(kwargs=kwargs):
                self.path.write_bytes(checkpoint(**kwargs))
                with self.assertRaises(ValueError):load_verified_checkpoint(None,self.path,'fixture')
    def test_native_structural_validation_propagates(self):
        class Reject:
            def load_binary(self,path,contract):raise RuntimeError('native malformed row')
        with self.assertRaisesRegex(RuntimeError,'native malformed'):load_verified_checkpoint(Reject(),self.path,'fixture')
    def test_verified_copy_survives_original_change(self):
        original=self.path
        class Verify:
            def load_binary(self,path,contract):
                original.write_bytes(b'changed after snapshot')
                assert Path(path).read_bytes()==checkpoint()
        self.assertEqual(load_verified_checkpoint(Verify(),self.path,'fixture')['iteration'],3)
    def test_empty_truncated_or_extra_bytes_rejected(self):
        for raw in (b'',checkpoint()[:20],checkpoint()[:-1],checkpoint()+b'x'):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):load_verified_checkpoint(None,self.path,'fixture')

if __name__=='__main__':unittest.main()
