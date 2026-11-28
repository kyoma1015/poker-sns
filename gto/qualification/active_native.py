"""Predeclared native confirmation on fresh worlds, never candidate selection."""
import argparse,gc,json,time
from pathlib import Path
import numpy as np
from gto.qualification import active_chance as ac,active_policy,active_study
from gto.qualification import integrated_audit_native as previous, integrated_study as old
from gto.qualification import sparse_solver,public_chance_solver as pcs
from gto.qualification.build import load
from gto.qualification.sparse_study import rb_value,samples,Force
from gto.qualification.action_native import interval
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed
from gto.qualification.policy import sha
from gto.native.training import NativeGame

def restore(seed,mode,fallback):
    from gto.qualification.active_resume import restore as restore_bundle
    q,identity=restore_bundle(active_study.ROOT/str(seed)/mode,'/tmp/active-eval-'+str(seed)+'-'+mode)
    return active_policy.Policy(q,fallback,identity)

def run(seed,n=8192):
    out=active_study.ROOT/str(seed)/'native-final'
    if out.exists():raise FileExistsError('independent final receipt is immutable')
    out.mkdir(parents=True);rules,native=load('/tmp/native-qualification');m=sparse_solver.load(next(Path('/tmp/sparse').glob('*.so')));w,origin=sparse_solver.warm(m,seed);fallback=old.old_policy(m,w,origin,seed);fallback.native=native
    previous_policy,_,_=previous.restore(seed);policies=[fallback,previous_policy,restore(seed,'refine',fallback),restore(seed,'bounded',fallback)];names=['protected_sparse','previous_signed_last','refined_884','bounded_2939'];ids=[p.policy_digest for p in policies]
    baseline=[{r:{} for r in range(4)} for p in policies];values=[[[] for _ in range(8)] for p in policies];game=NativeGame([100,100]);st=time.monotonic()
    for k,(deck,tape) in enumerate(samples(17140901,n)):
        if time.monotonic()-st>900:raise RuntimeError('native 900s wall stop; incomplete checkpoint not final evidence')
        for policy_index,(p,rows) in enumerate(zip(policies,values)):
            for arm_index,(arm,v) in enumerate(zip([p,*old.probes(p),Force(p,16)],rows)):
                before={r:dict(c) for r,c in getattr(p,'stats',{}).items()} if arm_index==0 else {}
                v.append(rb_value(arm,native,game,deck,tape,m))
                if arm_index==0:
                    for r,c in getattr(p,'stats',{}).items():
                        for key,value in c.items():baseline[policy_index][r][key]=baseline[policy_index][r].get(key,0)+value-before.get(r,{}).get(key,0)
        if (k+1)%2048==0:
            print(json.dumps(dict(seed=seed,worlds=k+1,seconds=time.monotonic()-st)),flush=True)
            compressed(out/'progress.json.gz',dict(worlds=k+1,evaluation_seed=17140901,digests=ids,values=values,complete=False))
    reports=[];delta=.001/100
    for policy_index,(name,p,vs) in enumerate(zip(names,policies,values)):
        reports.append(dict(name=name,digest=p.policy_digest,EV=interval(vs[0],-50,50,delta),deviations={kind:interval([sign*(x-y) for x,y in zip(row,vs[0])],-100,100,delta) for kind,sign,row in zip(old.KINDS+['open7'],old.SIGNS+[1],vs[1:])},baseline_coverage=baseline[policy_index],all_arms_coverage=getattr(p,'stats',None)))
    paired=[]
    for j in (2,3):
        for control in (0,1):
            paired.append(dict(candidate=names[j],control=names[control],EV=interval([a-b for a,b in zip(values[j][0],values[control][0])],-100,100,delta),river_jam_gain_difference=interval([(b-a)-(d-c) for a,b,c,d in zip(values[j][4],values[j][0],values[control][4],values[control][0])],-200,200,delta)))
    assert ids==[p.policy_digest for p in policies]
    compressed(out/'values.json.gz',dict(evaluation_seed=17140901,digests=ids,values=values))
    atomic(out/'result.json',dict(n=n,seed=seed,evaluation_seed=17140901,selection=False,reports=reports,paired=paired,seconds=time.monotonic()-st,source_sha256=sha(Path(__file__)),adapter_sha256=sha(Path(active_policy.__file__)),resume_sha256=sha(Path(__file__).with_name('active_resume.py')),family_confidence=.999,events=100,full_native_BR_upper=None,formal_acceptance=0,verified_RFI=0,verified_3bet=0))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--n',type=int,default=8192);a=p.parse_args();run(a.seed,a.n)
