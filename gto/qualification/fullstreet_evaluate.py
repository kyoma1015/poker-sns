"""Independent native comparison of bounded causal-fullstreet candidates."""
import argparse,copy,gzip,json,math,random,time
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification import fullstreet_solver as f,joint_release as old
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.policy import sha,act
from gto.qualification.native_mccfr import betting
from gto.qualification.public_response import observe
from gto.qualification.action_native import native_value,interval
from gto.qualification.coupled_evaluate import Extra
from gto.qualification.range_study import GeneralNuts
from gto.qualification.variance_study import compressed
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame


def select_early(lib,out):
    # Post-pilot validation selected the earliest16 point. Independent native seed
    # is not used to select it. Reconstruct short deterministic history; preserve128.
    out=Path(out);curves=json.loads((out/'curves.json').read_text())['curves'];checks=[]
    for seed,parentseed in ((17120101,17119201),(17120102,17119202)):
        folder=out/str(seed);meta=json.loads((folder/'policy-initial.json').read_text());blocks=f.load_blocks(folder/'train.npz');parent=json.loads(gzip.decompress((Path('docs/qa/joint-release-20261119')/str(parentseed)/'policy-final.json.gz').read_bytes()))
        q=f.Game(lib,meta['nodes'],blocks);prior=f.projected_prior(q,parent,True);q.prior[:]=prior;q.R[:]=np.asarray(prior,dtype=float)*1e-15;del prior,parent
        for _ in range(16):q.step()
        train=q.measure();expected=next(x for x in curves if x['seed']==seed and x['iterations']==16)
        if abs(train['restricted_NC_bb']-expected['train_NC_bb'])>1e-10:raise ValueError('deterministic16 replay mismatch')
        q.save(folder/'selected-checkpoint.npz');f.dump_policy(q,folder,meta,'policy-selected');q.use_blocks(f.load_blocks(folder/'fresh_heldout.npz'));held=q.measure()
        atomic(folder/'selected-metrics.json',dict(train=train,heldout=held,coverage=f.inspect_coverage(q),selection='post-pilot earliest16; validation reused for selection,not independent final quality proof'))
        checks.append(dict(seed=seed,iteration=16,train_NC_equal=True,original128_preserved=True));del q
    atomic(out/'selection.json',dict(replays=checks,learning_escalation=False,reason='fresh model-heldout worsened16->64->128; select16 for disjoint native test,do not extend256'))


def load_parent(build,ranklib,seed):
    base=load_policy(build,old.ARTIFACT);d=json.loads(gzip.decompress((Path('docs/qa/joint-release-20261119')/str(seed)/'policy-final.json.gz').read_bytes()));return old.JointPolicy(d,base,ranklib)


