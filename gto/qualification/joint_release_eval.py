"""Frozen same-game joint-policy export and independent native comparison."""
import argparse,gzip,json,random,time
from pathlib import Path
from gto.abstract import model
from gto.qualification import joint_release as j
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.range_continuation import load as load_range
from gto.qualification.coupled_evaluate import Extra
from gto.qualification.range_study import GeneralNuts
from gto.qualification.action_native import native_value,interval
from gto.qualification.public_response import observe
from gto.qualification.native_mccfr import betting
from gto.qualification.policy import act,sha
from gto.qualification.variance_study import compressed
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame

def read(path):return json.loads(gzip.decompress(Path(path).read_bytes()))

def run(build,ranklib,out):
    out=Path(out);base=load_policy(build,j.ARTIFACT);rank=model.load(ranklib);ps=[]
    for seed in (17119201,17119202):
        d=read(out/str(seed)/'policy-final.json.gz');p=j.JointPolicy(d,base,rank);ps.append(p);rows={}
        for name,prefix in [('rfi',[]),('vs_open',[8]),('vs_3bet',[8,22])]:
            b=betting(base.rules)
            for a in prefix:act(b,a)
            k=p.known[(0,tuple(tuple(h[:3]) for h in b.history))];n=p.nodes[k];start=p.bases[k];count=len(n['native_actions']);rows[name]={}
            for c,(label,group) in enumerate(zip(model.CLASSES,model.classes())):
                o=observe(b,group[0],[]);freq=p.row(o,True)
                if abs(sum(freq)-1)>1e-10 or any(x<0 for x in freq):raise ValueError('normalized169 row')
                rows[name][label]=dict(native_actions=o.actions,frequencies=freq,selected_actions=n['native_actions'],train_conditional_EV_bb=d['train_metrics']['action_EV_bb'][start+c*count:start+(c+1)*count],heldout_conditional_EV_bb=d['heldout_metrics']['action_EV_bb'][start+c*count:start+(c+1)*count],native_action_EV_interval_bb=None)
        compressed(out/str(seed)/'169-frequencies-EV.json.gz',dict(policy_digest=p.policy_digest,rows=rows,full_native_169_action_precision_bb=None,ordinary_registry_admission=False))
    previous=load_range(build,'docs/qa/preflop-reoptimized-20261118/range_reoptimized.json.gz',ranklib)
    profiles=[base,previous,*ps];names=['oldB','previous_range_reoptimized','joint_seed1','joint_seed2'];kinds=['open3p5','threebet10p5','river_jam','fold','open2p5','threebet9'];probes=[Extra(ps[0],k) for k in kinds]+[GeneralNuts(ps[0])]
    r=random.Random(17119211);ws=[(r.sample(range(52),9),r.getrandbits(128)) for _ in range(2048)];vals=[[] for _ in profiles+probes];start=time.monotonic();game=NativeGame([100,100]);delta=.001/15
    identity=dict(seed=17119211,n=2048,worlds=ws,policy_digests=[p.policy_digest for p in profiles],source_sha256=sha(Path(__file__)),native_binary_sha256=sha(Path(base.native.__file__)),confidence_family=.999,events=15)
    for i,(deck,tape) in enumerate(ws):
        if time.monotonic()-start>120:
            compressed(out/'native-checkpoint.json.gz',dict(identity=identity,completed=i,values=vals));atomic(out/'native.json',dict(status='INCOMPLETE_TIME_LIMIT',completed=i));return
        for p,v in zip(profiles+probes,vals):v.append(native_value(p,base.native,game,deck,tape))
        if (i+1)%256==0:
            compressed(out/'native-checkpoint.json.gz',dict(identity=identity,completed=i+1,values=vals));print(json.dumps(dict(native_worlds=i+1,seconds=time.monotonic()-start)),flush=True)
    ev=[dict(name=n,policy_digest=p.policy_digest,SB_EV_bb=interval(v,-50,50,delta)) for n,p,v in zip(names,profiles,vals)];changes=[]
    for qi in (2,3):
        for ci in (0,1):changes.append(dict(candidate=names[qi],control=names[ci],paired_EV_change_bb=interval([a-b for a,b in zip(vals[qi],vals[ci])],-100,100,delta)))
    dev=[]
    for k,v in zip(kinds+['river_nuts'],vals[4:]):
        sign=1 if k in ('open3p5','fold','open2p5') else -1;g=interval([sign*(a-b) for a,b in zip(v,vals[2])],-100,100,delta)
        dev.append(dict(kind=k,gain_bb=g,BR_gain_lower_bb=max(0,g['interval'][0])))
    gate=all(c['paired_EV_change_bb']['interval'][0]>0 for c in changes if c['control']=='oldB') and all(d['BR_gain_lower_bb']==0 for d in dev)
    atomic(out/'native.json',dict(status='COMPLETE_UNVERIFIED',identity=identity,profiles=ev,comparisons=changes,deviations=dev,nuts_queries=probes[-1].queries,nuts_jams=probes[-1].jams,seconds=time.monotonic()-start,learning_expansion_gate=gate,full_native_BR_upper_bb=None,full_native_NashConv_bb=None,continuation_error_upper_bb=None,omitted_size_error_upper_bb=None,full_native_169_EV_precision_bb=None,ordinary_registry_admission=False,verified_strategies=0,formal_acceptance=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--ranklib',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.build,a.ranklib,a.out)
