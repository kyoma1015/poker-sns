"""Strict manual PCS checkpoint/RNG replay; never an automatic restart service."""
import argparse,gc,json,random,tempfile
from pathlib import Path
import numpy as np
from gto.qualification import public_chance_solver as p
from gto.qualification.policy import sha
from gto.qualification.native_mccfr import digest
from gto.qualification.evaluate import atomic


def tuples(x):return tuple(tuples(v) for v in x) if isinstance(x,list) else x

def verify(seed,root):
    root=Path(root);folder=root/'warm'/str(seed);meta=json.loads((folder/'policy.json').read_text())
    for path,expected in meta['PCS_sources'].items():
        source=Path(path)
        if source.name=='public_chance_study.py' and sha(source)!=expected:
            choices=[root/'early-eight/driver-v1.py',root/'pilot-driver-v2.py',root/'pilot-driver-v3.py']
            source=next((x for x in choices if x.exists() and sha(x)==expected),source)
        if sha(source)!=expected:raise ValueError('source identity mismatch: '+str(source))
    lib=p.build('/tmp/pcs')
    if sha(Path(lib._name))!=meta['binary_sha256']:raise ValueError('build identity mismatch; explicit migration required')
    result=json.loads((folder/'result.json').read_text());checkpoint=folder/'best.npz'
    if meta['policy_digest']!=digest({k:v for k,v in meta.items() if k!='policy_digest'}) or result['policy_digest']!=meta['policy_digest'] or sha(folder/'policy.npz')!=meta['array_sha256']:
        raise ValueError('policy/result identity mismatch')
    if sha(checkpoint)!=result['checkpoint_sha256']:raise ValueError('checkpoint digest')
    state=json.loads((folder/'best-rng.json').read_text())
    if state['iterations']!=meta['iterations']:raise ValueError('best/RNG step mismatch')
    parent=Path('docs/qa/fullstreet-generalization-20261121/corrected')/str(seed)/'policy-best.npz'
    if sha(parent)!=meta['parent_array_sha256']:raise ValueError('warm policy identity')
    with np.load(parent) as d:prior=d['pi'].astype(np.float32)
    with tempfile.TemporaryDirectory() as stage:
        rstates=[]
        for i in range(2):
            q=p.Game(lib,meta['nodes'],[p.block(lib,[0,5,10,15,20])],prior=prior);q.restore(checkpoint)
            rng=random.Random();rng.setstate(tuples(state['rng_state']))
            q.use_blocks([p.draw(lib,rng)]);q.step();q.save(Path(stage)/f'{i}.npz');rstates.append(rng.getstate());del q;gc.collect()
        with np.load(Path(stage)/'0.npz') as a,np.load(Path(stage)/'1.npz') as b:
            for k in a.files:np.testing.assert_array_equal(a[k],b[k])
        assert rstates[0]==rstates[1]
    record=dict(seed=seed,source_build_checkpoint_RNG_verified=True,next_step_R_A_visits_RNG_bit_exact=True,checkpoint_sha256=sha(checkpoint),automatic_restart=False)
    atomic(folder/'resume-proof.json',record);return record

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--seed',type=int,required=True);x=a.parse_args();print(verify(x.seed,x.root))