def run(build,library,ranklib,out):
    out=Path(out);lib=f.load(library);base=load_policy(build,old.ARTIFACT);rank=model.load(ranklib)
    select_early(lib,out);parents=[load_parent(build,rank,s) for s in (17119201,17119202)];qs=[f.read_policy(out/str(s),lib,base,'policy-selected') for s in (17120101,17120102)]
    for seed,q in zip((17120101,17120102),qs):
        metrics=json.loads((out/str(seed)/'selected-metrics.json').read_text());rows={}
        for name,prefix in [('rfi',[]),('vs_open',[8]),('vs_3bet',[8,22])]:
            b=betting(base.rules)
            for a in prefix:act(b,a)
            k=q.known[(0,tuple(tuple(h[:3]) for h in b.history))];n=len(q.nodes[k]['children']);rows[name]={}
            for c,(label,g) in enumerate(zip(model.CLASSES,model.classes())):
                o=observe(b,g[0],[]);freq=q._row(o,False);at=q.bases[k]+c*n
                rows[name][label]=dict(native_actions=o.actions,frequencies=freq,average_mass=float(q.average_mass[at:at+n].sum()),train_conditional_model_EV_bb=metrics['train']['action_EV_bb'][str(k)][c*n:(c+1)*n],heldout_conditional_model_EV_bb=metrics['heldout']['action_EV_bb'][str(k)][c*n:(c+1)*n],native_action_EV_interval_bb=None)
        compressed(out/str(seed)/'169-frequencies-EV.json.gz',dict(policy_digest=q.policy_digest,rows=rows,full_native_EV_precision_bb=None,ordinary_registry_admission=False))
    initial=f.read_policy(out/'17120101',lib,base,'policy-initial');profiles=[base,parents[0],qs[0],qs[1],initial];names=['oldB','current_joint','fullstreet_seed1','fullstreet_seed2','prior_only']
    kinds=['open3p5','threebet10p5','river_jam','fold','open2p5','threebet9'];probes=[Extra(qs[0],k) for k in kinds]+[GeneralNuts(qs[0]),GeneralNuts(parents[0])]
    rng=random.Random(17120201);ws=[(rng.sample(range(52),9),rng.getrandbits(128)) for _ in range(2048)];values=[[] for _ in profiles+probes];game=NativeGame([100,100]);start=time.monotonic();coverage=[dict(worlds_with_unlearned=0,worlds_with_offtree=0,queries={r:dict(queries=0,unlearned=0,offtree=0) for r in range(4)}) for _ in qs]
    identity=dict(seed=17120201,n=2048,worlds=ws,policy_digests=[q.policy_digest for q in profiles],source_sha256=sha(Path(__file__)),native_binary_sha256=sha(Path(base.native.__file__)),confidence_family=.999,events=21)
    for i,(deck,tape) in enumerate(ws):
        if time.monotonic()-start>120:
            compressed(out/'native-checkpoint.json.gz',dict(identity=identity,completed=i,values=values,coverage=coverage));atomic(out/'native.json',dict(status='INCOMPLETE_TIME_LIMIT',completed=i));return
        for j,(q,v) in enumerate(zip(profiles+probes,values)):
            before=copy.deepcopy(q.stats) if j in (2,3) else None;v.append(native_value(q,base.native,game,deck,tape))
            if before is not None:
                delta={r:{k:q.stats[r][k]-before[r][k] for k in before[r]} for r in range(4)};cov=coverage[j-2]
                cov['worlds_with_unlearned']+=int(any(delta[r]['unlearned'] for r in delta));cov['worlds_with_offtree']+=int(any(delta[r]['offtree'] for r in delta))
                for r in delta:
                    for k in delta[r]:cov['queries'][r][k]+=delta[r][k]
        if (i+1)%256==0:
            compressed(out/'native-checkpoint.json.gz',dict(identity=identity,completed=i+1,values=values,coverage=coverage));print(json.dumps(dict(native_worlds=i+1,seconds=time.monotonic()-start)),flush=True)
    delta=.001/21;ev=[dict(name=n,digest=q.policy_digest,SB_EV_bb=interval(v,-50,50,delta)) for n,q,v in zip(names,profiles,values)];comparisons=[]
    for qi in (2,3):
        for ci in (0,1,4):comparisons.append(dict(candidate=names[qi],control=names[ci],paired_EV_change_bb=interval([a-b for a,b in zip(values[qi],values[ci])],-100,100,delta)))
    dev=[]
    for k,v in zip(kinds+['river_nuts'],values[5:12]):
        sign=1 if k in ('open3p5','open2p5','fold') else -1;gain=interval([sign*(a-b) for a,b in zip(v,values[2])],-100,100,delta);dev.append(dict(kind=k,gain_bb=gain))
    oldgain=[a-b for a,b in zip(values[1],values[12])];newgain=[a-b for a,b in zip(values[2],values[11])];reduction=interval([a-b for a,b in zip(oldgain,newgain)],-100,100,delta)
    for cov in coverage:cov['unlearned_world_rate']=cov['worlds_with_unlearned']/2048;cov['offtree_world_rate']=cov['worlds_with_offtree']/2048
    atomic(out/'native.json',dict(status='COMPLETE_UNVERIFIED',identity=identity,profiles=ev,comparisons=comparisons,deviations=dev,river_nuts_old_gain_bb=interval(oldgain,-100,100,delta),river_nuts_new_gain_bb=interval(newgain,-100,100,delta),river_nuts_reduction_bb=reduction,old_nuts_queries=probes[-1].queries,old_nuts_jams=probes[-1].jams,new_nuts_queries=probes[-2].queries,new_nuts_jams=probes[-2].jams,native_coverage=coverage,seconds=time.monotonic()-start,full_native_BR_upper_bb=None,full_native_NashConv_bb=None,full_native_EV_precision_bb=None,uniform_continuation_error_bb=None,omitted_size_error_bb=None,ordinary_registry_admission=False,formal_acceptance=0,verified_strategies=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--library',default='/tmp/fullstreet-build/fullstreet.so');p.add_argument('--ranklib',default='/tmp/range-continuation-build/range.so');p.add_argument('--out',required=True);a=p.parse_args();run(a.build,a.library,a.ranklib,a.out)
