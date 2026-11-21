"""Relaxed range/payoff fixed-point experiments; not joint full-game CFR."""
import argparse,gzip,json,random,time,copy
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification.preflop_reopt import rollout,matched_states,RATIO,ARTIFACT,H,aggregate
from gto.qualification.preflop_release_solver import load_policy,ReleasePolicy
from gto.qualification.range_continuation import RangePolicy,load_kernel
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha
from gto.qualification.variance_study import compressed
from gto.qualification.evaluate import atomic
import ctypes as C

PRIOR=Path('docs/qa/preflop-reoptimized-20261118/range_reoptimized.json.gz')

def worlds(seed,n):
    r=random.Random(seed);return [dict(board=r.sample(range(52),5),seed=r.getrandbits(128)) for _ in range(n)]

def payoff(policy,ws,deadline,checkpoint):
    nodes=policy.base.nodes;states=matched_states(policy.rules,nodes);counts,_=model.chance(model.classes());samples=[]
    for w in ws:
        leaf=np.zeros((len(nodes),169**2))
        ids=np.flatnonzero(~np.isin(H,w['board']).any(axis=1));valid=set(ids)
        ranks=np.asarray([model.rank(policy.lib,list(map(int,h))+w['board']) if i in valid else 0 for i,h in enumerate(H)],dtype=np.int64)
        signs=aggregate(ids,ids,ranks,1)
        for k,n in enumerate(nodes):
            if n['actor']<0 and not n['matched']:leaf[k]=n['value']
        for k,b in states.items():
            sums=nodes[k]['value']*signs if b.done else rollout(policy,b,w['board'],w['seed'],deadline)[0]
            leaf[k]=RATIO*sums/np.asarray(counts)
        samples.append(leaf.tolist())
        compressed(checkpoint,dict(policy_digest=policy.policy_digest,worlds=ws,completed=len(samples),samples=samples))
    return np.mean(samples,axis=0)

def evaluate(lib,leaf,nodes,strategy,n=169):
    m=len(nodes);_,p=model.chance(model.classes()) if n==169 else (None,None)
    if p is None:raise ValueError('use independent toy oracle for toy games')
    ev=(C.c_double*(m*3*n))();reach=(C.c_double*(m*n))();metrics=(C.c_double*4)()
    lib.abstract_evaluate(n,m,model.ints([x['actor'] for x in nodes]),model.ints([len(x['actions']) for x in nodes]),model.ints([c for x in nodes for c in (x['children']+[-1]*3)[:3]]),model.doubles(p),model.doubles(leaf.ravel().tolist()),model.doubles(strategy),ev,reach,metrics)
    return dict(profile_sb_ev_bb=metrics[0]/2,br_sb_ev_bb=metrics[1]/2,br_bb_min_sb_ev_bb=metrics[2]/2,abstract_nashconv_bb=metrics[3]/2,action_ev_chips=list(ev),reach=list(reach))

def candidate(anchor,target,alpha,identity):
    artifact=copy.deepcopy(anchor.base.artifact);artifact.pop('policy_digest',None);artifact.pop('combined_policy_digest',None)
    artifact['identity']=identity
    artifact['strategy']=[(1-alpha)*a+alpha*b for a,b in zip(anchor.base.strategy,target['strategy'])]
    carrier=ReleasePolicy(artifact,anchor.base.fallback);return RangePolicy(carrier,anchor.lib)

def run(build,library,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);allstart=time.monotonic();lib=load_kernel(library);curves=[]
    for seed in (17119101,17119102):
        folder=out/str(seed);folder.mkdir(exist_ok=True);start=time.monotonic();deadline=min(start+180,allstart+400)
        q=RangePolicy(load_policy(build,PRIOR),lib);ws=worlds(seed,4);validation=worlds(seed+100,4)
        for epoch in range(4):
            try:
                leaf=payoff(q,ws,deadline,folder/f'epoch{epoch}-train.json.gz')
                current=evaluate(lib,leaf,q.base.nodes,q.base.strategy)
                held=payoff(q,validation,deadline,folder/f'epoch{epoch}-heldout.json.gz')
                hold=evaluate(lib,held,q.base.nodes,q.base.strategy)
            except TimeoutError:
                atomic(folder/'stopped.json',dict(status='TIME_LIMIT',epoch=epoch,seconds=time.monotonic()-start));break
            report=dict(seed=seed,epoch=epoch,worlds=4,inner_iterations=100,alpha=.25,policy_digest=q.policy_digest,
                train_NC_bb=current['abstract_nashconv_bb'],heldout_NC_bb=hold['abstract_nashconv_bb'],heldout_EV_bb=hold['profile_sb_ev_bb'],seconds=time.monotonic()-start)
            artifact=q.base.artifact;artifact['policy_digest']=q.base.policy_digest;artifact['combined_policy_digest']=q.policy_digest
            artifact['abstract_sample_metrics']=dict(iterations=100,**{k:v for k,v in current.items() if k not in ('action_ev_chips','reach')})
            artifact['self_consistent_train_metrics']={k:v for k,v in current.items() if k not in ('action_ev_chips','reach')}
            artifact['self_consistent_heldout_metrics']={k:v for k,v in hold.items() if k not in ('action_ev_chips','reach')}
            artifact['action_ev_chips']=current['action_ev_chips'];artifact['reach']=current['reach']
            artifact['model_ranges']=model.ranges(dict(strategy=q.base.strategy,**current),q.base.nodes)
            compressed(folder/f'epoch{epoch}-strategy.json.gz',artifact);curves.append(report);atomic(out/'curves.json',dict(curves=curves,formal_acceptance=0,verified_strategies=0));print(json.dumps(report),flush=True)
            if epoch==3 or (epoch>=2 and report['heldout_NC_bb']>=curves[-3]['heldout_NC_bb']):break
            _,p=model.chance(model.classes());target=model.solve(lib,leaf.ravel().tolist(),p,q.base.nodes,iterations=100)
            identity=dict(schema='relaxed-range-payoff-v1',seed=seed,epoch=epoch+1,alpha=.25,train_worlds=ws,heldout_worlds=validation,
                parent_digest=q.policy_digest,source_sha256=sha(Path(__file__)),range_identity=q.id,iterations=100,
                range_coupling_error_bb=None,omitted_size_error_bb=None,ordinary_registry_admission=False,formal_profile=False)
            q=candidate(q,target,.25,identity)
    return curves

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--library',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.build,a.library,a.out)
