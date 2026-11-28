"""One bounded preflop policy-iteration step; never a full-game certificate."""
import argparse,copy,gzip,json,math,random,time
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification.range_continuation import HOLES,RangePolicy,load,history_action
from gto.qualification.preflop_release_solver import tree,ReleasePolicy
from gto.qualification.native_mccfr import betting,digest
from gto.qualification.policy import act,hand,sha
from gto.qualification.variance_study import compressed
from gto.qualification.evaluate import atomic

ARTIFACT='docs/qa/release-route-20261118/strategy.json.gz'
H=np.asarray(HOLES);CLASS=np.asarray([hand(h) for h in HOLES]);RATIO=math.comb(52,5)/math.comb(48,5)

def public_coins(seed,board,history):
    bits=int(digest([seed,list(board),list(history)]),16)
    return ((bits>>128)/2**128,(bits%(2**128))/2**128)

def choices(policy,ctx,seed,board,history):
    """Mixture sampler exactly reproduces epsilon/A+(1-epsilon)*sigma."""
    u,v=public_coins(seed,board,history);actions=ctx['available'];n=policy.buckets
    if u<policy.epsilon:return np.full(1326,actions[min(int(v*len(actions)),len(actions)-1)])
    out=np.full(1326,-1)
    for k in range(n):
        weights=[ctx['strategy'][(ctx['index']*3+j)*n+k] for j in range(len(ctx['node']['native_actions']))]
        j=min(int(np.searchsorted(np.cumsum(weights),v,side='right')),len(weights)-1)
        out[np.asarray(ctx['bucket'])==k]=ctx['node']['native_actions'][j]
    return out

def aggregate(a,b,ranks,stake,fold=None):
    aa=H[a];bb=H[b];valid=(aa[:,None,0]!=bb[None,:,0])&(aa[:,None,0]!=bb[None,:,1])&(aa[:,None,1]!=bb[None,:,0])&(aa[:,None,1]!=bb[None,:,1])
    values=np.full(valid.shape,fold,dtype=float) if fold is not None else stake*np.sign(ranks[a,None]-ranks[None,b])
    return np.bincount((CLASS[a,None]*169+CLASS[None,b])[valid],weights=values[valid],minlength=169**2)

def matched_states(rules,nodes):
    found={}
    def visit(k,b):
        n=nodes[k]
        if n['actor']<0:
            if n['matched']:found[k]=b
            return
        for a,child in zip(n['native_actions'],n['children']):
            c=copy.deepcopy(b);act(c,a);visit(child,c)
    visit(0,betting(rules));return found

def rollout(policy,start,board,seed,deadline,subsets=None):
    """Full public tree with shared action coins, no private/future policy input."""
    ids=np.flatnonzero(~np.isin(H,board).any(axis=1));valid=set(ids)
    ranks=np.asarray([model.rank(policy.lib,list(h)+list(board)) if i in valid else 0 for i,h in enumerate(HOLES)],dtype=np.int64)
    total=np.zeros(169**2);visited=0
    def visit(b,sets):
        nonlocal total,visited
        visited+=1
        if visited>4096 or time.monotonic()>deadline:raise TimeoutError('incomplete world discarded')
        if not len(sets[0]) or not len(sets[1]):return
        if b.done:
            fold=b.settle([0,0],True)['net'][0] if any(b.folded) else None
            total+=aggregate(*sets,ranks,b.live[0],fold);return
        shown=tuple(board[:(0,3,4,5)[b.round]]);hist=tuple(b.history)
        ctx=policy.context(b,shown,policy.ranges(hist,shown))
        selected=choices(policy,ctx,seed,shown,hist)
        for action in np.unique(selected[sets[b.actor]]):
            if action<0:raise ValueError('invalid actual own hand bucket')
            nxt=list(sets);nxt[b.actor]=sets[b.actor][selected[sets[b.actor]]==action]
            c=copy.deepcopy(b);act(c,int(action));visit(c,nxt)
    visit(copy.deepcopy(start),[ids,ids] if subsets is None else subsets);return total,visited

