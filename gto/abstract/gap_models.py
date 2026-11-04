"""Independent ledger reference, controlled model perturbations and board chance."""
import ctypes as C
import itertools,math,random,subprocess
from pathlib import Path
from gto.abstract import continuation_game as base,range_features as features
from gto.abstract.continuation_learning import FrozenContinuation
from gto.abstract.flop_conditional import Observation,validate_flop
from gto.abstract.flop_exact import U16
from gto.abstract.model import ints,doubles,IP,DP,classes


def build(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);src=Path(__file__).with_name('gap_reference.cc');dest=root/'gap-reference.so';subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(src),'-o',str(dest)],check=True);lib=C.CDLL(str(dest.resolve()));lib.gap_forms.argtypes=[C.c_int,C.c_int,C.c_double,C.c_double,C.c_double,DP];lib.gap_forms.restype=C.c_int
 lib.gap_reference.argtypes=[C.c_int,C.c_int,C.c_int,C.c_int,IP,IP,IP,IP,U16,U16,DP,DP,DP,DP,C.c_int,C.c_double,C.c_double,C.c_double,DP,DP,IP,DP];lib.gap_reference.restype=C.c_int
 lib.gap_board_chance.argtypes=[C.c_int,IP,IP,DP,DP,DP,DP];lib.gap_board_chance.restype=C.c_int;lib.gap_direct_mass.argtypes=[C.c_int,IP,IP,DP,DP,IP,DP];lib.gap_direct_mass.restype=C.c_int
 lib.gap_exact_reference.argtypes=[IP,IP,C.POINTER(C.c_uint64)];lib.gap_exact_reference.restype=C.c_int;lib.gap_rank7.argtypes=[IP];lib.gap_rank7.restype=C.c_uint64
 lib.gap_solve.argtypes=[C.c_int,C.c_int,C.c_int,DP,DP,C.c_int,DP,DP];lib.gap_solve.restype=C.c_int;return lib

def forms(lib,actions,actor,pot,remaining,fraction):
 out=(C.c_double*(actions*actions*2))()
 if lib.gap_forms(actions,actor,pot,remaining,fraction,out):raise ValueError('invalid research cashflow context')
 return [(out[i*2],out[i*2+1]) for i in range(actions*actions)]

def make_game(aggregate_lib,reference_lib,m,reach,book,variant):
 pot=reach['post_call_pot_bb'];remaining=reach['remaining_stack_bb']*variant['stack_scale'];actor=reach['hero_actor'];actions=variant['arms'];basekeys=[[features.signal(Observation(p,m['flop'],seat,pot,reach['remaining_stack_bb']),book) for p in m['pairs']] for seat in (actor,1-actor)]
 def rename(k):return (*k[:2],remaining,*k[3:12],round(remaining/pot,8),*k[13:])
 keys=[[rename(k) for k in rows] for rows in basekeys];hs,vs=[sorted(set(rows)) for rows in keys];hm={k:i for i,k in enumerate(hs)};vm={k:i for i,k in enumerate(vs)};hi=[hm[k] for k in keys[0]];vi=[vm[k] for k in keys[1]];nh,nv=len(hs),len(vs);mom=(C.c_double*(nh*nv*2))();rh=reach['hero_reach'] if variant['range']=='actual' else [1.]*169;rv=reach['villain_reach'] if variant['range']=='actual' else [1.]*169
 if aggregate_lib.type_aggregate(m['n'],nh,nv,m['cards'],ints(m['labels']),ints(hi),ints(vi),m['win'],m['tie'],doubles(rh),doubles(rv),mom):raise ValueError('model chance aggregation failed')
 f=forms(reference_lib,actions,actor,pot,remaining,variant['bet_fraction']);tensor=[[[[mom[(i*nv+j)*2]*f[a*actions+b][0]+mom[(i*nv+j)*2+1]*(f[a*actions+b][1]-f[a*actions+b][0]) for b in range(actions)] for a in range(actions)] for j in range(nv)] for i in range(nh)]
 return {'hkeys':hs,'vkeys':vs,'tensor':tensor,'chance_mass':[mom[2*i] for i in range(nh*nv)],'actions':actions,'flop':list(m['flop']),'stage':reach['stage'],'pair_hi':hi,'pair_vi':vi,'base_key_map':{rename(k):k for rows in basekeys for k in rows},'hero_reach':rh,'villain_reach':rv,'hero_actor':actor,'pot':pot,'remaining':remaining,'fraction':variant['bet_fraction'],'variant':variant['name'],'raises_available':min(pot*variant['bet_fraction'],remaining)<remaining-1e-12}

