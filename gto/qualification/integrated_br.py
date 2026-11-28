"""Independent vector BR on an explicitly projected native finite public tree.
No full-native upper bound: board law/action projection are part of this game.
"""
import ctypes as C,json,time
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification import public_chance_solver as pcs
from gto.qualification.native_mccfr import betting
from gto.qualification.policy import act
from gto.qualification.public_response import observe


def observations(nodes,rules):
    out=[]
    for n in nodes:
        if n['actor']<0:out.append(dict(actor=-1));continue
        b=betting(rules)
        for h in n['native_prefix']:
            while b.round<h[0]:b.next_round()
            act(b,h[2] if h[2] in (0,1) else 3 if h[2]==-3 else h[2]+2)
        while b.round<n['round']:b.next_round()
        o=observe(b,(48,49),[0,5,10,15,20][:len(([],[0,5,10],[0,5,10,15],[0,5,10,15,20])[n['round']])])
        assert o.actor==n['actor']
        out.append(dict(actor=o.actor,round=o.round,history=o.history,legal=o.actions,live=o.live,street=o.street,remaining=o.remaining,price=o.price))
    return out


def snapshot(q,nodes,obs,boards,average=True):
    answer=[];omitted=[];zero=0
    for board in boards:
        raw=q.core.snapshot(board,obs,average);rows=[]
        for n,o,r in zip(nodes,obs,raw):
            if n['actor']<0:rows.append(None);continue
            allpi=np.asarray(r['pi']);ix=[o['legal'].index(a) for a in n['native_actions']];pi=allpi[:,ix].copy();z=pi.sum(axis=1);zero+=int(np.sum(z<=0));omitted.append(float(np.max(1-z)))
            pi=np.divide(pi,z[:,None],out=np.full_like(pi,1/pi.shape[1]),where=z[:,None]>0)
            rows.append(dict(pi=pi,keys=r['keys']))
        answer.append(rows)
    return answer,dict(action_projection='condition on restricted native actions; zero-mass projection uniform, never native certificate',max_removed_mass=max(omitted,default=0),zero_mass_projected_rows=zero)


def measure(lib,nodes,boards,rows,*,physical=False):
    B=len(boards);H=1081;N=len(nodes);blocks=[pcs.block(lib,b,1/B) for b in boards];out=[];ptr=lambda x:x.ctypes.data_as(model.DP)
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
                    v[b,k]=br[b,k]=x/(B*1070190)
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


def transfer_bound(projected_nc,*,continuation_uniform_error=None,chance_uniform_error=None,omitted_gains=None,information_gains=None):
    """Conditional 2p zero-sum transfer lemma, NOT a certificate issuer.
    eps must bound payoffs uniformly over BOTH players' continuation strategies;
    an on-policy EV confidence interval is not such a bound. Missing proof =>None.
    Omitted/information deltas bound each player's additional unilateral gain.
    """
    if any(x is None for x in (continuation_uniform_error,chance_uniform_error,omitted_gains,information_gains)):return None
    vals=[projected_nc,continuation_uniform_error,chance_uniform_error,*omitted_gains,*information_gains]
    if len(omitted_gains)!=2 or len(information_gains)!=2 or not all(np.isfinite(x) and x>=0 for x in vals):raise ValueError('proved nonnegative 2player error envelopes required')
    return projected_nc+2*(continuation_uniform_error+chance_uniform_error)+sum(omitted_gains)+sum(information_gains)
