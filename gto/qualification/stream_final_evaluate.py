"""Frozen last-iterate confirmation; final data never choose a candidate.
4 policies paired on fresh native worlds; finite-catalog BR is NOT native BR.
"""
import argparse,gc,json,time
from pathlib import Path
from gto.qualification import public_stream_final as study,public_stream_study as store,sampling_policy,stream_measure,stream_sampling as ss,stream_chance as sc,active_native,integrated_study as old,sparse_solver,integrated_precision
from gto.qualification.build import load
from gto.qualification.sparse_study import rb_value,samples,Force
from gto.qualification.action_native import interval
from gto.qualification.variance_study import compressed
from gto.qualification.evaluate import atomic
from gto.qualification.policy import sha
from gto.native.training import NativeGame

ROOT=study.ROOT

def run(seed,n):
    folder=ROOT/str(seed);selection=json.load(open(folder/'result.json'));last=selection['last'];out=folder/'independent-final'
    if out.exists():raise FileExistsError('preserve frozen independent confirmation')
    out.mkdir();atomic(out/'freeze.json',dict(checkpoint=last['checkpoint'],selected_before_final_data=True,selection_best=selection['best']['checkpoint'],policy='predeclared last iterate diagnostic; no adoption from final data',native_world_seed=17154101,n=n,final_catalog_seed=17153301+seed))
    rules,native=load('/tmp/native-qualification');m=sparse_solver.load(next(Path('/tmp/sparse').glob('*.so')));w,origin=sparse_solver.warm(m,seed);fallback=old.old_policy(m,w,origin,seed);fallback.native=native
    cold=time.monotonic();q,identity,_=store.restore(last['checkpoint']);restored=time.monotonic();p=sampling_policy.Policy(q,fallback,identity)
    atomic(out/'offline-resource.json',dict(checkpoint_restore_seconds=restored-cold,policy_index_seconds=time.monotonic()-restored,scalar_cells=q.S,public_nodes=len(q.nodes),scope='offline Python/native only; not app SLA; certified cache miss solve latency UNKNOWN'))
    snapshot=ss.replace_bank(q,sc.catalog(q.lib,17153301+seed),average_snapshot=True)
    envelope=stream_measure.refinement_envelope(snapshot);coarse=envelope['coarse'];fine=envelope['fine']
    atomic(out/'finite-final.json',dict(policy_digest=p.policy_digest,coarse=coarse,fine=fine,envelope=envelope,full_native_BR_upper=None,selection=False));del snapshot;gc.collect()
    integrated_precision.certificate(p,rules,m,out,seed,context_seconds=30)
    precision=json.load(open(out/'169-context-EV.json'));range_audit={}
    for name,context in precision['contexts'].items():
        _,_,likelihood,_=integrated_precision.tables(p,rules,context['prefix'])
        range_audit[name]=dict(prefix=context['prefix'],positive_opponent_hand_classes=int((likelihood>0).sum()),max_opponent_history_likelihood=float(likelihood.max()),undefined_zero_posterior_cells=sum(r.get('status')=='UNKNOWN_ZERO_RANGE' for r in context['rows'].values()),zero_hero_reach_but_defined_counterfactual_cells=sum(r.get('status')!='UNKNOWN_ZERO_RANGE' and r['hero_history_reach']==0 for r in context['rows'].values()),interpretation='Zero opponent posterior: conditional EV undefined, not a fabricated0. Zero own reach with nonzero opponent posterior: counterfactual decision EV remains defined.')
    atomic(out/'range-diagnosis.json',dict(policy_digest=p.policy_digest,contexts=range_audit,old_10p5_structural_support_omission=True,new_10p5_downstream_support_present=True,unlearned_backoff_not_quality_proof=True))
    # Evaluate policies one at a time on IDENTICAL deterministic worlds/tapes.
    # This retains paired CRN while avoiding simultaneous large policy indices.
    names=['protected_sparse','previous_signed_last','active_2board_2939','public52_CDF_last'];ids=[None]*4
    values=[[[] for _ in range(8)] for _ in names];coverage=[{r:{} for r in range(4)} for _ in names];game=NativeGame([100,100]);start=time.monotonic()
    for j in (3,0,1,2):
        if j==3:x=p
        elif j==0:x=fallback
        elif j==1:x,_,_=active_native.previous.restore(seed)
        else:x=active_native.restore(seed,'bounded',fallback)
        ids[j]=x.policy_digest
        reference=json.load(open(active_native.active_study.ROOT/str(seed)/'native-confirm-32768'/'result.json'))['reports']
        if j<3:assert ids[j]==reference[j]['digest'], 'protected control digest changed'
        for k,(deck,tape) in enumerate(samples(17154101,n)):
            if time.monotonic()-start>1800:raise RuntimeError('1800s independent confirmation stop; incomplete is not evidence')
            for a,(arm,row) in enumerate(zip([x,*old.probes(x),Force(x,16)],values[j])):
                before={r:dict(c) for r,c in getattr(x,'stats',{}).items()} if a==0 else {}
                row.append(rb_value(arm,native,game,deck,tape,m))
                if a==0:
                    for r,c in getattr(x,'stats',{}).items():
                        for key,v in c.items():coverage[j][r][key]=coverage[j][r].get(key,0)+v-before.get(r,{}).get(key,0)
            if (k+1)%8192==0:
                print(json.dumps(dict(seed=seed,model=names[j],worlds=k+1,seconds=time.monotonic()-start)),flush=True)
                compressed(out/'progress.json.gz',dict(complete=False,model=names[j],n=k+1,world_seed=17154101,digests=ids,values=values))
        assert x.policy_digest==ids[j]
        del arm
        if j==3:del p,q
        del x;gc.collect()
    delta=.001/150;reports=[];paired=[]
    for j,(name,vs) in enumerate(zip(names,values)):
        reports.append(dict(name=name,digest=ids[j],EV=interval(vs[0],-50,50,delta),deviations={kind:interval([sign*(a-b) for a,b in zip(row,vs[0])],-100,100,delta) for kind,sign,row in zip(old.KINDS+['open7'],old.SIGNS+[1],vs[1:])},baseline_coverage=coverage[j]))
    for j in range(3):
        paired.append(dict(control=names[j],EV=interval([a-b for a,b in zip(values[3][0],values[j][0])],-100,100,delta),deviation_gain_difference={kind:interval([sign*((a-b)-(c-d)) for a,b,c,d in zip(row,values[3][0],crow,values[j][0])],-200,200,delta) for kind,sign,row,crow in zip(old.KINDS+['open7'],old.SIGNS+[1],values[3][1:],values[j][1:])}))
    compressed(out/'values.json.gz',dict(world_seed=17154101,policy_digests=ids,values=values))
    atomic(out/'result.json',dict(seed=seed,n=n,evaluation_seed=17154101,reports=reports,paired=paired,seconds=time.monotonic()-start,family_confidence=.999,events=150,policy_changed=False,selection=False,full_native_BR_upper=None,formal_pass=0,source_sha256=sha(Path(__file__))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--n',type=int,default=32768);a=p.parse_args();run(a.seed,a.n)
