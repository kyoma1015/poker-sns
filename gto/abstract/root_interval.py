"""Readonly root EV/BR intervals. Unknown cells are bounded, never zero-filled."""
import ctypes as C,math,subprocess,hashlib
from pathlib import Path
from functools import lru_cache
from gto.abstract import model,street_tree as st
from gto.abstract.model import ints,doubles,IP,DP


def build(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);target=root/'root-coeff.so';subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(Path(__file__).with_suffix('.cc')),'-o',str(target)],check=True);lib=C.CDLL(str(target.resolve()));lib.root_coeff.argtypes=[C.c_int,C.c_int,C.c_int,IP,IP,IP,DP,DP,DP,DP,DP];lib.root_coeff.restype=C.c_int;return lib


def coefficients(lib,g,policy):
 args=st._args(g,policy);size=g['h']*g['v'];a=(C.c_double*size)();b=(C.c_double*size)()
 if lib.root_coeff(*args[:8],args[-1],a,b):raise ValueError('invalid behavioral coefficient game')
 return list(a),list(b)


@lru_cache(maxsize=1)
def full_counts():return tuple(model.chance(model.classes())[0])


def class_partial(lib,coefflib,m,g,policy,hero_actor,hero_reach,villain_reach,profile):
 a,b=coefficients(coefflib,g,policy);base=g['game'];out=(C.c_double*(169*169))();counts=(C.c_int*(169*169))()
 if lib.type_leaf(m['n'],g['h'],g['v'],m['cards'],ints(m['labels']),ints(base['pair_hi']),ints(base['pair_vi']),m['win'],m['tie'],doubles(a),doubles(b),out,counts):raise ValueError('unweighted class-pair aggregation failed')
 mass=math.fsum(counts[i*169+j]*hero_reach[i]*villain_reach[j] for i in range(169) for j in range(169));value=math.fsum(out[i*169+j]*counts[i*169+j]*hero_reach[i]*villain_reach[j] for i in range(169) for j in range(169))/mass;error=abs(value-profile)
 if error>1e-8:raise ValueError('class-pair/scalar fixed-profile EV disagreement')
 known=[0.]*(169*169);covered=[0.]*(169*169);full=full_counts();sign=1 if hero_actor==0 else -1
 for i in range(169):
  for j in range(169):
   k=i*169+j;pos=k if hero_actor==0 else j*169+i;q=counts[k]/(full[k]*17296) if full[k] else 0.;covered[pos]=q;known[pos]=sign*out[k]*q
 return known,covered,error


def evaluate(lib,nodes,policy,prob,lower,upper,n):
 size=len(nodes)*n*n
 if len(lower)!=size or len(upper)!=size or len(prob)!=n*n or len(policy)!=len(nodes)*3*n:raise ValueError('root interval dimensions')
 if any(not math.isfinite(a+b) or a>b for a,b in zip(lower,upper)):raise ValueError('ordered finite payoff bounds required')
 before=hashlib.sha256(doubles(policy)).hexdigest();rows=[]
 for leaf in (lower,upper):
  ev=(C.c_double*(len(nodes)*3*n))();reach=(C.c_double*(len(nodes)*n))();out=(C.c_double*4)()
  if lib.abstract_evaluate(n,len(nodes),ints([x['actor'] for x in nodes]),ints([len(x['actions']) for x in nodes]),ints([c for x in nodes for c in (x['children']+[-1]*3)[:3]]),doubles(prob),doubles(leaf),doubles(policy),ev,reach,out):raise ValueError('readonly root evaluation failed')
  rows.append([float(v) for v in out])
 if before!=hashlib.sha256(doubles(policy)).hexdigest():raise ValueError('frozen preflop policy changed')
 lo,hi=rows
 if any(a>b+1e-7 for a,b in zip(lo[:3],hi[:3])):raise ValueError('root EV/BR monotonicity failed')
 return {'profile_sb_ev_interval': [lo[0],hi[0]],'sb_preflop_br_ev_interval':[lo[1],hi[1]],'bb_preflop_br_sb_ev_interval':[lo[2],hi[2]],'preflop_nashconv_interval':[max(0.,lo[1]-hi[2]),max(0.,hi[1]-lo[2])],'sb_deviation_gain_interval':[max(0.,lo[1]-hi[0]),max(0.,hi[1]-lo[0])],'bb_deviation_gain_interval':[max(0.,lo[0]-hi[2]),max(0.,hi[0]-lo[2])],'policy_digest_before':before,'policy_digest_after':before,'policy_updated':False}


def root_bounds(lib,pi,kernels):
 nodes=model.tree();n=169;lower=[0.]*(len(nodes)*n*n);upper=list(lower);by_leaf={r['leaf_index']:data for r,data in kernels}
 for k,node in enumerate(nodes):
  if node['actor']>=0:continue
  if not node['matched']:low=[float(node['value'])]*(n*n);high=low
  else:
   data=by_leaf.get(k);known=data['known_sb_bb'] if data else [0.]*(n*n);mass=data['class_board_probability'] if data else [0.]*(n*n)
   if any(not 0<=p<=1+1e-12 for p in mass):raise ValueError('invalid class conditional coverage')
   low=[2*(v-50*(1-p)-1e-7) for v,p in zip(known,mass)];high=[2*(v+50*(1-p)+1e-7) for v,p in zip(known,mass)]
  lower[k*n*n:(k+1)*n*n]=low;upper[k*n*n:(k+1)*n*n]=high
 result=evaluate(lib,nodes,pi,model.chance(model.classes())[1],lower,upper,n)
 for k,v in result.items():
  if isinstance(v,list):result[k]=[x/2 for x in v]
 result.update(units='BB before blinds',scope='169-class preflop-only BR; fixed postflop profiles, no suit-specific or fullNLHE BR guarantee',unknown_matched_cells='±50BB, not zero',kernel_uses_new_boards_only=True,real_game_approximation_error='UNKNOWN',external_gto_comparison='NOT PERFORMED');return result


def respond_until(lib,g,budgets,threshold):
 prior=st.uniform(g);args=st._args(g,prior);size=len(prior);reg=(C.c_double*size)();sums=(C.c_double*size)();avg=(C.c_double*size)();out=(C.c_double*5)();start=0;trace=[]
 for stop in budgets:
  if stop<=start or lib.street_train(*args,start,stop,reg,sums,avg,out):raise ValueError('incremental response update failed')
  m=st._metrics(out);m.update(iterations=stop,positive_counterfactual_regret_bound_bb=out[4]);trace.append(m)
  if m['restricted_nashconv_bb']>out[4]+1e-7:raise ValueError('counterfactual regret bound failed')
  if m['restricted_nashconv_bb']<=threshold:break
  start=stop
 return trace
