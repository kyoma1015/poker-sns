"""Independent weighted finite-law BR; no complete-native bound.
Derived from the preserved independent integrated_br oracle; only board weights change.
"""
import numpy as np
from gto.abstract import model
from gto.qualification import public_chance_solver as pcs
def measure(lib,nodes,boards,rows,*,physical=False,weights=None):
    B=len(boards);H=1081;N=len(nodes);weights=np.asarray(weights if weights is not None else [1/B]*B,dtype=float);assert np.all(weights>0) and abs(weights.sum()-1)<1e-12;blocks=[pcs.block(lib,b,float(w)) for b,w in zip(boards,weights)];out=[];ptr=lambda x:x.ctypes.data_as(model.DP)
    for owner in (0,1):
        reach=np.ones((B,N,H));v=np.zeros_like(reach);br=np.zeros_like(reach)
        for k,n in enumerate(nodes):
            if n['actor']<0:continue
            for j,c in enumerate(n['children']):
                for b in range(B):reach[b,c]=reach[b,k]*(rows[b][k]['pi'][:,j] if n['actor']!=owner else 1.)
        for k in range(N-1,-1,-1):
            n=nodes[k]
            if n['actor']<0:
                for b,block in enumerate(blocks):
                    mass=np.empty(H);win=mass.copy()
                    rc=lib.pcs_terminal(H,model.ints(block['holes'].ravel()),model.ints(block['ranks']),ptr(reach[b,k]),ptr(mass),ptr(win));assert rc==0
                    c0=n.get('c0',0);c1=n.get('c1',0)
                    x=(c0*mass+c1*win) if owner==0 else (-(c0+c1)*mass+c1*win)
                    v[b,k]=br[b,k]=x*weights[b]/1070190
            else:
                children=n['children']
                for b in range(B):v[b,k]=sum(rows[b][k]['pi'][:,j]*v[b,c] for j,c in enumerate(children)) if n['actor']==owner else v[b,children].sum(axis=0)
                if n['actor']!=owner:
                    for b in range(B):br[b,k]=br[b,children].sum(axis=0)
                else:
                    groups={};ids=[]
                    for b,block in enumerate(blocks):
                        if physical:
                            keys=[(tuple(map(int,h)),tuple(boards[b][:(0,3,4,5)[n['round']]])) for h in block['holes']]
                        else:keys=rows[b][k]['keys']
                        ids.append(np.array([groups.setdefault(key,len(groups)) for key in keys]))
                    values=np.stack([np.concatenate([br[b,c] for b in range(B)]) for c in children],axis=1);idx=np.concatenate(ids)
                    totals=np.stack([np.bincount(idx,weights=values[:,j],minlength=len(groups)) for j in range(len(children))],axis=1)
                    choices=np.argmax(totals,axis=1)[idx];picked=values[np.arange(len(idx)),choices].reshape(B,H)
                    br[:,k]=picked
        out.append(dict(EV=float(v[:,0].sum()),BR=float(br[:,0].sum())))
    assert abs(out[0]['EV']+out[1]['EV'])<1e-8
    nc=out[0]['BR']+out[1]['BR'];assert nc>=-1e-8
    return dict(EV_bb=out[0]['EV'],BR_SB_bb=out[0]['BR'],BR_BB_bb=out[1]['BR'],NashConv_bb=max(0,nc),physical_infosets=physical,full_native_BR_upper=None)


class Rows:
    """Lazily expand only the current public node, not B*N*H Python rows."""
    def __init__(self,q):self.boards=[BoardRows(q,b) for b in range(len(q.blocks))]
    def __getitem__(self,b):return self.boards[b]

class BoardRows:
    def __init__(self,q,b):self.q=q;self.b=b;self.pi=q.policy();self.last=None;self.row=None
    def __getitem__(self,k):
        if self.last==k:return self.row
        q=self.q;n=q.nodes[k]
        if n['actor']<0:return None
        count=len(n['children']);at=q.active[self.b,k]
        self.row=dict(pi=self.pi[at[:,None]+np.arange(count)],keys=[q.keys[k][(int(a)-q.base[k])//count] for a in at]);self.last=k
        return self.row

def finite_measure(q,physical=False):
    return measure(q.lib,q.nodes,[b['board'] for b in q.blocks],Rows(q),physical=physical,weights=[b['weight'] for b in q.blocks])
