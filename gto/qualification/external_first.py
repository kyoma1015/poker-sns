"""All-action first-owner external sampling, outcome sampling below. HU50 only."""
import math
import random
from pathlib import Path
from gto.qualification.native_mccfr import betting, choose
from gto.qualification.policy import act, sha
from gto.qualification.public_response import observe
from gto.qualification.variance_mccfr import VarianceSolver, cv_updates


def combine(updates):
    rows={}
    for o,pi,delta,weight in updates:
        r=rows.setdefault(o.key,dict(observation=o,R=[0.]*len(pi),S=[0.]*len(pi)))
        for a in range(len(pi)):r['R'][a]+=delta[a];r['S'][a]+=weight*pi[a]
    return rows


class ExternalFirst(VarianceSolver):
    def __init__(self,rules,native,seed=1201117):
        super().__init__(rules,native,seed,suits=True,control=False)
        self.id={**self.id,'external_sha256':sha(Path(__file__)),'sampling':'first-owner-external'}
        self.leaves=0;self.batches=0

    def snapshot(self):return {**super().snapshot(),'leaves':self.leaves,'batches':self.batches}

    def restore(self,data):
        super().restore(data);self.leaves=data['leaves'];self.batches=data['batches']

    def first_actions(self,deck,owner):
        b=betting(self.rules);holes=[deck[:2],deck[2:4]];prefix=[]
        while not b.done:
            o=self.observation(observe(b,holes[b.actor],deck[4:4+(0,3,4,5)[b.round]]))
            if b.actor==owner:return o.actions,prefix
            pi=self.row(o);action=choose(o.actions,pi,self.rng);prefix.append(action);act(b,action)
        return (),prefix

    def branch(self,deck,owner,forced,prefix=(),branch_rng=None):
        b=betting(self.rules);holes=[deck[:2],deck[2:4]]
        records=[];logq=0.;ownq=0.;reach=1.;first=True
        rng=branch_rng if branch_rng is not None else self.rng
        while not b.done:
            o=self.observation(observe(b,holes[b.actor],deck[4:4+(0,3,4,5)[b.round]]));pi=self.row(o)
            own=b.actor==owner;enumerated=own and first
            q=[.6/len(pi)+.4*p for p in pi] if own else pi
            a=forced if enumerated else (prefix[len(b.history)] if len(b.history)<len(prefix) else choose(o.actions,q,rng));index=o.actions.index(a)
            sampling=1. if enumerated else q[index]
            if own:
                # Each enumerated branch contributes one action's value but only
                # 1/n of the first-node average strategy (no n-fold overcount).
                avg=reach*math.exp(-logq)/(len(pi) if enumerated else 1)
                records.append((o,pi,index,sampling,ownq,avg,[0.]*len(pi)))
                ownq+=math.log(sampling);reach*=pi[index];first=False
            logq+=math.log(sampling);act(b,a)
            if len(b.history)>512:raise RuntimeError('path budget')
        ranks=[self.native.rank7(h+deck[4:]) for h in holes]
        utility=b.settle(ranks,b.round>=1)['net'][owner]/2
        return list(cv_updates(records,utility))

    def batch(self,owner,remaining=1024):
        # Stop before drawing chance when insufficient worst-case budget;
        # selecting only cheap sampled deals would bias the last update.
        if remaining<99:return False
        deck=self.rng.sample(range(52),9)
        actions,prefix=self.first_actions(deck,owner)
        seed=self.rng.getrandbits(128)
        if max(1,len(actions))>remaining:raise RuntimeError('HU50 action bound changed')
        pending=[]
        # The same chance and sampled pre-owner prefix are reused. Branch RNGs
        # are separate from the master stream, so no later deal reuses branch
        # uniforms. Common branch seeds reduce comparison noise. No policy
        # update until ALL legal first actions have been traversed.
        for a in actions:
            pending.extend(self.branch(deck,owner,a,prefix,random.Random(seed)))
        for key,r in combine(pending).items():
            o=r['observation'];row=self.rows.setdefault(key,dict(actions=list(o.actions),R=[0.]*len(r['R']),S=[0.]*len(r['S'])))
            for field in ('R','S'):
                row[field]=[x+y for x,y in zip(row[field],r[field])]
                if not all(math.isfinite(x) for x in row[field]):raise ArithmeticError('nonfinite external estimator')
            self.counts[key]+=1;self.visits+=1
        self.leaves+=max(1,len(actions));self.batches+=1
        if owner==1:self.iteration+=1
        return True


def train(build,source,output,seconds=2.,leaf_budget=1024,resume=None):
    import gzip,json,time
    from gto.qualification.build import load
    from gto.qualification.evaluate import atomic
    from gto.qualification.variance_study import compressed
    rules,native=load(build);s=ExternalFirst(rules,native)
    if resume:s.restore(json.loads(gzip.decompress(Path(resume).read_bytes())))
    else:s.migrate(json.loads(Path(source).read_text()))
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();first=s.leaves;last=s.leaves
    while time.monotonic()-start<seconds and s.leaves-first<leaf_budget:
        if not s.batch(s.batches%2,leaf_budget-(s.leaves-first)):break
        if s.leaves-last>=64:
            compressed(out/'orbit-external-checkpoint.json.gz',s.snapshot());last=s.leaves
    elapsed=time.monotonic()-start
    compressed(out/'orbit-external-checkpoint.json.gz',s.snapshot())
    result=dict(policy_digest=s.policy_digest,training_seconds=elapsed,leaves=s.leaves-first,
                total_leaves=s.leaves,batches=s.batches,coverage=s.coverage(),expanded_learning=False)
    atomic(out/'external-comparison.json',result)
    return result


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--source',required=True)
    p.add_argument('--output',required=True);p.add_argument('--resume');a=p.parse_args()
    print(json.dumps(train(a.build,a.source,a.output,resume=a.resume),indent=2))
