"""Exact suit-orbit reuse and unbiased known-payoff baseline for native MCCFR.

Legacy solver/source/checkpoints remain unchanged. Migration explicitly creates
another policy; no claim that pooling preserves an asymmetric source policy.
"""
import copy
from collections import Counter
from dataclasses import replace
from functools import lru_cache
import itertools
import json
import math
from pathlib import Path
from gto.qualification.native_mccfr import Solver, identity, betting, choose, digest
from gto.qualification.policy import act, sha
from gto.qualification.public_response import Observation, observe

PERMUTATIONS=tuple(itertools.permutations(range(4)))

@lru_cache(maxsize=4096)
def canonical_cards(own, board):
    def mapped(p):
        hand=tuple(sorted(c//4*4+p[c%4] for c in own))
        cards=tuple(c//4*4+p[c%4] for c in board)
        # Flop order carries no game information; turn/river order does.
        return hand,tuple(sorted(cards[:3]))+cards[3:]
    return min(mapped(p) for p in PERMUTATIONS)


def canonical(o):
    own,board=canonical_cards(o.own,o.board)
    return replace(o,own=own,board=board)


def cv_updates(records, utility):
    """Recursive baseline-corrected outcome estimator; zero baseline = old OS.

    Each baseline is fixed before the current sample. Opponent q=sigma. At an
    owner node, v_a=b_a+1[a=sample]*(child-b_a)/q_a; v=sum sigma_a*v_a.
    Prefix own sampling reach corrects counterfactual regrets. Chance is sampled
    from its actual law. Average sums are unchanged by the control variate.
    """
    value=utility
    for o,pi,index,q,log_prefix,avg_weight,baseline in reversed(records):
        estimates=list(baseline)
        estimates[index]+=(value-baseline[index])/q
        value=math.fsum(p*x for p,x in zip(pi,estimates))
        scale=math.exp(-log_prefix)
        yield o,pi,[(x-value)*scale for x in estimates],avg_weight


class VarianceSolver(Solver):
    def __init__(self,rules,native,seed=1201117,*,suits=False,control=False):
        super().__init__(rules,native,seed)
        self.suits,self.control=suits,control
        self.id={**self.id,'extension_sha256':sha(Path(__file__)),
                 'key':'exact-suit-orbit' if suits else 'raw',
                 'baseline':'exact-fold' if control else 'zero'}
        self.counts=Counter();self.origin=None;self.gradient_sums={}

    def observation(self,o): return canonical(o) if self.suits else o

    def row(self,o,average=False): return super().row(self.observation(o),average)

    def migrate(self,data):
        if data['identity']!=identity():raise ValueError('legacy identity mismatch')
        self.origin=digest(data); self.iteration=data['iteration'];self.visits=data['visits']
        def tuples(x):return tuple(tuples(v) for v in x) if isinstance(x,list) else x
        self.rng.setstate(tuples(data['rng']))
        self.rows={}
        for key,old in data['rows'].items():
            d=json.loads(key)
            for k in ('own','board','remaining','street','live','dead','folded','actions'):d[k]=tuple(d[k])
            d['history']=tuple(tuple(h) for h in d['history'])
            new=self.observation(Observation(**d)).key
            row=self.rows.setdefault(new,dict(actions=old['actions'][:],R=[0.]*len(old['R']),S=[0.]*len(old['S'])))
            if row['actions']!=old['actions']:raise ValueError('orbit action mismatch')
            for k in ('R','S'):row[k]=[x+y for x,y in zip(row[k],old[k])]

    def snapshot(self):
        return {**super().snapshot(),'origin':self.origin,'counts':dict(self.counts)}

    def restore(self,data):
        super().restore(data);self.origin=data['origin'];self.counts=Counter(data['counts'])

    def trajectory(self,owner,*,update=True):
        deck=self.rng.sample(range(52),9);holes=[deck[:2],deck[2:4]]
        b=betting(self.rules);records=[];logq=0.;ownq=0.;reach=1.
        while not b.done:
            o=self.observation(observe(b,holes[b.actor],deck[4:4+(0,3,4,5)[b.round]]))
            pi=super().row(o);n=len(pi)
            q=[.6/n+.4*p for p in pi] if b.actor==owner else pi
            action=choose(o.actions,q,self.rng);index=o.actions.index(action)
            if b.actor==owner:
                baseline=[-(o.live[owner]+o.dead[owner])/2 if self.control and a==0 else 0. for a in o.actions]
                records.append((o,pi,index,q[index],ownq,reach*math.exp(-logq),baseline))
                ownq+=math.log(q[index]);reach*=pi[index]
            logq+=math.log(q[index]);act(b,action)
            if len(b.history)>512:raise RuntimeError('path budget')
        ranks=[self.native.rank7(h+deck[4:]) for h in holes]
        utility=b.settle(ranks,b.round>=1)['net'][owner]/2
        norm=0.
        for o,pi,delta,weight in cv_updates(records,utility):
            norm+=math.fsum(x*x for x in delta)
            if not update:
                sums=self.gradient_sums.setdefault(o.key,[0.]*len(delta))
                for a,x in enumerate(delta):sums[a]+=x
                continue
            row=self.rows.setdefault(o.key,dict(actions=list(o.actions),R=[0.]*len(pi),S=[0.]*len(pi)))
            for a in range(len(pi)):
                row['R'][a]+=delta[a];row['S'][a]+=weight*pi[a]
            if not all(math.isfinite(x) for x in row['R']+row['S']):raise ArithmeticError('nonfinite estimator')
            self.counts[o.key]+=1;self.visits+=1
        return norm

    def coverage(self):
        n=sum(self.counts.values());unique=len(self.counts)
        return dict(updates=n,distinct_updated_infosets=unique,total_infosets=len(self.rows),
                    repeated_updates=n-unique,revisit_rate=(n-unique)/n if n else 0,
                    max_updates_per_infoset=max(self.counts.values(),default=0),
                    root_updated_infosets=sum(not json.loads(k)['history'] for k in self.counts))
