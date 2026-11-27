"""Lossless public-stream shards, RNG/next-step replay and tamper rejection."""
import hashlib,json,random,tempfile,unittest
from pathlib import Path
import numpy as np
from gto.qualification import active_chance as ac,public_chance_solver as pcs,stream_sampling as ss,stream_features,public_stream_study as store
from gto.qualification.policy import sha

class Checkpoint(unittest.TestCase):
    def test_shards_restore_rng_optimizer_and_reject_modified_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib=ac.build(str(Path(tmp)/'build'));nodes=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5),dict(actor=-1,children=[],round=3,c0=-3,c1=6)]
            q=ss.Game(lib,nodes,[dict(pcs.block(lib,[0,5,10,15,20],1.),stratum=(0,0,0))]);q.step();rng=random.Random(123);rng.random()
            identity=dict(seed=123,nodes=nodes,splits=[],sources={str(Path(__file__)):sha(Path(__file__))},binary_sha256=sha(Path(lib._name)),feature_binary_sha256=sha(Path(stream_features.build()._name)))
            folder=Path(tmp)/'checkpoint';store.save(q,folder,identity,rng);r,_,rrng=store.restore(folder)
            for name in ('R','A','prior','visits'):np.testing.assert_array_equal(getattr(q,name),getattr(r,name))
            self.assertEqual(rng.getrandbits(64),rrng.getrandbits(64));q.step();r.step()
            for name in ('R','A','visits'):np.testing.assert_array_equal(getattr(q,name),getattr(r,name))
            shard=next(folder.glob('R-*.npy.zst'));shard.write_bytes(shard.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError,'optimizer shard SHA'):store.restore(folder)
