import json,time,gc,tempfile
from pathlib import Path
from gto.qualification import sparse_solver as s,sparse_study as st
from gto.qualification.build import load
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
rules,_=load('/tmp/poker-public-response-build');m=s.load('/tmp/sparse-sharing-final-build/_sparse_qualification.cpython-312-x86_64-linux-gnu.so');root=Path('docs/qa/sparse-generalization-20261124');rows=[]
for seed in (17120101,17120102):
 begin=time.monotonic();folder=root/'hu-final'/str(seed)/'compact';meta=json.loads((folder/'pilot.json').read_text());w,origin=s.warm(m,seed);q=s.Solver(m,w,origin,seed+1500000,sharing=True,extra_support=meta['extra_support'],rows=250000);s.bootstrap_preflop(q,Path('docs/qa/legal-size-20261124/hu-final')/str(seed)/'best',rules);del w;gc.collect();st.archive_restore(q,folder/'best');frozen=q.policy_digest
 hashes=[];complete=[]
 with tempfile.TemporaryDirectory() as tmp:
  for name in ('a','b'):
   st.archive_restore(q,folder/'best');complete.append(q.step(10.)['complete']);q.save(Path(tmp)/name);hashes.append(sha(Path(tmp)/name/'checkpoint.bin'))
 assert hashes[0]==hashes[1]
 rows.append(dict(seed=seed,source_policy_digest=frozen,complete=complete,identical_next_checkpoint_sha256=hashes[0],seconds=time.monotonic()-begin,automatic_resume=False));del q;gc.collect()
atomic(root/'resume.json',dict(rows=rows))
