"""Causal CF-residual refinement of the existing streamed active CFR+ game.
Unchanged information rows retain exact optimizer history. New information rows
start R/A0 with the frozen old policy as explicit prior; no fictitious split CF.
"""
import gc
from types import SimpleNamespace
import numpy as np
from gto.abstract import model
from gto.qualification import stream_sampling as ss,stream_features,active_chance as ac,fullstreet_solver as fs,stream_measure
from gto.qualification import sampling_policy
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha
from pathlib import Path

def ancestor_code(code,r,ra):
    if not 0<=ra<=r<=3:raise ValueError('causal observation prefix')
    return ((code//(169<<r))>>(r-ra))*(169<<ra)+((code%(169<<r))>>(r-ra))

def project(key,k,nodes,old_splits):
    code,memory=key;r=nodes[k]['round']
    return (code,tuple((a,f) for a,f in memory if (a,ancestor_code(code,r,nodes[a]['round'])) in old_splits))

class Parent:
    def __init__(self,p):
        self.p=p;self.nodes=p.q.nodes;self.splits=p.q.splits
    def values(self,k,key):
        key=project(key,k,self.nodes,self.splits);n=len(self.nodes[k]['children']);at=self.p.lookup[k].get(key)
        if at is not None:return self.p.pi[at:at+n]
        return self.p.backoff[k].get(key[0],np.ones(n)/n)
    def slim(self):
        # Preserve serving behavior and true touched-row diagnostics, not full
        # training matrices/chunks. Numeric magnitudes are used only in p.pi.
        q=self.p.q
        self.p.q=SimpleNamespace(nodes=q.nodes,keys=q.keys,lib=q.lib,splits=q.splits,
            visits=q.visits,R=(q.R!=0).astype(np.uint8),A=(q.A>0).astype(np.uint8),
            initial_average=np.zeros(q.S,dtype=np.uint8),initial_regret=np.zeros(q.S,dtype=np.uint8))


def change(q,splits,parent):
    new=ss.Game(q.lib,q.nodes,q.blocks,set(q.splits)|set(splits),previous=q)
    fill_new(new,q,parent);return new

def fill_new(q,previous,parent):
    for st,t,n,k in q.rows:
        first=len(previous.keys[k]);rows=q.prior[st:st+t*n].reshape(t,n)
        for j in range(first,t):rows[j]=parent.values(k,q.keys[k][j])
    q.initial_average=np.zeros(q.S);q.initial_regret=np.zeros(q.S)

def next_bank(q,blocks,parent):
    new=ss.Game(q.lib,q.nodes,blocks,q.splits,previous=q);fill_new(new,q,parent);return new

class Policy:
    def __init__(self,q,parent,identity):
        self.base=sampling_policy.Policy(q,parent.p.fallback.base,identity);self.parent=parent
        self.native=parent.p.native;self.rules=parent.p.rules;self.stats=self.base.stats
        self.policy_digest=digest(dict(child=self.base.policy_digest,parent=parent.p.policy_digest,source=sha(Path(__file__))))
    def row(self,o,average=False):
        p=self.base;k=p.known.get((o.round,tuple(tuple(h[:3]) for h in o.history)))
        if k is not None:
            def code(r):
                z=(o.own,o.board[:(0,3,4,5)[r]])
                if z not in p.cache:p.cache[z]=fs.signal(p.q.lib,*z)
                return (fs.public_code(z[1])>>(3-r))*(169<<r)+(p.cache[z]>>(3-r))
            memory=tuple((a,ac.feature(p.q.lib,o.own,o.board[:(0,3,4,5)[p.q.nodes[a]['round']]])) for a in p.ancestors[k]+[k] if p.q.nodes[a]['actor']==o.actor and p.q.nodes[a]['round'] and (a,code(p.q.nodes[a]['round'])) in p.q.splits)
            if (code(o.round),memory) in p.lookup[k]:return p.row(o,True)
        s=self.stats[o.round];s['queries']+=1;s['parent_delegate']+=1
        before=dict(self.parent.p.stats[o.round]);v=self.parent.p.row(o,True)
        for key in ('average_updated_row','regret_changed_row'):
            s['parent_'+key]+=self.parent.p.stats[o.round][key]-before.get(key,0)
        return v


def scores(q,rounds=(2,3)):
    """Local deviation CF heterogeneity under frozen sigma. Not a BR bound.
    Opponent reach/card removal/chance are exact on the declared finite catalog.
    New feature partitions refine full OLD keys, never merge previous memory.
    """
    B=len(q.blocks);H=1081;pi=q.policy();ptr=lambda x:x.ctypes.data_as(model.DP)
    holes=[model.ints(b['holes'].ravel()) for b in q.blocks];ranks=[model.ints(b['ranks']) for b in q.blocks];features={};groups={};answer=[]
    for r in rounds:
        lookup={};ids=[]
        for b in q.blocks:
            for f in stream_features.features(b['holes'],b['board'][:(0,3,4,5)[r]]):ids.append(lookup.setdefault(f,len(lookup)))
        features[r]=(np.asarray(ids),len(lookup))
    for owner in (0,1):
        def walk(k,reach,own):
            n=q.nodes[k]
            if n['actor']<0:
                v=np.empty((B,H))
                for b,block in enumerate(q.blocks):
                    m=np.empty(H);w=np.empty(H);p=np.ascontiguousarray(reach[b]);rc=q.lib.pcs_terminal(H,holes[b],ranks[b],ptr(p),ptr(m),ptr(w))
                    if rc:raise ValueError('independent terminal CF')
                    c0=n.get('c0',0);c1=n.get('c1',0);v[b]=block['weight']/1070190*(c0*m+c1*w if owner==0 else -(c0+c1)*m+c1*w)
                return v
            count=len(n['children']);probs=pi[q.active[:,k,:,None]+np.arange(count)];values=[]
            for a,c in enumerate(n['children']):values.append(walk(c,reach if n['actor']==owner else reach*probs[:,:,a],own*probs[:,:,a] if n['actor']==owner else own))
            if n['actor']!=owner:return np.sum(values,axis=0)
            r=n['round']
            if r in rounds:
                tag=(id(q.keys[k]),r)
                if tag not in groups:
                    old=((q.active[:,k]-q.base[k])//count).ravel();fid,F=features[r];pairs,inv=np.unique(np.stack((old,fid),axis=1),axis=0,return_inverse=True);groups[tag]=(old,pairs[:,0],inv)
                old,coarse,inv=groups[tag];cf=np.stack([v.ravel() for v in values],axis=1);fine=np.stack([np.bincount(inv,weights=cf[:,a],minlength=len(coarse)) for a in range(count)],axis=1)
                total=np.stack([np.bincount(old,weights=cf[:,a],minlength=len(q.keys[k])) for a in range(count)],axis=1)
                gaps=np.bincount(coarse,weights=fine.max(axis=1),minlength=len(q.keys[k]))-total.max(axis=1)
                aggregated={}
                for j,g in enumerate(gaps):
                    c=q.keys[k][j][0]
                    if (k,c) not in q.splits and g>1e-12:aggregated[c]=aggregated.get(c,0.)+float(g)
                live=np.empty((B,H))
                for b,block in enumerate(q.blocks):
                    h=block['holes'];cards=np.bincount(h.ravel(),weights=np.repeat(reach[b],2),minlength=52)
                    mass=reach[b].sum()-cards[h[:,0]]-cards[h[:,1]]+reach[b]
                    live[b]=block['weight']/1070190*mass*own[b]
                byrow=np.bincount(old,weights=live.ravel(),minlength=len(q.keys[k]))
                for c,g in aggregated.items():answer.append(dict(node=k,coarse=c,round=r,owner=owner,CF_gap=g,on_policy_reach=sum(float(byrow[j]) for j,key in enumerate(q.keys[k]) if key[0]==c)))
            return sum(probs[:,:,a]*v for a,v in enumerate(values))
        walk(0,np.ones((B,H)),np.ones((B,H)))
    return sorted(answer,key=lambda x:x['CF_gap'],reverse=True)
