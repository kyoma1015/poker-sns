"""Cached causal active partitions; same active C++ kernel/row semantics.
Nodes with identical observable partitions share immutable key metadata, never
regret/average values or public histories. Original active Game is unchanged.
"""
import numpy as np
from gto.qualification import active_chance as ac,stream_features

class Game(ac.Game):
    def __init__(self,lib,nodes,blocks,splits=()):
        self.lib,self.nodes,self.blocks,self.C=lib,nodes,blocks,169;self.splits=set(map(tuple,splits));self.t=0;self.P=0
        self.active=np.full((len(blocks),len(nodes),1081),-1,dtype=np.int32);self.keys=[None]*len(nodes);self.base=[];self.prebase=[];self.rows=[];self.spans=[];self.parent_rows=[]
        ancestors=[[] for _ in nodes]
        for k,n in enumerate(nodes):
            for c in n['children']:ancestors[c]=ancestors[k]+([k] if n['actor']>=0 else [])
        bynode={}
        for k,c in self.splits:bynode.setdefault(k,set()).add(c)
        self.observations={(b,r):stream_features.features(block['holes'],block['board'][:(0,3,4,5)[r]]) for b,block in enumerate(blocks) for r in (1,2,3)}
        codes=[np.asarray(b['codes']) for b in blocks];coarse={(b,r):(block['public']>>(3-r))*(169<<r)+(codes[b]>>(3-r)) for b,block in enumerate(blocks) for r in range(4)}
        partitions={};self.partition_signatures=[];S=0
        for k,n in enumerate(nodes):
            self.base.append(S);self.prebase.append(self.P if n['round']==0 and n['actor']>=0 else -1)
            if n['actor']<0:self.spans.append(0);self.partition_signatures.append(None);continue
            r=n['round'];selected=tuple((a,tuple(sorted(bynode[a]))) for a in ancestors[k]+[k] if a in bynode and nodes[a]['actor']==n['actor'])
            sig=(r,selected);self.partition_signatures.append(sig)
            if sig not in partitions:
                if not selected:
                    values=np.concatenate([coarse[b,r] for b in range(len(blocks))]);u,first,inv=np.unique(values,return_index=True,return_inverse=True);order=np.argsort(first);renumber=np.empty(len(u),dtype=np.int32);renumber[order]=np.arange(len(u));keys=[(int(u[j]),()) for j in order];ids=renumber[inv].reshape(len(blocks),1081)
                else:
                    groups={};keys=[];ids=np.empty((len(blocks),1081),dtype=np.int32)
                    for b in range(len(blocks)):
                        for h in range(1081):
                            memory=tuple((a,self.observations[b,nodes[a]['round']][h]) for a,allowed in selected if int(coarse[b,nodes[a]['round']][h]) in bynode[a])
                            key=(int(coarse[b,r][h]),memory);gid=groups.setdefault(key,len(groups));ids[b,h]=gid
                            if gid==len(keys):keys.append(key)
                partitions[sig]=(keys,ids)
            keys,ids=partitions[sig];count=len(n['children']);self.keys[k]=keys;self.active[:,k]=S+ids*count
            self.rows.append((S,len(keys),count,k));span=len(keys)*count;self.spans.append(span);S+=span
            if r==0:self.P+=169*count
        self.S=S;self.prior=np.zeros(S,dtype=np.float32);self.R=np.zeros(S);self.A=np.zeros(S);self.visits=np.zeros(S,dtype=np.uint16)
        for st,t,n,k in self.rows:self.prior[st:st+t*n]=1/n
        self.grad=np.zeros(S);self.avg=np.zeros(S);self.den=np.zeros(S);self.num=np.zeros(self.P);self.evden=np.zeros(self.P)
        self.estimate_bytes=self.active.nbytes+S*54+len(blocks)*len(nodes)*1081*8*5
        if self.estimate_bytes>512*1024**2:raise MemoryError('same512MiB active kernel budget')
        self.use_blocks(blocks)

    def use_blocks(self,blocks):
        from gto.abstract import model
        if abs(sum(b['weight'] for b in blocks)-1)>1e-12:raise ValueError('normalized chance weights')
        if hasattr(self,'static') and [b['board'] for b in blocks]!=[b['board'] for b in self.blocks]:raise ValueError('reindex a different board bank')
        self.blocks=blocks;nodes=self.nodes;offsets=np.cumsum([0]+[len(n['children']) for n in nodes])
        values=[[n['actor'] for n in nodes],offsets,[c for n in nodes for c in n['children']],[n['round'] for n in nodes],self.base,self.prebase,[b['public'] for b in blocks],[1081]*len(blocks),np.arange(len(blocks))*1081,[0]*len(blocks),np.concatenate([b['codes'] for b in blocks]),self.active.ravel(),self.spans,np.concatenate([b['holes'].ravel() for b in blocks]),np.concatenate([b['ranks'] for b in blocks])]
        # Keep NumPy owners alive: no per-element ctypes conversion/copy of the
        # multi-million-entry active index on every new public chance batch.
        self._static_arrays=[np.ascontiguousarray(v,dtype=np.int32) for v in values];self.static=[v.ctypes.data_as(model.IP) for v in self._static_arrays]
        self._float_arrays=[np.asarray([b['weight'] for b in blocks],dtype=float),np.asarray([n.get('c0',0.) for n in nodes],dtype=float),np.asarray([n.get('c1',0.) for n in nodes],dtype=float)]
        self.weights,self.c0,self.c1=[v.ctypes.data_as(model.DP) for v in self._float_arrays]
