"""Fixed fresh paired old-sparse/PCS size confirmation; never candidate selection."""
import gc,json,time
from pathlib import Path
import numpy as np
from gto.qualification import sparse_solver as s,fullstreet_solver as f,public_chance_solver as p
from gto.qualification.integrated_study import old_policy
from gto.qualification.sparse_study import samples,rb_value
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.coupled_evaluate import Extra
from gto.qualification.action_native import interval
from gto.qualification.policy import sha
from gto.qualification.native_mccfr import digest
from gto.qualification.build import load
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame


def run(seed,n=32768):
    root=Path('docs/qa/integrated-solver-20261126');out=root/f'baseline-size-confirmation-{seed}.json'
    if out.exists():raise FileExistsError('preserve completed independent confirmation')
    _,native=load('/tmp/native-qualification');m=s.load(next(Path('/tmp/sparse').glob('*.so')));w,origin=s.warm(m,seed);old=old_policy(m,w,origin,seed);old.native=native
    lib=p.build('/tmp/confirmation-ranks');base=load_policy('/tmp/native-qualification',f.old.ARTIFACT);folder=Path('docs/qa/public-chance-20261125/warm')/str(seed);meta=json.loads((folder/'policy.json').read_text())
    assert sha(folder/'policy.npz')==meta['array_sha256'];assert digest({k:v for k,v in meta.items() if k!='policy_digest'})==meta['policy_digest']
    d=np.load(folder/'policy.npz');pcs=f.Policy(meta,d['pi'],(d['average_mass']>0).astype(np.uint8),lib,base);d.close();pcs._digest=meta['policy_digest'];del w;gc.collect()
    ids=[old.policy_digest,pcs.policy_digest];profiles=[old,Extra(old,'open3p5'),pcs,Extra(pcs,'open3p5')];values=[[] for _ in profiles];st=time.monotonic();game=NativeGame([100,100])
    for i,(deck,tape) in enumerate(samples(17136901,n)):
        if time.monotonic()-st>120:raise RuntimeError('confirmation budget; no partial receipt')
        for q,row in zip(profiles,values):row.append(rb_value(q,native,game,deck,tape,m))
    gains=[[a-b for a,b in zip(values[i+1],values[i])] for i in (0,2)];delta=.001/20
    result=dict(seed=seed,evaluation_seed=17136901,n=n,policy_digests=ids,old_sparse_gain=interval(gains[0],-100,100,delta),old_PCS_gain=interval(gains[1],-100,100,delta),paired_PCS_minus_sparse_gain=interval([a-b for a,b in zip(gains[1],gains[0])],-200,200,delta),seconds=time.monotonic()-st,confidence_family=.999,source_sha256=sha(Path(__file__)),candidate_selection_allowed=False,full_native_BR_upper=None,formal_acceptance=0)
    atomic(out,result);print(json.dumps(result),flush=True)
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);x=a.parse_args();run(x.seed)
