"""Exact four-arm Bayesian TYPE game; restricted signals/actions, not NLHE GTO.

Each player selects ONE complete plan at its own abstract type. Opponent type
cannot select hero action. Tensor entries already contain full joint chance.
"""
import ctypes as C,hashlib,json,math,subprocess
from dataclasses import asdict
from pathlib import Path
from gto.abstract.model import ints,doubles,IP,DP
from gto.abstract.flop_exact import U16
from gto.abstract.flop_conditional import Observation
from gto.abstract.continuation_learning import key,ARMS,payoff,FrozenContinuation
from gto.abstract.frozen_flop_reach import frozen_reach

def build(directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);source=Path(__file__).with_suffix('.cc');target=directory/'type-game.so'
 subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(source),'-o',str(target)],check=True)
 lib=C.CDLL(str(target.resolve()));lib.type_aggregate.argtypes=[C.c_int,C.c_int,C.c_int,IP,IP,IP,IP,U16,U16,DP,DP,DP];lib.type_aggregate.restype=C.c_int
 lib.type_solve.argtypes=[C.c_int,C.c_int,DP,C.c_int,C.c_uint32,DP,DP];lib.type_solve.restype=C.c_int
 lib.type_leaf.argtypes=[C.c_int,C.c_int,C.c_int,IP,IP,IP,IP,U16,U16,DP,DP,DP,IP];lib.type_leaf.restype=C.c_int
 return lib

def observations(m,reach):
 args=(m['flop'],reach['post_call_pot_bb'],reach['remaining_stack_bb'])
 return ([key(Observation(p,args[0],reach['hero_actor'],*args[1:])) for p in m['pairs']], [key(Observation(p,args[0],1-reach['hero_actor'],*args[1:])) for p in m['pairs']])

def game(lib,m,policy,stage):
 if m['n']!=1176:raise ValueError('complete fixed-flop chance required')
 r=frozen_reach(stage,policy,after_call=True);hk,vk=observations(m,r);hkeys=sorted(set(hk));vkeys=sorted(set(vk));hi=[hkeys.index(k) for k in hk];vi=[vkeys.index(k) for k in vk];bh,bv=len(hkeys),len(vkeys);out=(C.c_double*(bh*bv*2))()
 if lib.type_aggregate(m['n'],bh,bv,m['cards'],ints(m['labels']),ints(hi),ints(vi),m['win'],m['tie'],doubles(r['hero_reach']),doubles(r['villain_reach']),out):raise ValueError('type aggregation failed')
 tensor=[];actor=r['hero_actor'];pot=r['post_call_pot_bb'];remaining=r['remaining_stack_bb'];c0=[[payoff(0,a,b,actor,pot,remaining) for b in ARMS] for a in ARMS];c1=[[payoff(1,a,b,actor,pot,remaining)-c0[i][j] for j,b in enumerate(ARMS)] for i,a in enumerate(ARMS)]
 for i in range(bh):
  row=[]
  for j in range(bv):
   mass,eq=out[(i*bv+j)*2:(i*bv+j)*2+2];row.append([[mass*c0[a][b]+eq*c1[a][b] for b in range(4)] for a in range(4)])
  tensor.append(row)
 return {'hkeys':hkeys,'vkeys':vkeys,'tensor':tensor,'chance_mass':[out[i*2] for i in range(bh*bv)],'stage':stage,'flop':list(m['flop']),'scope':'exact posterior; one private type/complete-plan decision per player; public board abstracted by key','numerical_guard_bb':1e-7,'sampling_error_bb':0}

def combine(games):
 if not games:raise ValueError('nonempty research board mixture')
 hs=sorted({k for g in games for k in g['hkeys']});vs=sorted({k for g in games for k in g['vkeys']});a=[[[[0.]*4 for _ in range(4)] for _ in vs] for _ in hs]
 for g in games:
  for i,k in enumerate(g['hkeys']):
   for j,l in enumerate(g['vkeys']):
    for x in range(4):
     for y in range(4):a[hs.index(k)][vs.index(l)][x][y]+=g['tensor'][i][j][x][y]/len(games)
 return {'hkeys':hs,'vkeys':vs,'tensor':a,'research_public_board_weights':[1/len(games)]*len(games),'sampling_error_bb':0,'numerical_guard_bb':1e-7}

def strategies(g,policy):
 p=[policy.table.get(k,(.25,)*4) for k in g['hkeys']];q=[policy.table.get(k,(.25,)*4) for k in g['vkeys']]
 for row in p+q:
  if len(row)!=4 or any(not math.isfinite(v) or v<0 for v in row) or not math.isclose(math.fsum(row),1,rel_tol=0,abs_tol=1e-12):raise ValueError('normalized finite plan mixture required')
 return p,q

