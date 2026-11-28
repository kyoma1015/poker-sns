"""Fast streamed active layouts with exact carry of persistent optimizer rows.
Chance banks may change; raw weighted updates remain in the existing kernel.
"""
import gc
import numpy as np
from gto.qualification import active_chance as ac,stream_chance as sc,stream_index as fast
class Game(sc.Game):
    """Global active rows; only one board's CF state resides in the C++ kernel.
    Chunk-local BR maxima are a board-revealed relaxation, NOT restricted NC.
    Exact shared-information BR is evaluated separately by stream_br.
    """
    def __init__(self,lib,nodes,blocks,splits=(),previous=None):
        if not blocks or abs(sum(b['weight'] for b in blocks)-1)>1e-12:raise ValueError('normalized public law')
        self.lib,self.nodes,self.blocks,self.C=lib,nodes,blocks,169;self.splits=set(map(tuple,splits));self.t=0;self.P=0
        self.keys=[None if n['actor']<0 else [] for n in nodes];lookup=[{} for _ in nodes];chunks=[];shared={}
        for b in blocks:
            q=fast.Game(lib,nodes,[dict(b,weight=1.)],self.splits);local_ids=[];local_cache={}
            for st,t,n,k in q.rows:
                sig=q.partition_signatures[k]
                if sig not in shared:
                    keys=list(previous.keys[k]) if previous is not None else []
                    shared[sig]=(keys,{key:j for j,key in enumerate(keys)})
                self.keys[k],lookup[k]=shared[sig]
                if sig not in local_cache:
                    ids=[]
                    for key in q.keys[k]:
                        if key not in lookup[k]:lookup[k][key]=len(self.keys[k]);self.keys[k].append(key)
                        ids.append(lookup[k][key])
                    local_cache[sig]=np.asarray(ids,dtype=np.int32)
                local_ids.append((st,local_cache[sig],n,k))
            q.keys=None;q.observations=None;q.parent_rows=None
            q.R=q.A=q.prior=q.visits=None
            chunks.append((q,local_ids,float(b['weight'])))
        self.base=[];self.prebase=[];self.rows=[];self.S=0
        for k,n in enumerate(nodes):
            self.base.append(self.S);self.prebase.append(self.P if n['actor']>=0 and n['round']==0 else -1)
            if n['actor']<0:continue
            count=len(n['children']);t=len(self.keys[k]);self.rows.append((self.S,t,count,k));self.S+=t*count
            if n['round']==0:self.P+=169*count
        self.R=np.zeros(self.S);self.A=np.zeros(self.S);self.prior=np.zeros(self.S,dtype=float);self.visits=np.zeros(self.S,dtype=np.uint16)
        self.grad=np.zeros(self.S);self.avg=np.zeros(self.S);self.den=np.zeros(self.S);self.num=np.zeros(self.P);self.evden=np.zeros(self.P)
        for st,t,n,k in self.rows:self.prior[st:st+t*n]=1/n
        self.chunks=[];active=[]
        for q,ids,weight in chunks:
            mapping=np.empty(q.S,dtype=np.int32)
            for st,gids,n,k in ids:mapping[st:st+len(gids)*n]=(self.base[k]+gids[:,None]*n+np.arange(n)).ravel()
            a=np.full_like(q.active,-1);valid=q.active>=0;a[valid]=mapping[q.active[valid]];active.append(a)
            q.active=None;self.chunks.append((q,mapping,weight))
        self.active=np.concatenate(active);del chunks,lookup;gc.collect()
        self.estimate_bytes=self.active.nbytes+self.S*70+max(q.estimate_bytes for q,_,_ in self.chunks)
        if self.estimate_bytes>1536*1024**2:raise MemoryError('1.5GiB numeric streaming budget (Python keys measured separately)')

        if previous is not None:
            # Prefix key order is retained exactly at each public node. New cells
            # get zero accumulators, not pseudohistory. Off-bank old rows persist.
            for st,t,n,k in previous.rows:
                dst=self.base[k];end=t*n
                self.R[dst:dst+end]=previous.R[st:st+end];self.A[dst:dst+end]=previous.A[st:st+end];self.prior[dst:dst+end]=previous.prior[st:st+end];self.visits[dst:dst+end]=previous.visits[st:st+end]
            self.t=previous.t

    def save(self,path):
        from pathlib import Path
        path=Path(path);tmp=path.with_suffix('.tmp.npz');np.savez_compressed(tmp,R=self.R,A=self.A,prior=self.prior,visits=self.visits,t=np.array(self.t));tmp.replace(path)

    def restore(self,path):
        super().restore(path)
        with np.load(path) as d:
            if 'prior' not in d or d['prior'].shape!=(self.S,):raise ValueError('explicit streaming prior required')
            self.prior=d['prior'].copy()


def parent_tables(q,current=False):
    # The rule is frozen BEFORE the next chance draw. It depends only on past
    # optimizer state and observable coarse information, never the new runout.
    pi=q.policy(not current);tables=[]
    for k,n in enumerate(q.nodes):
        if n['actor']<0:tables.append({});continue
        count=len(n['children']);keys=q.keys[k];t=len(keys);st=q.base[k];mass=np.zeros(t)
        for b,block in enumerate(q.blocks):mass+=np.bincount((q.active[b,k]-st)//count,minlength=t)*block['weight']/1081
        code=np.array([key[0] for key in keys]);unique,inv=np.unique(code,return_inverse=True);den=np.bincount(inv,weights=mass);p=pi[st:st+t*count].reshape(t,count)
        sums=np.stack([np.bincount(inv,weights=mass*p[:,j],minlength=len(unique)) for j in range(count)],axis=1)
        tables.append({int(c):row/d for c,row,d in zip(unique,sums,den) if d>0})
    return tables


def replace_bank(previous,blocks,*,average_snapshot=False):
    table=parent_tables(previous,current=not average_snapshot)
    q=Game(previous.lib,previous.nodes,blocks,previous.splits,previous=previous);q.prior=q.prior.astype(float,copy=False)
    for st,t,n,k in q.rows:
        oldt=len(previous.keys[k]);p=q.prior[st:st+t*n].reshape(t,n)
        for j in range(oldt,t):p[j]=table[k].get(q.keys[k][j][0],np.ones(n)/n)
    q.initial_average=np.zeros(q.S);q.initial_regret=np.zeros(q.S)
    return q


def reset_target(q):
    # Fixed-catalog regrets are NOT unbiased history for the full52 public law.
    # Preserve behavior as a tie-breaking prior, reset optimizer only on this
    # explicit target-law change. Subsequent fresh banks carry R/A exactly.
    q.prior=q.policy().copy();q.R.fill(0);q.A.fill(0);q.visits.fill(0);q.t=0
    q.initial_average=np.zeros(q.S);q.initial_regret=np.zeros(q.S)
