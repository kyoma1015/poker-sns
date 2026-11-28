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