def lift(policy,g):
 return FrozenContinuation({k:(*policy.table[g['base_key_map'][k]],*([0.]*(g['actions']-4))) for k in g['hkeys']+g['vkeys']})

def strategies(g,p):
 rows=[]
 for k in g['hkeys']+g['vkeys']:
  v=p.table[k]
  if len(v)!=g['actions'] or any(not math.isfinite(x) or x<0 for x in v) or not math.isclose(math.fsum(v),1,abs_tol=1e-12):raise ValueError('normalized explicit own-type strategy required')
  rows.append(v)
 return rows[:len(g['hkeys'])],rows[len(g['hkeys']):]

def evaluate(g,policy):
 p,q=strategies(g,policy);a=g['tensor'];A=g['actions'];hu=[[math.fsum(a[i][j][x][y]*q[j][y] for j in range(len(q)) for y in range(A)) for x in range(A)] for i in range(len(p))];vu=[[math.fsum(a[i][j][x][y]*p[i][x] for i in range(len(p)) for x in range(A)) for y in range(A)] for j in range(len(q))];value=math.fsum(p[i][x]*hu[i][x] for i in range(len(p)) for x in range(A));brh=math.fsum(max(v) for v in hu);brv=math.fsum(min(v) for v in vu)
 if min(brh-value,value-brv,brh-brv)<-1e-7:raise ValueError('invalid restricted best-response interval')
 return {'profile_hero_ev_bb':value,'hero_br_ev_bb':brh,'villain_br_hero_ev_bb':brv,'restricted_nashconv_bb':max(0.,brh-brv),'restricted_exploitability_bb':max(0.,brh-brv)/2,'sampling_error_bb':0,'full_game_gto_verified':False}

def solve(lib,g,prior,iterations):
 if type(iterations) is not int or not 1<=iterations<=10000000:raise ValueError('bounded positive sweeps required')
 p,q=strategies(g,prior);A=g['actions'];keys=g['hkeys']+g['vkeys'];avg=(C.c_double*(len(keys)*A))();reg=(C.c_double*(len(keys)*A))()
 if lib.gap_solve(len(p),len(q),A,doubles([v for row in g['tensor'] for cell in row for arm in cell for v in arm]),doubles([v for row in p+q for v in row]),iterations,avg,reg):raise ValueError('research response rejected inputs')
 out=FrozenContinuation({k:tuple(v/math.fsum(avg[i*A:i*A+A]) for v in avg[i*A:i*A+A]) for i,k in enumerate(keys)});metric=evaluate(g,out);bound=math.fsum(max(0.,max(reg[i*A:i*A+A])) for i in range(len(keys)))/iterations
 if metric['restricted_nashconv_bb']>bound+1e-7:raise ValueError('generic regret bound identity failed')
 metric.update(iterations=iterations,positive_external_regret_bound_bb=bound);return out,metric

