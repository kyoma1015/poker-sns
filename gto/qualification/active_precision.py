"""Reuse the existing conditional stratified EV certificate on the bounded policy."""
import argparse,json
from pathlib import Path
from gto.qualification import active_native,active_study,integrated_study as old,sparse_solver
from gto.qualification.build import load
from gto.qualification.integrated_precision import certificate

def run(seed):
    rules,native=load('/tmp/native-qualification');m=sparse_solver.load(next(Path('/tmp/sparse').glob('*.so')));w,origin=sparse_solver.warm(m,seed);fallback=old.old_policy(m,w,origin,seed);fallback.native=native
    q=active_native.restore(seed,'bounded',fallback)
    receipt=json.loads((active_study.ROOT/str(seed)/'native-confirm-32768/result.json').read_text())
    if q.policy_digest!=receipt['reports'][-1]['digest']:raise ValueError('native/EV policy digest mismatch')
    out=active_study.ROOT/str(seed)/'precision'
    out.mkdir(exist_ok=True)
    certificate(q,rules,m,out,seed,context_seconds=30)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);run(a.parse_args().seed)
