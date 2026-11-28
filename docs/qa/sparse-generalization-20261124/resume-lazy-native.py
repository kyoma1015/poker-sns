import gzip,json,time
from pathlib import Path
from gto.qualification.build import load
from gto.qualification.multiplayer_joint import SparseJoint
from gto.native.training import NativeGame
from gto.qualification.evaluate import atomic
_,native=load('/tmp/poker-public-response-build');root=Path('docs/qa/sparse-generalization-20261124/multiplayer-lazy');rows=[]
for n in (6,9):
 for seed in (17124101,17124102):
  start=time.monotonic();game=NativeGame([100-20*(p%3) for p in range(n)],bba=2,rake_num=1,rake_den=20);state=json.loads(gzip.decompress((root/f'{n}max-{seed}-final.json.gz').read_bytes()));digests=[]
  for _ in range(2):
   q=SparseJoint(native,game,seed=seed,average_mode='lazy');q.restore(state);q.step();digests.append(q.state()['digest'])
  assert digests[0]==digests[1];rows.append(dict(players=n,seed=seed,source_checkpoint_digest=state['digest'],identical_next_checkpoint_digest=digests[0],seconds=time.monotonic()-start,no_automatic_resume=True))
atomic(root/'actual-resume.json',dict(rows=rows))
