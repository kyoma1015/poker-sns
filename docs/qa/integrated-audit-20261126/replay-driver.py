import json,hashlib,tempfile,random,gc
from pathlib import Path
from gto.qualification.integrated_audit_native import restore,TAG
from gto.qualification.integrated_audit import ROOT,layout
from gto.qualification.sparse_study import archive_restore
from gto.qualification import public_chance_solver as pcs
from gto.qualification.policy import sha
from gto.qualification.build import load

def tuples(x):return tuple(map(tuples,x)) if isinstance(x,list) else x
proofs=[]
for seed in (17120101,17120102):
 q,m,r=restore(seed);folder=ROOT/'ablations'/str(seed)/TAG/'last';states=[]
 with tempfile.TemporaryDirectory() as d:
  for trial in range(2):
   archive_restore(q,folder);step=q.step(10);assert step['complete'],step;p=Path(d)/'cp';q.core.save(str(p),'same');states.append(sha(p))
 assert states[0]==states[1];proofs.append(dict(kind='native_trained_last',seed=seed,nextstep_SHA256=states[0],exact=True));del q;gc.collect()
rules,_=load('/tmp/native-qualification');nodes,obs=layout(rules)
for seed in (17120101,17120102):
 for mode in ('exact','sample'):
  f=ROOT/'same-game'/str(seed)/mode;record=json.loads((f/'result.json').read_text());assert record['source_sha256']==sha(Path('gto/qualification/integrated_same_game.py'))
  lib=pcs.build('/tmp/same-game-'+str(seed)+'-'+mode);blocks=[pcs.block(lib,b,.5) for b in record['boards']];q=pcs.Game(lib,nodes,[dict(blocks[0],weight=1.)]);states=[];rngstate=json.loads((f/'rng.json').read_text())['state']
  for trial in range(2):
   q.restore(f/'checkpoint.npz');rng=random.Random();rng.setstate(tuples(rngstate));q.use_blocks([dict(blocks[rng.randrange(2)],weight=1.)] if mode=='sample' else blocks);q.step()
   h=hashlib.sha256()
   for x in (q.R,q.A,q.visits):h.update(x.tobytes())
   h.update(str(q.t).encode());h.update(repr(rng.getstate()).encode());states.append(h.hexdigest())
  assert states[0]==states[1]
  identity=dict(source_sha256=record['source_sha256'],native_tree_metadata_sha256=sha(Path('docs/qa/public-chance-20261125/warm/17120101/policy.json')),sources={p:sha(Path(p)) for p in ('gto/qualification/public_chance_solver.py','gto/qualification/public_chance_core.cc','gto/qualification/fullstreet_solver.py','gto/qualification/integrated_br.py')},binary_sha256=sha(Path(lib._name)),checkpoint_sha256=sha(f/'checkpoint.npz'),initial_sha256=sha(f/'initial.npz'),rng_sha256=sha(f/'rng.json'),boards=record['boards'],native_certificate=False,nextstep_exact=True,nextstep_SHA256=states[0]);(f/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
  proofs.append(dict(kind='same_game_'+mode,seed=seed,nextstep_SHA256=states[0],exact=True));del q;gc.collect()
(ROOT/'final-checkpoint-replay.json').write_text(json.dumps(proofs,indent=2)+'\n');print(proofs)