def reference(lib,m,g,policy):
 p,q=strategies(g,policy);A=g['actions'];nh,nv=len(p),len(q);out=(C.c_double*((nh+nv)*(A+1)))();leaf=(C.c_double*(169*169))();count=(C.c_int*(169*169))();z=(C.c_double*1)()
 if lib.gap_reference(m['n'],nh,nv,A,m['cards'],ints(m['labels']),ints(g['pair_hi']),ints(g['pair_vi']),m['win'],m['tie'],doubles(g['hero_reach']),doubles(g['villain_reach']),doubles([v for row in p for v in row]),doubles([v for row in q for v in row]),g['hero_actor'],g['pot'],g['remaining'],g['fraction'],out,leaf,count,z):raise ValueError('independent concrete-pair reference failed')
 targets={}
 for i,k in enumerate(g['hkeys']+g['vkeys']):
  mass=out[i*(A+1)];targets[k]={'mass':mass/z[0],'ev':[out[i*(A+1)+a+1]/mass for a in range(A)] if mass>0 else None}
 value=math.fsum(t['mass']*math.fsum(a*b for a,b in zip(t['ev'],policy.table[k])) for k,t in targets.items() if k in set(g['hkeys']) and t['ev'] is not None);brh=math.fsum(t['mass']*max(t['ev']) for k,t in targets.items() if k in set(g['hkeys']) and t['ev'] is not None);brv=-math.fsum(t['mass']*max(t['ev']) for k,t in targets.items() if k in set(g['vkeys']) and t['ev'] is not None)
 return {'targets':targets,'class_leaf_hero_net_bb':list(leaf),'compatible_class_pair_counts':list(count),'raw_reach_mass':z[0],'metrics':{'profile_hero_ev_bb':value,'hero_br_ev_bb':brh,'villain_br_hero_ev_bb':brv,'restricted_nashconv_bb':brh-brv}}

def full_pairs():
 pairs=[];labels=[]
 for h,group in enumerate(classes()):pairs.extend(group);labels.extend([h]*len(group))
 return pairs,labels,ints([c for p in pairs for c in p])

def board_chance(lib,reach):
 pairs,labels,cards=full_pairs();out=(C.c_double*22100)();z=(C.c_double*1)()
 if lib.gap_board_chance(len(pairs),cards,ints(labels),doubles(reach['hero_reach']),doubles(reach['villain_reach']),out,z):raise ValueError('board chance normalization failed')
 return {'flops':[list(b) for b in itertools.combinations(range(52),3)],'probabilities':list(out),'raw_preflop_reach_mass':z[0],'sum':math.fsum(out),'conditional_history':reach['history']+['call'],'sampling_error':0,'all_boards_is_chance_support_not_unseen_strategy_test':True}

def direct_mass(lib,reach,flop):
 validate_flop(flop);pairs,labels,cards=full_pairs();z=(C.c_double*1)()
 if lib.gap_direct_mass(len(pairs),cards,ints(labels),doubles(reach['hero_reach']),doubles(reach['villain_reach']),ints(flop),z):raise ValueError('direct physical deal sum failed')
 return z[0]

def rank_checks(lib,m,seed,count):
 rng=random.Random(seed+sum((i+1)*c for i,c in enumerate(sorted(m['flop'])))*7919);chosen=set();rows=[]
 while len(rows)<count:
  i=rng.randrange(m['n']);legal=[j for j,p in enumerate(m['pairs']) if not set(p)&set(m['pairs'][i])];j=rng.choice(legal)
  if (i,j) in chosen:continue
  chosen.add((i,j));out=(C.c_uint64*3)()
  if lib.gap_exact_reference(ints([*m['pairs'][i],*m['pairs'][j]]),ints(m['flop']),out):raise ValueError('independent exact rank reference failed')
  expected=(m['win'][i*m['n']+j],m['tie'][i*m['n']+j],990-m['win'][i*m['n']+j]-m['tie'][i*m['n']+j]);rows.append({'holes':[*m['pairs'][i],*m['pairs'][j]],'reference_counts':list(out),'matrix_counts':list(expected),'mismatch':tuple(out)!=expected,'runouts':990})
 return rows
