import tempfile,json,time,gc
from pathlib import Path
from gto.qualification import sparse_solver as s
from gto.qualification.sparse_study import archive_restore
from gto.qualification.policy import sha
from gto.qualification.build import load
load('/tmp/poker-public-response-build')
module=s.load('/tmp/sparse-build/_sparse_qualification.cpython-312-x86_64-linux-gnu.so');out=Path('docs/qa/legal-size-20261124');results=[]
for seed in (17120101,17120102):
 start=time.monotonic();w,origin=s.warm(module,seed);q=s.Solver(module,w,origin,seed+1100000);del w;gc.collect();folder=out/'hu-final'/str(seed)/'best';before=sha(folder/'checkpoint.bin.gz');archive_restore(q,folder);frozen=q.policy_digest
 with tempfile.TemporaryDirectory() as tmp:
  complete=[];digests=[]
  for name in ('a','b'):
   archive_restore(q,folder);complete.append(q.step(3.)['complete']);q.save(Path(tmp)/name);digests.append(sha(Path(tmp)/name/'checkpoint.bin'))
  assert all(complete) and digests[0]==digests[1] and before==sha(folder/'checkpoint.bin.gz')
 results.append(dict(seed=seed,policy_digest=frozen,resume_complete=complete,identical_next_checkpoint_sha256=digests[0],original_archive_unchanged=True,seconds=time.monotonic()-start));del q;gc.collect()
(out/'resume.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