def evaluate(g,policy):
 p,q=strategies(g,policy);a=g['tensor'];hu=[[math.fsum(a[i][j][x][y]*q[j][y] for j in range(len(q)) for y in range(4)) for x in range(4)] for i in range(len(p))];vu=[[math.fsum(a[i][j][x][y]*p[i][x] for i in range(len(p)) for x in range(4)) for y in range(4)] for j in range(len(q))]
 value=math.fsum(p[i][x]*hu[i][x] for i in range(len(p)) for x in range(4));brh=math.fsum(max(row) for row in hu);brv=math.fsum(min(row) for row in vu);nc=brh-brv
 if min(brh-value,value-brv,nc)<-1e-7:raise ValueError('negative deviation beyond numerical guard')
 return {'profile_hero_ev_bb':value,'hero_br_ev_bb':brh,'villain_br_hero_ev_bb':brv,'hero_deviation_gain_bb':max(0.,brh-value),'villain_deviation_gain_bb':max(0.,value-brv),'restricted_nashconv_bb':max(0.,nc),'restricted_exploitability_bb':max(0.,nc)/2,'convention':'two-player zero-sum NashConv/2; only4whole plans and own key types','sampling_error_bb':0,'numerical_guard_bb':1e-7,'full_game_gto_verified':False}

def solve(lib,g,iterations,seed):
 if type(iterations) is not int or iterations<1:raise ValueError('positive full-sweep iterations required')
 bh,bv=len(g['hkeys']),len(g['vkeys']);flat=[v for row in g['tensor'] for m in row for arm in m for v in arm];avg=(C.c_double*((bh+bv)*4))();reg=(C.c_double*((bh+bv)*4))()
 if lib.type_solve(bh,bv,doubles(flat),iterations,seed,avg,reg):raise ValueError('type regret learning failed')
 ks=g['hkeys']+g['vkeys'];p=FrozenContinuation({k:tuple(x/math.fsum(avg[i*4:i*4+4]) for x in avg[i*4:i*4+4]) for i,k in enumerate(ks)});result=evaluate(g,p);bound=math.fsum(max(0.,max(reg[i*4:i*4+4])) for i in range(bh+bv))/iterations
 result.update(iterations=iterations,initialization_seed=seed,positive_external_regret_bound_bb=bound)
 if result['restricted_nashconv_bb']>bound+1e-7:raise ValueError('full-sweep regret identity failed')
 return p,result

def fixed_opponents(g,learned):
 out=[];p,q=strategies(g,learned)
 for name,choose in [('uniform',lambda k:(.25,)*4),*[(f'pure_arm_{a}',lambda k,a=a:tuple(float(i==a) for i in range(4))) for a in range(4)],('own_strength',lambda k:tuple(float(i==(2 if k[3] else 3)) for i in range(4)))]:
  fixed={k:choose(k) for k in g['hkeys']+g['vkeys']};hero=FrozenContinuation({**learned.table,**{k:fixed[k] for k in g['vkeys']}});villain=FrozenContinuation({**learned.table,**{k:fixed[k] for k in g['hkeys']}});h=evaluate(g,hero);v=evaluate(g,villain)
  out.append({'opponent':name,'hero_vs_fixed_ev_bb':h['profile_hero_ev_bb'],'hero_br_vs_fixed_bb':h['hero_br_ev_bb'],'hero_improvement_bb':h['hero_deviation_gain_bb'],'villain_vs_fixed_hero_ev_bb':v['profile_hero_ev_bb'],'villain_br_hero_ev_bb':v['villain_br_hero_ev_bb'],'villain_improvement_bb':v['villain_deviation_gain_bb']})
 return out

def research_leaf(lib,m,preflop,stage,continuation):
 """Actual-flop classpair payoff hook; NOT an averaged real-deal CFR kernel.

No range weights in leaf cells: CFR must supply its own chance/reach. Existing
CFR arrays are never changed. Selected-board averaging is explicitly forbidden.
"""
 r=frozen_reach(stage,preflop,after_call=True);hk,vk=observations(m,r);hs=sorted(set(hk));vs=sorted(set(vk));hi=[hs.index(k) for k in hk];vi=[vs.index(k) for k in vk];c0=[];c1=[]
 for h in hs:
  for v in vs:
   p=continuation.table.get(h,(.25,)*4);q=continuation.table.get(v,(.25,)*4)
   def val(e):return math.fsum(p[i]*q[j]*payoff(e,a,b,r['hero_actor'],r['post_call_pot_bb'],r['remaining_stack_bb']) for i,a in enumerate(ARMS) for j,b in enumerate(ARMS))
   lo=val(0);c0.append(lo);c1.append(val(1)-lo)
 out=(C.c_double*(169*169))();counts=(C.c_int*(169*169))()
 if lib.type_leaf(m['n'],len(hs),len(vs),m['cards'],ints(m['labels']),ints(hi),ints(vi),m['win'],m['tie'],doubles(c0),doubles(c1),out,counts):raise ValueError('leaf export failed')
 sb_chips=[0.]*(169*169);sign=1 if r['hero_actor']==0 else -1
 for i in range(169):
  for j in range(169):sb_chips[(i*169+j) if r['hero_actor']==0 else (j*169+i)]=sign*2*out[i*169+j]
 return {'schema':'research-actual-flop-leaf-v1','flop':list(m['flop']),'stage':stage,'sb_net_chips_by_class_pair':sb_chips,'hero_net_bb_by_class_pair':list(out),'compatible_hole_counts':list(counts),'zero_count_cells':'UNREACHABLE;0 payoff placeholder is not an EV estimate','scope':'RESEARCH ONLY; caller must integrate true public-board chance; not connected to frozen CFR','sampling_error_bb':0,'numerical_guard_bb':1e-7,'full_game_gto_verified':False}
