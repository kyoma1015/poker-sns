"""Matched own-information games, chance-weighted projection and floor bounds.

Chance is conditional on frozen public preflop history. Rich references expose
only a player's OWN holes, never the opponent's realized private cards.
"""
import ctypes as C
import math
from gto.abstract.model import ints,doubles
from gto.abstract.flop_conditional import Observation
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.continuation_learning import ARMS,payoff,FrozenContinuation
from gto.abstract.range_features import signal
from gto.abstract import continuation_game as base


def game(lib,m,pi,stage,book,hero='range23',villain='range23'):
 r=frozen_reach(stage,pi,after_call=True);pot,stack=r['post_call_pot_bb'],r['remaining_stack_bb'];actor=r['hero_actor']
 def keys(seat,mode):
  result=[]
  for pair in m['pairs']:
   k=signal(Observation(pair,m['flop'],seat,pot,stack),book)
   result.append(k if mode=='range23' else k[:20] if mode=='uniform20' else (seat,pot,stack,*sorted(pair)))
  return result
 hk,vk=keys(actor,hero),keys(1-actor,villain);hs,vs=sorted(set(hk)),sorted(set(vk));hm={k:i for i,k in enumerate(hs)};vm={k:i for i,k in enumerate(vs)};bh,bv=len(hs),len(vs);out=(C.c_double*(bh*bv*2))()
 if lib.type_aggregate(m['n'],bh,bv,m['cards'],ints(m['labels']),ints([hm[k] for k in hk]),ints([vm[k] for k in vk]),m['win'],m['tie'],doubles(r['hero_reach']),doubles(r['villain_reach']),out):raise ValueError('factorial chance aggregation failed')
 lo=[[payoff(0,a,b,actor,pot,stack) for b in ARMS] for a in ARMS];delta=[[payoff(1,a,b,actor,pot,stack)-lo[i][j] for j,b in enumerate(ARMS)] for i,a in enumerate(ARMS)]
 tensor=[[[[out[2*(i*bv+j)]*lo[a][b]+out[2*(i*bv+j)+1]*delta[a][b] for b in range(4)] for a in range(4)] for j in range(bv)] for i in range(bh)]
 return {'hkeys':hs,'vkeys':vs,'tensor':tensor,'chance_mass':[out[i*2] for i in range(bh*bv)],'stage':stage,'flop':list(m['flop']),'sampling_error_bb':0,'numerical_guard_bb':1e-7}


def reindex(g,transform):
 """Sum joint-chance weighted utilities; never normalize each hidden type pair."""
 hs=sorted({transform(k) for k in g['hkeys']});vs=sorted({transform(k) for k in g['vkeys']});hm={k:i for i,k in enumerate(hs)};vm={k:i for i,k in enumerate(vs)}
 a=[[[[0.]*4 for _ in range(4)] for _ in vs] for _ in hs];mass=[0.]*(len(hs)*len(vs))
 for i,k in enumerate(g['hkeys']):
  h=hm[transform(k)]
  for j,l in enumerate(g['vkeys']):
   v=vm[transform(l)];mass[h*len(vs)+v]+=g['chance_mass'][i*len(g['vkeys'])+j]
   for x in range(4):
    for y in range(4):a[h][v][x][y]+=g['tensor'][i][j][x][y]
 return {**g,'hkeys':hs,'vkeys':vs,'tensor':a,'chance_mass':mass}


def project(g,p,transform):
 """Own-type marginal projection. Opponent private information is integrated."""
 accum={};weights={};nv=len(g['vkeys'])
 for side in ('hkeys','vkeys'):
  for i,k in enumerate(g[side]):
   w=math.fsum(g['chance_mass'][i*nv+j] for j in range(nv)) if side=='hkeys' else math.fsum(g['chance_mass'][j*nv+i] for j in range(len(g['hkeys'])))
   c=transform(k);accum.setdefault(c,[0.]*4);weights[c]=weights.get(c,0.)+w
   for arm in range(4):accum[c][arm]+=w*p.table[k][arm]
 return FrozenContinuation({k:tuple(x/weights[k] for x in v) if weights[k]>0 else (.25,)*4 for k,v in accum.items()})


def structure_key(k):return (*k[:9],0,0,0,*k[12:])


def mix(games):
 """Equal RESEARCH board mixture with own-type marginal masses retained."""
 hs=sorted({k for g in games for k in g['hkeys']});vs=sorted({k for g in games for k in g['vkeys']});hm={k:i for i,k in enumerate(hs)};vm={k:i for i,k in enumerate(vs)};a=[[[[0.]*4 for _ in range(4)] for _ in vs] for _ in hs];mass=[0.]*(len(hs)*len(vs))
 for g in games:
  for i,k in enumerate(g['hkeys']):
   h=hm[k]
   for j,l in enumerate(g['vkeys']):
    v=vm[l];mass[h*len(vs)+v]+=g['chance_mass'][i*len(g['vkeys'])+j]/len(games)
    for x in range(4):
     for y in range(4):a[h][v][x][y]+=g['tensor'][i][j][x][y]/len(games)
 return {'hkeys':hs,'vkeys':vs,'tensor':a,'chance_mass':mass,'sampling_error_bb':0,'numerical_guard_bb':1e-7}


def information_floor(lib,rich_coarse,coarse_rich,iterations,seed):
 """Certified bracket for min coarse-profile NC measured with richer own types.

min NC = min_qC max_pR u - max_pC min_qR u = V(R,C)-V(C,R).
Full-sweep regrets bound asymmetric saddle values independently. This bound is
NOT a positive lower bound on the coarse game's own NashConv or full NLHE.
"""
 _,a=base.solve(lib,rich_coarse,iterations,seed);_,b=base.solve(lib,coarse_rich,iterations,seed)
 lower=max(0.,a['villain_br_hero_ev_bb']-b['hero_br_ev_bb']-2e-7)
 upper=max(0.,a['hero_br_ev_bb']-b['villain_br_hero_ev_bb']+2e-7)
 return {'minimum_richer_reference_nashconv_lower_bb':lower,'constructive_upper_bb':upper,'asymmetric_rich_coarse':a,'asymmetric_coarse_rich':b,'absolute_0_1_impossible_in_reference':lower>.1,'absolute_0_1_constructively_feasible_in_reference':upper<=.1,'full_game_gto_verified':False}
