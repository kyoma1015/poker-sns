"""Frozen bounded solver policy on native observations; explicit legal backoff.
Unknown histories use the preserved sparse controller, never an implicit fold.
Backoff is not evidence of strategic safety or an error bound.
"""
from collections import Counter
import numpy as np
from gto.qualification import active_chance as ac,fullstreet_solver as fs
from gto.qualification.native_mccfr import digest

class Policy:
    def __init__(self,q,fallback,identity):
        self.q=q;self.fallback=fallback;self.native=fallback.native;self.rules=fallback.rules
        self.pi=q.policy();self.stats={r:Counter() for r in range(4)};self.cache={}
        self.known={(n['round'],tuple(tuple(h) for h in n['native_prefix'])):k for k,n in enumerate(q.nodes) if n['actor']>=0}
        self.ancestors=[[] for n in q.nodes]
        for k,n in enumerate(q.nodes):
            for c in n['children']:self.ancestors[c]=self.ancestors[k]+([k] if n['actor']>=0 else [])
        self.lookup=[];self.backoff=[]
        for k,n in enumerate(q.nodes):
            if n['actor']<0:self.lookup.append({});self.backoff.append({});continue
            count=len(n['children']);keys=q.keys[k];self.lookup.append({key:q.base[k]+j*count for j,key in enumerate(keys)})
            sums={};weights={}
            for b,block in enumerate(q.blocks):
                for h,at in enumerate(q.active[b,k]):
                    coarse=keys[(int(at)-q.base[k])//count][0];w=block['weight']/1081
                    sums.setdefault(coarse,np.zeros(count));weights[coarse]=weights.get(coarse,0)+w;sums[coarse]+=w*self.pi[at:at+count]
            self.backoff.append({code:v/weights[code] for code,v in sums.items()})
        self._digest=digest(dict(identity=identity,fallback=fallback.policy_digest,pi_sha256=__import__('hashlib').sha256(self.pi.astype('<f8').tobytes()).hexdigest(),backoff='chance-weighted parent average; off-tree preserved Sparse'))
    @property
    def policy_digest(self):return self._digest
    def row(self,o,average=False):
        if len(o.live)!=2 or any(o.live[p]+o.remaining[p]!=100 for p in (0,1)) or any(o.dead):raise ValueError('HU50 zero-ante/rake research only')
        r=o.round;self.stats[r]['queries']+=1
        k=self.known.get((r,tuple(tuple(h[:3]) for h in o.history)))
        if k is None:
            self.stats[r]['offtree']+=1;return self.fallback.row(o,True)
        n=self.q.nodes[k]
        if n['actor']!=o.actor or any(a not in o.actions for a in n['native_actions']):raise ValueError('exact native ledger/action mismatch')
        def coarse(round):
            key=(o.own,o.board[:(0,3,4,5)[round]])
            if key not in self.cache:
                if len(self.cache)>16384:self.cache.clear()
                self.cache[key]=fs.signal(self.q.lib,*key)
            return (fs.public_code(key[1])>>(3-round))*(169<<round)+(self.cache[key]>>(3-round))
        memory=[]
        for a in self.ancestors[k]+[k]:
            na=self.q.nodes[a];ra=na['round']
            if na['actor']==o.actor and ra and (a,coarse(ra)) in self.q.splits:memory.append((a,ac.feature(self.q.lib,o.own,o.board[:(0,3,4,5)[ra]])))
        code=coarse(r);key=(code,tuple(memory));at=self.lookup[k].get(key)
        if at is None:
            self.stats[r]['unseen_refinement']+=1;values=self.backoff[k].get(code)
            if values is None:self.stats[r]['unseen_parent']+=1;return self.fallback.row(o,True)
        else:
            self.stats[r]['indexed_row']+=1;values=self.pi[at:at+len(n['children'])]
            end=at+len(values)
            if hasattr(self.q,'initial_average'):
                self.stats[r]['average_updated_row']+=int(self.q.A[at:end].sum()>self.q.initial_average[at:end].sum()+1e-14)
                self.stats[r]['regret_changed_row']+=int(np.max(abs(self.q.R[at:end]-self.q.initial_regret[at:end]))>1e-14)
            self.stats[r]['CF_reached_row']+=int(self.q.visits[at]>0)
        weights=dict(zip(n['native_actions'],values));answer=[float(weights.get(a,0.)) for a in o.actions]
        if abs(sum(answer)-1)>1e-10 or min(answer)<0:raise ValueError('normalized legal native response')
        return answer
