import json,tempfile,gc,time
from pathlib import Path
from gto.qualification import sparse_solver as s
from gto.qualification.build import load
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
rules,_=load('/tmp/poker-public-response-build');module=s.load('/tmp/sparse-sharing-final-build/_sparse_qualification.cpython-312-x86_64-linux-gnu.so');root=Path('docs/qa/sparse-generalization-20261124');records=[]
for seed in (17120101,17120102):
 begin=time.monotonic();folder=root/'hu-final'/str(seed)/'compact';pilot=json.loads((folder/'pilot.json').read_text());meta=json.loads((folder/'best'/'checkpoint.json').read_text());w,origin=s.warm(module,seed);q=s.Solver(module,w,origin,seed+1500000,sharing=True,extra_support=pilot['extra_support'],rows=250000);s.bootstrap_preflop(q,Path('docs/qa/legal-size-20261124/hu-final')/str(seed)/'best',rules);del w;gc.collect()
 for _ in range(meta['iterations']):assert q.step(10.)['complete']
 with tempfile.TemporaryDirectory() as tmp:q.save(tmp);actual=sha(Path(tmp)/'checkpoint.bin')
 assert actual==meta['sha256'];records.append(dict(seed=seed,iterations=q.iteration,exact_reproduced_sha256=actual,seconds=time.monotonic()-begin,scope='same pinned build/warm/RNG, entire selected R/A/prior/RNG binary reproduced without selection callbacks'))
 del q;gc.collect()
atomic(root/'reproduction.json',dict(rows=records))