def run(build,library,out,worlds=8,seconds=300,resume=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);start=time.monotonic();deadline=start+seconds
    policy=load(build,ARTIFACT,library);nodes=tree(policy.rules);states=matched_states(policy.rules,nodes)
    counts,p=model.chance(model.classes());counts=np.asarray(counts);rng=random.Random(17118301)
    planned=[dict(board=rng.sample(range(52),5),seed=rng.getrandbits(128)) for _ in range(worlds)]
    identity=dict(schema='range-payoff-preflop-iteration-v1',anchor_digest=policy.policy_digest,worlds=planned,
        chance_ratio=RATIO,source_sha256={str(x):sha(x) for x in [Path(__file__),Path(model.__file__),Path(model.__file__).with_name('core.cc')]},
        range_identity=policy.id,iterations=100,range_coupling_error_bb=None,omitted_size_error_bb=None,formal_profile=False)
    checkpoint=out/'kernel-checkpoint.json.gz';active=[];passive=[];completed=[]
    if resume:
        saved=json.loads(gzip.decompress(checkpoint.read_bytes()))
        if saved['identity']!=identity:raise ValueError('resume identity mismatch')
        active=saved['active'];passive=saved['passive'];completed=saved['completed']
    for w in planned[len(completed):]:
        av=np.zeros((len(nodes),169**2));pv=np.zeros_like(av);visits=0
        ids=np.flatnonzero(~np.isin(H,w['board']).any(axis=1));valid=set(ids)
        ranks=np.asarray([model.rank(policy.lib,list(h)+w['board']) if i in valid else 0 for i,h in enumerate(HOLES)],dtype=np.int64)
        sign=aggregate(ids,ids,ranks,1)
        try:
            for k,b in states.items():
                pv[k]=RATIO*nodes[k]['value']*sign/counts
                if b.done:av[k]=pv[k]
                else:
                    sums,v=rollout(policy,b,w['board'],w['seed'],deadline);av[k]=RATIO*sums/counts;visits+=v
        except TimeoutError:
            atomic(out/'stopped.json',dict(status='INCOMPLETE_TIME_LIMIT',completed=len(completed),seconds=time.monotonic()-start));break
        active.append(av.tolist());passive.append(pv.tolist());completed.append(dict(**w,public_nodes=visits))
        compressed(checkpoint,dict(identity=identity,completed=completed,active=active,passive=passive))
        print(json.dumps(dict(completed=len(completed),seconds=time.monotonic()-start,public_nodes=visits)),flush=True)
        if time.monotonic()>deadline:break
    if not completed:raise RuntimeError('no complete kernel world; checkpoint protected')
    policies={}
    for label,samples in [('passive_control',passive),('range_reoptimized',active)]:
        leaf=np.mean(samples,axis=0)
        for k,n in enumerate(nodes):
            if n['actor']<0 and not n['matched']:leaf[k]=n['value']
        result=model.solve(policy.lib,leaf.ravel().tolist(),p,nodes,iterations=100)
        artifact=dict(identity=dict(**identity,variant=label,completed_worlds=len(completed)),nodes=nodes,strategy=result['strategy'],fallback_policy_digest=policy.base.fallback.policy_digest,
            abstract_sample_metrics={k:result[k] for k in ('iterations','seconds','profile_sb_ev_bb','br_sb_ev_bb','br_bb_min_sb_ev_bb','abstract_nashconv_bb')},
            action_ev_chips=result['action_ev_chips'],reach=result['reach'],
            model_ranges=model.ranges(result,nodes),ordinary_registry_admission=False,status='BLOCKED_UNVERIFIED',formal_acceptance_complete=0,verified_strategy_count=0)
        carrier=ReleasePolicy(artifact,policy.base.fallback);artifact['policy_digest']=carrier.policy_digest
        combined=RangePolicy(carrier,policy.lib);artifact['combined_policy_digest']=combined.policy_digest
        artifact['changed_strategy_entries_vs_old']=sum(abs(a-b)>1e-12 for a,b in zip(carrier.strategy,policy.base.strategy))
        compressed(out/(label+'.json.gz'),artifact);policies[label]=combined
    atomic(out/'generation.json',dict(status='BLOCKED_UNVERIFIED',completed_worlds=len(completed),requested_worlds=worlds,seconds=time.monotonic()-start,
        policies={k:v.policy_digest for k,v in policies.items()},full_native_BR_upper_bb=None,nashconv_bb=None,full_169_action_native_EV_precision_bb=None,
        range_coupling_error_bb=None,formal_acceptance=0,verified_strategies=0))
    return policies

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--library',required=True);p.add_argument('--out',required=True);p.add_argument('--worlds',type=int,default=8);p.add_argument('--seconds',type=float,default=300);p.add_argument('--resume',action='store_true');a=p.parse_args();run(a.build,a.library,a.out,a.worlds,a.seconds,a.resume)
