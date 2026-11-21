"""Fresh fixed-world native holdout of reoptimized preflop frequencies."""
import argparse,gzip,json,random,time
from pathlib import Path
from gto.qualification.preflop_reopt import ARTIFACT
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.range_continuation import load,RangePolicy
from gto.qualification.action_native import native_value,interval
from gto.qualification.range_followup import Probe
from gto.qualification.range_study import GeneralNuts
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed
from gto.qualification.policy import sha
from gto.native.training import NativeGame

def evaluate(build,library,out):
    out=Path(out);prior=load(build,ARTIFACT,library)
    control=RangePolicy(load_policy(build,out/'passive_control.json.gz'),prior.lib)
    new=RangePolicy(load_policy(build,out/'range_reoptimized.json.gz'),prior.lib)
    ps=[prior.base,prior,control,new];names=['old_B_passive','prior_range_fixed_preflop','matched_passive_kernel_new_range','range_reoptimized']
    kinds=['open3p5','threebet10p5','river_jam','river_nuts'];probes=[Probe(new,k) for k in kinds[:3]]+[GeneralNuts(new)]
    rng=random.Random(17118302);worlds=[(rng.sample(range(52),9),rng.getrandbits(128)) for _ in range(256)]
    values=[[] for _ in ps+probes];game=NativeGame([100,100]);start=time.monotonic()
    identity=dict(policy_digests=[p.policy_digest for p in ps],seed=17118302,n=256,worlds=worlds,
        native_binary_sha256=sha(Path(new.native.__file__)),source_sha256=sha(Path(__file__)))
    for i,(deck,tape) in enumerate(worlds):
        if time.monotonic()-start>90:
            compressed(out/'native-holdout-checkpoint.json.gz',dict(identity=identity,values=values,completed=i))
            atomic(out/'native-holdout.json',dict(status='INCOMPLETE_TIME_LIMIT',completed=i));return
        for p,v in zip(ps+probes,values):v.append(native_value(p,new.native,game,deck,tape))
        if (i+1)%32==0:
            compressed(out/'native-holdout-checkpoint.json.gz',dict(identity=identity,values=values,completed=i+1))
            print(json.dumps(dict(native_worlds=i+1,seconds=time.monotonic()-start)),flush=True)
    delta=.001/11
    profiles=[dict(name=n,digest=p.policy_digest,SB_EV_bb=interval(v,-50,50,delta)) for n,p,v in zip(names,ps,values)]
    comparisons=[dict(control=names[i],paired_SB_EV_change_bb=interval([a-b for a,b in zip(values[3],values[i])],-100,100,delta)) for i in range(3)]
    deviations=[]
    for k,v in zip(kinds,values[4:]):
        sign=1 if k=='open3p5' else -1
        gains=interval([sign*(a-b) for a,b in zip(v,values[3])],-100,100,delta)
        deviations.append(dict(kind=k,gain_bb=gains,independent_BR_gain_lower_bb=max(0,gains['interval'][0])))
    gate=comparisons[1]['paired_SB_EV_change_bb']['interval'][0]>0 and all(d['independent_BR_gain_lower_bb']==0 for d in deviations)
    atomic(out/'native-holdout.json',dict(status='COMPLETE_UNVERIFIED',identity=identity,profiles=profiles,comparisons=comparisons,deviations=deviations,
        confidence_family=.999,events=11,seconds=time.monotonic()-start,learning_expansion_gate=gate,
        nashconv_lower_bb=max(d['independent_BR_gain_lower_bb'] for d in deviations),full_native_BR_upper_bb=None,nashconv_bb=None,
        ordinary_registry_admission=False,verified_strategies=0,formal_acceptance=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--library',required=True);p.add_argument('--out',required=True);a=p.parse_args();evaluate(a.build,a.library,a.out)
