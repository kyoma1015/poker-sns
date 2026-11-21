"""Immutable root-class chance batches and legal action-family priors. Research."""
import math,random,time
from collections import Counter
from pathlib import Path
from gto.abstract.model import classes
from gto.qualification.first_external import FirstExternalSolver
from gto.qualification.action_baseline import ActionBaselineSolver
from gto.qualification.native_mccfr import matching,choose,betting
from gto.qualification.public_response import observe
from gto.qualification.policy import sha

GROUPS=classes()

def family_prior(actions):
    groups=[[a for a in actions if a==0],[a for a in actions if a==1],[a for a in actions if a not in (0,1)]]
    groups=[g for g in groups if g]
    return [next(1/(len(groups)*len(g)) for g in groups if a in g) for a in actions]

def chance_plan(rng,groups=GROUPS):
    plan=[];total=sum(map(len,groups));n=len(groups)
    for k in rng.sample(range(n),n):
        own=list(rng.choice(groups[k]));remaining=[c for c in range(52) if c not in own]
        plan.append((own+rng.sample(remaining,7),[rng.getrandbits(128) for _ in (0,1)],n*len(groups[k])/total))
    return plan

def adaptive_probabilities(masses,visits,missing):
    priority=[float(m) for m in missing] if any(missing) else [1/math.sqrt(v+1) for v in visits]
    total=math.fsum(priority)
    return [.2*p+.8*w/total for p,w in zip(masses,priority)]

class CoverageSolver(FirstExternalSolver):
    def __init__(self,rules,native,*,external=False,family=False,adaptive=False):
        super().__init__(rules,native);self.external,self.family=external,family;self.macro_batches=0
        self.adaptive=adaptive;self.class_visits=[0]*len(GROUPS);self.root_keys=None;self.chance_weight_max=0.
        self.id={**self.id,'coverage_source_sha256':sha(Path(__file__)),'first_external':external,
            'untrained_prior':'equal-legal-action-family' if family else 'uniform-all-legal',
            'chance':('adaptive positive root-class q; exact mass/q' if adaptive else '169-strata frozen pair strategy; 169*combo_mass corrections')}
    def row(self,o,average=False):
        o=self.observation(o);r=self.rows.get(o.key);field='S' if average and not self.current_behavior else 'R'
        if self.family and (r is None or math.fsum(max(0,x) for x in r[field])<=0):return family_prior(o.actions)
        return ActionBaselineSolver.row(self,o,average)
    def collect(self,owner,deck,rng):
        return (FirstExternalSolver.collect if self.external else ActionBaselineSolver.collect)(self,owner,deck,rng)
    def snapshot(self):return {**super().snapshot(),'macro_batches':self.macro_batches,'class_visits':self.class_visits[:],'chance_weight_max':self.chance_weight_max}
    def restore(self,d):
        super().restore(d);self.macro_batches=d['macro_batches'];self.class_visits=d['class_visits'][:];self.chance_weight_max=d['chance_weight_max']
    def step(self):
        if not self.adaptive:return super().step()
        if self.root_keys is None:
            b=betting(self.rules)
            self.root_keys=[self.observation(observe(b,g[0],[])).key for g in GROUPS]
        masses=[len(g)/1326 for g in GROUPS]
        missing=[not (self.rows.get(k) and math.fsum(self.rows[k]['S'])>0) for k in self.root_keys]
        q=adaptive_probabilities(masses,self.class_visits,missing)
        k=choose(list(range(len(GROUPS))),q,self.rng);weight=masses[k]/q[k]
        own=list(self.rng.choice(GROUPS[k]));deck=own+self.rng.sample([c for c in range(52) if c not in own],7)
        seeds=[self.rng.getrandbits(128) for _ in (0,1)]
        batches=[self.collect(p,deck,random.Random(seeds[p])) for p in (0,1)]
        pending={};rc=Counter();sc=Counter();visits=0
        for grads,avgs in batches:
            for o,pi,delta,_ in grads:
                row=pending.setdefault(o.key,dict(actions=list(o.actions),R=[0.]*len(pi),S=[0.]*len(pi)))
                row['R']=[x+weight*y for x,y in zip(row['R'],delta)];rc[o.key]+=1;visits+=1
            for o,pi,w in avgs:
                row=pending.setdefault(o.key,dict(actions=list(o.actions),R=[0.]*len(pi),S=[0.]*len(pi)))
                row['S']=[x+weight*w*y for x,y in zip(row['S'],pi)];sc[o.key]+=1
        self._publish(pending,rc,sc,visits,1)
        self.class_visits[k]+=1;self.chance_weight_max=max(self.chance_weight_max,weight)

    def _publish(self,pending,rc,sc,visits,n):
        for k,delta in pending.items():
            old=self.rows.get(k)
            for f in ('R','S'):
                if old:delta[f]=[x+y for x,y in zip(old[f],delta[f])]
                if not all(math.isfinite(x) for x in delta[f]):raise ArithmeticError('nonfinite batch')
        self.rows.update(pending);self.counts.update(rc);self.average_counts.update(sc)
        self.iteration+=n;self.average_iterations+=n;self.visits+=visits

    def batch(self,timeout=30):
        start=time.monotonic();plan=chance_plan(self.rng);pending={};rc=Counter();sc=Counter();visits=0
        for deck,seeds,weight in plan:
            if time.monotonic()-start>timeout:raise TimeoutError('incomplete chance batch; no row updates applied')
            for owner in (0,1):
                grads,avgs=self.collect(owner,deck,random.Random(seeds[owner]))
                for o,pi,delta,_ in grads:
                    k=o.key;row=pending.setdefault(k,dict(actions=list(o.actions),R=[0.]*len(pi),S=[0.]*len(pi)))
                    row['R']=[x+weight*y for x,y in zip(row['R'],delta)];rc[k]+=1;visits+=1
                for o,pi,w in avgs:
                    k=o.key;row=pending.setdefault(k,dict(actions=list(o.actions),R=[0.]*len(pi),S=[0.]*len(pi)))
                    row['S']=[x+weight*w*y for x,y in zip(row['S'],pi)];sc[k]+=1
        # Publish only after all169 strata and finite checks; no adaptive target leakage.
        self._publish(pending,rc,sc,visits,len(plan));self.macro_batches+=1
        return len(plan)
