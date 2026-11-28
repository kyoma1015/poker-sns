"""Fresh confirmation of the predeclared full-support candidate, no retraining.
8192-world diagnostics are not pooled, and no policy is chosen from confirmation.
"""
import argparse,json,time
from gto.qualification import active_native as previous,active_study,integrated_study as old
from gto.qualification import sparse_solver
from gto.qualification.build import load
from gto.qualification.sparse_study import rb_value,samples,Force
from gto.qualification.action_native import interval
from gto.qualification.variance_study import compressed
from gto.qualification.evaluate import atomic
from gto.qualification.policy import sha
from gto.native.training import NativeGame
from pathlib import Path

def run(seed):
    out=active_study.ROOT/str(seed)/'native-confirm-32768'
    if out.exists():raise FileExistsError('preserve independent confirmation')
    out.mkdir(parents=True);rules,native=load('/tmp/native-qualification');m=sparse_solver.load(next(Path('/tmp/sparse').glob('*.so')));w,origin=sparse_solver.warm(m,seed);fallback=old.old_policy(m,w,origin,seed);fallback.native=native
    oldlast,_,_=previous.previous.restore(seed);candidate=previous.restore(seed,'bounded',fallback);policies=[fallback,oldlast,candidate];names=['protected_sparse','previous_signed_last','bounded_2939'];ids=[p.policy_digest for p in policies];values=[[[] for _ in range(8)] for p in policies];game=NativeGame([100,100]);st=time.monotonic()
    for k,(deck,tape) in enumerate(samples(17141901,32768)):
        if time.monotonic()-st>900:raise RuntimeError('900s confirmation stop, incomplete != evidence')
        for p,rows in zip(policies,values):
            for arm,v in zip([p,*old.probes(p),Force(p,16)],rows):v.append(rb_value(arm,native,game,deck,tape,m))
        if (k+1)%8192==0:
            print(json.dumps(dict(seed=seed,worlds=k+1,seconds=time.monotonic()-st)),flush=True)
            compressed(out/'progress.json.gz',dict(complete=False,n=k+1,world_seed=17141901,policy_digests=ids,values=values))
    delta=.001/100;reports=[]
    for name,p,vs in zip(names,policies,values):reports.append(dict(name=name,digest=p.policy_digest,EV=interval(vs[0],-50,50,delta),deviations={kind:interval([sign*(a-b) for a,b in zip(row,vs[0])],-100,100,delta) for kind,sign,row in zip(old.KINDS+['open7'],old.SIGNS+[1],vs[1:])}))
    paired=[]
    for control in (0,1):paired.append(dict(control=names[control],EV=interval([a-b for a,b in zip(values[2][0],values[control][0])],-100,100,delta),river_jam_gain_difference=interval([(b-a)-(d-c) for a,b,c,d in zip(values[2][4],values[2][0],values[control][4],values[control][0])],-200,200,delta)))
    assert ids==[p.policy_digest for p in policies]
    compressed(out/'values.json.gz',dict(evaluation_seed=17141901,policy_digests=ids,values=values))
    atomic(out/'result.json',dict(seed=seed,n=32768,evaluation_seed=17141901,predeclared_primary='bounded_2939',policy_changed=False,pooled_with_8192=False,reports=reports,paired=paired,seconds=time.monotonic()-st,family_confidence=.999,events=100,source_sha256=sha(Path(__file__)),full_native_BR_upper=None,formal_pass=0))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);run(p.parse_args().seed)
