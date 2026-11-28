"""Fixed-policy, same13-board budget public-gradient variance gate."""
import argparse,gc,json,time
from pathlib import Path
import numpy as np
from gto.qualification import public_stream_study as ps,stream_chance as sc,stream_sampling as ss,public_stream_batch as pps
from gto.qualification.evaluate import atomic
from gto.qualification.policy import sha

def run(seed):
    q,meta,_=ps.restore(ps.ROOT/str(seed)/'t180');out=ps.ROOT/str(seed)/'proposal-variance.json'
    if out.exists():raise FileExistsError('preserve variance comparison')
    samples={};timing={}
    for name,draw in [('one_per_stratum',sc.catalog),('target_CDF',pps.catalog)]:
        rows=[];cpu=0.
        for j in range(8):
            tick=time.process_time();bank=draw(q.lib,17157101+j);r=ss.replace_bank(q,bank);r.evaluate_owner(r.policy(False),0);root=r.nodes[0];n=len(root['children']);indices={key[0]:r.base[0]+i*n for i,key in enumerate(r.keys[0])};rows.append(np.stack([r.grad[indices[h]:indices[h]+n] for h in range(169)]));cpu+=time.process_time()-tick;del r;gc.collect()
        samples[name]=np.asarray(rows);timing[name]=cpu
    v={name:float(a.var(axis=0,ddof=1).sum()) for name,a in samples.items()};ratio=v['target_CDF']/v['one_per_stratum'];means=samples['target_CDF'].mean(axis=0)-samples['one_per_stratum'].mean(axis=0)
    atomic(out,dict(seed=seed,repeats=8,boards_per_batch=13,root_CF_variance_trace=v,ratio=ratio,CPU_seconds=timing,mean_difference_L2=float(np.linalg.norm(means)),same_frozen_current_policy=True,adopt_proposal_for_research=ratio<.8,expectation_proof='exact CDF stratum mass plus independent weighted private-vector oracle; finite variance sample is not a bias proof',formal_pass=0,source_sha256=sha(Path(__file__))))
    print(json.dumps(dict(seed=seed,variance=v,ratio=ratio,timing=timing)),flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);run(a.parse_args().seed)
