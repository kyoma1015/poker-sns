"""Fresh fixed-n confirmation of a selected legal exploit; not full BR."""
import argparse,json,random,time
from pathlib import Path
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.range_continuation import RangePolicy,load_kernel
from gto.qualification.coupled_evaluate import Extra
from gto.qualification.action_native import native_value,interval
from gto.qualification.variance_study import compressed
from gto.qualification.evaluate import atomic
from gto.qualification.policy import sha
from gto.native.training import NativeGame

def run(build,library,out):
    out=Path(out);lib=load_kernel(library);ps=[RangePolicy(load_policy(build,out/str(seed)/'epoch2-strategy.json.gz'),lib) for seed in (17119101,17119102)];ds=[Extra(p,'open2p5') for p in ps]
    r=random.Random(17119112);ws=[(r.sample(range(52),9),r.getrandbits(128)) for _ in range(4096)];vals=[[] for _ in range(4)];start=time.monotonic();game=NativeGame([100,100])
    identity=dict(seed=17119112,n=4096,worlds=ws,policy_digests=[p.policy_digest for p in ps],source_sha256=sha(Path(__file__)),native_binary_sha256=sha(Path(ps[0].native.__file__)),deviation='SB root raise-to2.5BB',selection='selected on disjoint seed17119111 pilot; no reuse of pilot outcomes')
    for i,(deck,tape) in enumerate(ws):
        if time.monotonic()-start>180:
            atomic(out/'open-confirmation.json',dict(status='INCOMPLETE_TIME_LIMIT',completed=i));return
        for p,v in zip(ps+ds,vals):v.append(native_value(p,ps[0].native,game,deck,tape))
        if (i+1)%256==0:
            compressed(out/'open-confirmation-checkpoint.json.gz',dict(identity=identity,completed=i+1,values=vals));print(json.dumps(dict(confirmed_worlds=i+1,seconds=time.monotonic()-start)),flush=True)
    reports=[]
    for j,p in enumerate(ps):
        gain=interval([a-b for a,b in zip(vals[2+j],vals[j])],-100,100,.001/2)
        reports.append(dict(policy_digest=p.policy_digest,root_deviation_gain_bb=gain,independent_BR_gain_lower_bb=max(0,gain['interval'][0])))
    atomic(out/'open-confirmation.json',dict(status='COMPLETE_UNVERIFIED',identity=identity,reports=reports,confidence_family=.999,seconds=time.monotonic()-start,
        full_native_BR_upper_bb=None,full_native_nashconv_bb=None,ordinary_registry_admission=False,formal_acceptance=0,verified_strategies=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--library',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.build,a.library,a.out)
