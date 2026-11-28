"""Depth-first independent weighted private-vector BR on a finite public catalog.
Same game/infosets as stream_br, without B*N*H reach/value/BR matrices. Opponent
reach is propagated causally; each owner infoset integrates worlds BEFORE max.
No complete-native chance/action/abstraction certificate is implied.
"""
import numpy as np
from gto.abstract import model

def measure(q,physical=False):
    B=len(q.blocks);H=1081;pi=q.policy();ptr=lambda x:x.ctypes.data_as(model.DP);groups={};results=[]
    holes=[model.ints(b['holes'].ravel()) for b in q.blocks];ranks=[model.ints(b['ranks']) for b in q.blocks]
    def group(k):
        n=q.nodes[k];r=n['round'];tag=('physical',r) if physical else ('abstract',id(q.keys[k]))
        if tag not in groups:
            if physical:
                lookup={};ids=[]
                for b in q.blocks:
                    board=tuple(b['board'][:(0,3,4,5)[r]])
                    for h in b['holes']:
                        key=(tuple(map(int,h)),board);ids.append(lookup.setdefault(key,len(lookup)))
                groups[tag]=(np.asarray(ids),len(lookup))
            else:
                ids=((q.active[:,k]-q.base[k])//len(n['children'])).ravel();groups[tag]=(ids,len(q.keys[k]))
        return groups[tag]
    for owner in (0,1):
        def walk(k,reach):
            n=q.nodes[k]
            if n['actor']<0:
                v=np.empty((B,H))
                for b,block in enumerate(q.blocks):
                    mass=np.empty(H);win=np.empty(H);opponent=np.ascontiguousarray(reach[b]);rc=q.lib.pcs_terminal(H,holes[b],ranks[b],ptr(opponent),ptr(mass),ptr(win))
                    if rc:raise ValueError('independent CF terminal')
                    c0=n.get('c0',0);c1=n.get('c1',0);scale=block['weight']/1070190
                    v[b]=scale*(c0*mass+c1*win if owner==0 else -(c0+c1)*mass+c1*win)
                return v,v
            count=len(n['children']);probs=pi[q.active[:,k,:,None]+np.arange(count)];values=[];responses=[]
            for a,c in enumerate(n['children']):
                v,br=walk(c,reach if n['actor']==owner else reach*probs[:,:,a]);values.append(v);responses.append(br)
            if n['actor']!=owner:return np.sum(values,axis=0),np.sum(responses,axis=0)
            v=sum(probs[:,:,a]*x for a,x in enumerate(values));idx,t=group(k);scores=np.stack([np.bincount(idx,weights=x.ravel(),minlength=t) for x in responses],axis=1);choice=np.argmax(scores,axis=1)[idx];stack=np.stack(responses,axis=-1).reshape(B*H,count);best=stack[np.arange(B*H),choice].reshape(B,H)
            return v,best
        v,br=walk(0,np.ones((B,H)));results.append((float(v.sum()),float(br.sum())))
    if abs(results[0][0]+results[1][0])>1e-8:raise ValueError('independent zero-sum EV')
    nc=results[0][1]+results[1][1]
    if nc< -1e-8:raise ValueError('BR below on-policy value')
    return dict(EV_bb=results[0][0],BR_SB_bb=results[0][1],BR_BB_bb=results[1][1],NashConv_bb=max(0,nc),physical_infosets=physical,full_native_BR_upper=None,scope='exact finite-catalog/private-pair/public-support BR; full target chance error UNKNOWN')

def refinement_envelope(q):
    coarse=measure(q);fine=measure(q,True);gaps=[fine['BR_SB_bb']-coarse['BR_SB_bb'],fine['BR_BB_bb']-coarse['BR_BB_bb']]
    if min(gaps)< -1e-8:raise ValueError('information refinement cannot lower BR')
    assert abs(fine['NashConv_bb']-coarse['NashConv_bb']-sum(gaps))<1e-8
    return dict(coarse=coarse,fine=fine,exact_same_policy_finite_information_gains=gaps,finite_fine_NC_upper=coarse['NashConv_bb']+sum(gaps),full_native_NC_upper=None,chance_error_upper=None,omitted_size_error_upper=None,continuation_error_upper=None)
