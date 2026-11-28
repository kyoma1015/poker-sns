"""Blinded-policy native confirmation; four frozen controllers, paired worlds."""
import argparse,gc,gzip,json,time
from pathlib import Path
import numpy as np
from gto.qualification import integrated_audit as audit,integrated_study as old,fullstreet_solver as f
from gto.qualification.policy import sha
from gto.qualification.sparse_study import archive_restore,rb_value,samples,Force
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.action_native import interval
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed
from gto.native.training import NativeGame
ROOT=audit.ROOT/'native-final'
TAG='coarse-signed-rebased-uniform-baseline-physical'

def restore(seed,which='last'):
    folder=audit.ROOT/'ablations'/str(seed)/TAG/which;meta=json.loads((folder/'checkpoint.json').read_text());i=meta['identity']
    pin=i['audit_source_sha256'];paths=[Path(audit.__file__),*audit.ROOT.rglob('integrated_audit.py')]
    if not any(sha(p)==pin for p in paths):raise ValueError('executed driver source unavailable')
    q,m,rules=audit.make(seed,i['coarse'],i['signed_regret'],'warm_initialization' in i,i['linear_average'],i['baseline'],i['lazy_rows'])
    q.identity.update(physical_BR_primary=i['physical_BR_primary'],audit_source_sha256=pin);archive_restore(q,folder);return q,m,rules

def evaluate(seed,n=16384):
    folder=ROOT/str(seed)
    if folder.exists() and any(folder.iterdir()):raise FileExistsError('never overwrite final')
    folder.mkdir(parents=True,exist_ok=True);q,m,rules=restore(seed);legacy,_,_=audit.historical(seed,'best');w,origin=old.s.warm(m,seed);sparse=old.old_policy(m,w,origin,seed);sparse.native=q.native
    base=load_policy('/tmp/native-qualification',f.old.ARTIFACT);p=Path('docs/qa/public-chance-20261125/warm')/str(seed);meta=json.loads((p/'policy.json').read_text());arrays=np.load(p/'policy.npz');pi=arrays['pi'];mass=(arrays['average_mass']>0).astype(np.uint8);arrays.close();pcs=f.Policy(meta,pi,mass,q.ranklib,base);pcs._digest=meta['policy_digest']
    audit.archive_save(legacy,audit.ROOT/'historical-migrated'/str(seed));policies=[sparse,pcs,legacy,q];names=['old_sparse','old_PCS','old_integrated_t0','new_trained_last'];ids=[p.policy_digest for p in policies];track=old.Track(q);values=[[[] for _ in range(8)] for p in policies];start=time.monotonic();game=NativeGame([100,100])
    for k,(deck,tape) in enumerate(samples(17138701,n)):
        if time.monotonic()-start>360:raise RuntimeError('final evaluation wall budget, no completed receipt')
        for j,p in enumerate(policies):
            arms=[track if j==3 else p,*old.probes(p),Force(p,16)]
            for arm,v in zip(arms,values[j]):v.append(rb_value(arm,q.native,game,deck,tape,m))
        if (k+1)%2048==0:print(json.dumps(dict(seed=seed,worlds=k+1,seconds=time.monotonic()-start)),flush=True)
    kinds=old.KINDS+['open7'];signs=old.SIGNS+[1];delta=.001/200;reports=[]
    for name,p,v in zip(names,policies,values):reports.append(dict(name=name,digest=p.policy_digest,EV=interval(v[0],-50,50,delta),deviations={key:interval([sgn*(a-b) for a,b in zip(row,v[0])],-100,100,delta) for key,sgn,row in zip(kinds,signs,v[1:])}))
    paired=[dict(control=names[j],EV=interval([a-b for a,b in zip(values[3][0],values[j][0])],-100,100,delta),open3p5_gain=interval([(a-b)-(c-d) for a,b,c,d in zip(values[3][1],values[3][0],values[j][1],values[j][0])],-200,200,delta)) for j in range(3)]
    assert ids==[p.policy_digest for p in policies];compressed(folder/'values.json.gz',dict(seed=17138701,policy_digests=ids,values=values))
    atomic(folder/'result.json',dict(seed=seed,n=n,evaluation_seed=17138701,experimental_candidate='predeclared trained last, selectedt0 was NOT renamed as learning; no final-data reselection',reports=reports,paired=paired,coverage=track.count,seconds=time.monotonic()-start,source_sha256=sha(Path(__file__)),family_confidence=.999,events=200,full_native_BR_upper=None,formal_acceptance=0,ordinary_registry_admission=False))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);x=a.parse_args();evaluate(x.seed)
