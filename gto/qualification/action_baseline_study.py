"""Fixed-budget four-arm action-baseline/reach comparison; warm corrected S."""
import argparse,gzip,json,math,random,time
from pathlib import Path
from gto.qualification.action_baseline import ActionBaselineSolver
from gto.qualification.build import load
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed
from gto.qualification.native_mccfr import digest


def diagnostic(s,seed,n=256):
    rng=random.Random(seed);sums={};norms=[]
    for i in range(n):
        deck=rng.sample(range(52),9);regrets,_=s.collect(i%2,deck,random.Random(rng.getrandbits(128)))
        norm=0.
        for o,pi,delta,_ in regrets:
            norm+=math.fsum(x*x for x in delta)
            row=sums.setdefault(o.key,[0.]*len(delta))
            for a,x in enumerate(delta):row[a]+=x
        norms.append(norm)
    return dict(seed=seed,paths=n,cf_trace_sample_variance=(sum(norms)-sum(x*x for row in sums.values() for x in row)/n)/(n-1))


def run(build,source,output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    rules,native=load(build);data=json.loads(gzip.decompress(Path(source).read_bytes()));arms=[]
    for baseline,targeted in ((False,False),(True,False),(False,True),(True,True)):
        name=('baseline' if baseline else 'zero')+('-reach' if targeted else '-standard')
        frozen=ActionBaselineSolver(rules,native,baseline=baseline,targeted=targeted);frozen.warm(data)
        initial=frozen.policy_digest
        diagnostics=[diagnostic(frozen,seed) for seed in (1711801,1711802,1711803)]
        assert frozen.policy_digest==initial
        s=ActionBaselineSolver(rules,native,baseline=baseline,targeted=targeted);s.warm(data)
        start=time.monotonic();i=0
        while i<512 and time.monotonic()-start<2:
            s.step();i+=1
            if i%32==0:compressed(out/(name+'-checkpoint.json.gz'),s.snapshot())
        elapsed=time.monotonic()-start;compressed(out/(name+'-checkpoint.json.gz'),s.snapshot())
        R=sum(s.counts.values());S=sum(s.average_counts.values())
        arms.append(dict(name=name,baseline=baseline,targeted=targeted,new_iterations=i,training_seconds=elapsed,
            policy_digest=s.policy_digest,total_infosets=len(s.rows),R_updates=R,R_infosets=len(s.counts),
            S_updates=S,S_infosets=len(s.average_counts),R_revisit_rate=1-len(s.counts)/R,
            S_revisit_rate=1-len(s.average_counts)/S,positive_average_reach=dict(s.reach_counts),diagnostics=diagnostics))
        atomic(out/'comparison.json',dict(source_sha256=digest(data),arms=arms,status='RUNNING'))
    atomic(out/'comparison.json',dict(source_sha256=digest(data),arms=arms,status='UNVERIFIED_AWAITING_NATIVE_HOLDOUT',expanded_learning=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.build,a.source,a.output)
