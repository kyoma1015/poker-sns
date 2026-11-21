"""Bounded conditional native evaluation; no quality/registry admission."""
import argparse,json,math,random,time
from pathlib import Path
from gto.qualification.range_continuation import load,RangePolicy
from gto.qualification.action_native import native_value
from gto.qualification.release_deviation import RiverNuts,binomial_lower,nuts
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame

BASELINE=Path('docs/qa/coverage-release-20261118/B-native-deviation.json')
ARTIFACT='docs/qa/release-route-20261118/strategy.json.gz'

def policies(build,library):
    a=load(build,ARTIFACT,library);return [a,RangePolicy(a.base,a.lib,buckets=16)]

def pilot(build,library,out):
    ps=policies(build,library);rng=random.Random(17118201);worlds=[(rng.sample(range(52),9),rng.getrandbits(128)) for _ in range(64)];reports=[]
    for p in ps:
        start=time.monotonic();a=b=0.
        for deck,tape in worlds:
            if time.monotonic()-start>30:raise RuntimeError('pilot budget')
            a+=native_value(p.base,p.native,NativeGame([100,100]),deck,tape);b+=native_value(p,p.native,NativeGame([100,100]),deck,tape)
        reports.append(dict(buckets=p.buckets,n=64,seconds=time.monotonic()-start,old_EV=a/64,new_EV=b/64,policy_digest=p.policy_digest,solves=p.solves,solve_seconds=p.solve_seconds,status='PILOT_NOT_QUALITY_PASS'))
    atomic(out,dict(profiles=reports))

class GeneralNuts(RiverNuts):
    def row(self,o,average=False):
        if o.actor==1 and o.round==3 and o.street[1]==o.price and 1 in o.actions and o.live[0]==o.live[1] and 0<o.live[1]<100 and o.remaining[1]>0:
            self.queries+=1
            if nuts(self.base.native,list(o.own),list(o.board)):
                self.jams+=1;a=max(o.actions);return [float(x==a) for x in o.actions]
        return self.base.row(o,True)

def conditional(build,library,out,resume=None,general=False):
    ps=policies(build,library);old=ps[0].base;receipt=json.loads(BASELINE.read_text())
    if old.policy_digest!=receipt['source_policy_digest']:raise ValueError('source receipt mismatch')
    if general:ps=ps[:1]
    target=512 if general else 256;seed=17118206 if general else 17118202
    count=receipt['jams'];n=receipt['n'];alpha=.001/(len(ps)+1)
    mass_lower=binomial_lower(count,n,alpha)
    olddev=RiverNuts(old);devs=[(GeneralNuts if general else RiverNuts)(p) for p in ps];rng=random.Random(seed)
    start=time.monotonic();accepted=0;attempts=0;differences=[[] for _ in ps];oldgains=[];newgains=[[] for _ in ps]
    checkpoint=Path(str(out)+'.progress.json');game=NativeGame([100,100]);prior_seconds=0.;accepted_worlds=[];counter_complete=True
    if resume:
        saved=json.loads(Path(resume).read_text())
        if saved['policy_digests']!=[p.policy_digest for p in ps]:raise ValueError('resume policy mismatch')
        def tuples(x):return tuple(tuples(y) for y in x) if isinstance(x,list) else x
        rng.setstate(tuples(saved['rng']));accepted=saved['accepted'];attempts=saved['attempts'];prior_seconds=saved['seconds']
        oldgains=saved['old_gains'];newgains=saved['new_gains'];differences=saved['differences'];accepted_worlds=saved['worlds']
        counter_complete=saved.get('new_deviation_jams') is not None
        if counter_complete:
            for d,previous_jams in zip(devs,saved['new_deviation_jams']):d.jams=previous_jams
        if any(len(v)!=accepted for v in [oldgains,*newgains,*differences]):raise ValueError('resume sample length')
    while accepted<target:
        if prior_seconds+time.monotonic()-start>120:
            atomic(out,dict(status='INCOMPLETE_TIME_LIMIT',accepted=accepted,attempts=attempts,policy_digests=[p.policy_digest for p in ps]));return
        attempts+=1;deck=rng.sample(range(52),9);tape=rng.getrandbits(128);before=olddev.jams
        v= native_value(olddev,old.native,game,deck,tape)
        if olddev.jams==before:continue
        reference=native_value(old,old.native,game,deck,tape);oldgain=reference-v
        assert oldgain>=0 and (oldgain==0 or oldgain>=40)
        oldgains.append(oldgain)
        for p,d,ds,gs in zip(ps,devs,differences,newgains):
            a=native_value(p,p.native,game,deck,tape);b=native_value(d,p.native,game,deck,tape);gain=a-b;difference=oldgain-gain
            assert -100<=difference<=149
            gs.append(gain);ds.append(difference)
        accepted+=1;accepted_worlds.append(dict(deck=deck,tape=tape))
        if accepted%16==0:atomic(checkpoint,dict(accepted=accepted,target=target,attempts=attempts,seconds=prior_seconds+time.monotonic()-start,rng=rng.getstate(),new_deviation_jams=[d.jams for d in devs] if counter_complete else None,worlds=accepted_worlds,old_gains=oldgains,new_gains=newgains,differences=differences,policy_digests=[p.policy_digest for p in ps]))
    radius=249*math.sqrt(math.log(1/alpha)/(2*accepted));reports=[]
    for p,ds,gs in zip(ps,differences,newgains):
        mean=sum(ds)/accepted;lower=mean-radius
        reports.append(dict(buckets=p.buckets,policy_digest=p.policy_digest,conditional_old_gain_bb=sum(oldgains)/accepted,
            conditional_new_gain_bb=sum(gs)/accepted,conditional_paired_reduction_bb=mean,conditional_reduction_lower_bb=lower,
            root_reduction_lower_bb=mass_lower*lower if lower>0 else None,stage_gate=lower>0,generalized_river_pots=general,known_nut_deviation_actions=devs[len(reports)].jams if counter_complete else None))
    atomic(out,dict(status='COMPLETE_UNVERIFIED',seconds=prior_seconds+time.monotonic()-start,attempts=attempts,conditional_events=accepted,seed=seed,
        source_receipt=str(BASELINE),source_event_count=count,source_worlds=n,event_mass_lower=mass_lower,
        confidence_family=.999,events=len(ps)+1,conditional_hoeffding_radius_bb=radius,
        support_proof='preflop B unchanged; new deviation can act only on same globally-nut deal+preflop events E; payoff difference0 outside E',
        profiles=reports,raw_old_gains=oldgains,raw_new_gains=newgains,worlds=accepted_worlds,full_br_upper_bb=None,nashconv_bb=None,nashconv_upper_bb=None,
        ordinary_registry_admission=False,verified_strategy_count=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--library',required=True);p.add_argument('--output',required=True);p.add_argument('--pilot',action='store_true');p.add_argument('--resume');p.add_argument('--general',action='store_true');a=p.parse_args()
    if a.pilot:pilot(a.build,a.library,a.output)
    else:conditional(a.build,a.library,a.output,a.resume,a.general)
