"""HU50BB research abstraction; never a full-game GTO certificate."""
import ctypes as C
import hashlib,json,math,subprocess,tempfile,time
from array import array
from itertools import combinations
from pathlib import Path
from gto.hand169 import CLASSES,hand_class
from gto.native.hand169_bridge import card_name

ROOT=Path(__file__).resolve().parents[2]
CONDITION={'players':2,'stacks_chips':[100,100],'bb_chips':2,'sb_chips':1,'ante':0,'rake':0,
 'raise_to_chips':[5,18,42,100],'private_abstraction':'169 starting classes; exact compatible-combo chance mass',
 'postflop_abstraction':'one half-pot flop bet, own-hand/public-flop fixed controllers; turn/river check-through',
 'formal_profile':False,'full_game_gto_verified':False}

def build(directory):
 from gto.native.build_reconstructed import decode,AUXILIARY
 directory=Path(directory);directory.mkdir(exist_ok=True,parents=True)
 source=decode('g11_rules_embed.h')
 if hashlib.sha256(source).hexdigest()!=AUXILIARY['g11_rules_embed.h'][1]:raise ValueError('reused rank source pin differs')
 # Reuse only the existing pure C++ five/seven-card ranking functions.
 ranks=source.decode().split('static V five(',1)[1].rsplit('}',1)[0]
 (directory/'rank_reused.h').write_text('static V five('+ranks)
 output=directory/'abstract.so';code=Path(__file__).with_name('core.cc')
 command=['c++','-std=c++17','-O3','-shared','-fPIC',str(code),'-I'+str(directory),'-o',str(output)]
 subprocess.run(command,check=True)
 metadata={'compiler':subprocess.check_output(['c++','--version'],text=True).splitlines()[0],'binary_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(code.read_bytes()).hexdigest(),'rank_source_sha256':hashlib.sha256(source).hexdigest(),'command':command}
 (directory/'manifest.json').write_text(json.dumps(metadata,sort_keys=True)+'\n');return output

IP=C.POINTER(C.c_int);DP=C.POINTER(C.c_double)
def ints(values):return (C.c_int*len(values))(*values)
def doubles(values):return (C.c_double*len(values))(*values)

def load(path):
 lib=C.CDLL(str(Path(path).resolve()))
 lib.abstract_rank.argtypes=[IP,C.c_int];lib.abstract_rank.restype=C.c_uint64
 lib.abstract_kernel.argtypes=[C.c_int,IP,IP,C.c_int,C.c_int,DP,DP];lib.abstract_kernel.restype=C.c_int
 lib.abstract_solve.argtypes=[C.c_int,C.c_int,IP,IP,IP,DP,DP,C.c_int,DP,DP,DP,DP];lib.abstract_solve.restype=C.c_int
 lib.abstract_evaluate.argtypes=[C.c_int,C.c_int,IP,IP,IP,DP,DP,DP,DP,DP,DP];lib.abstract_evaluate.restype=C.c_int
 return lib

def rank(lib,cards):
 if len(cards) not in (5,7) or len(set(cards))!=len(cards) or any(type(c) is not int or not 0<=c<52 for c in cards):raise ValueError('five/seven distinct cards')
 return lib.abstract_rank(ints(cards),len(cards))

def classes():
 groups={k:[] for k in CLASSES}
 for pair in combinations(range(52),2):groups[hand_class([card_name(c) for c in pair])].append(pair)
 return [groups[k] for k in CLASSES]

def chance(groups):
 # Inclusion/exclusion: intersecting exactly once subtracted once; identical
 # combos subtracted twice and restored once. Ordered seat assignments.
 incidence=[[sum(c in pair for pair in g) for c in range(52)] for g in groups]
 counts=[len(a)*len(b)-sum(x*y for x,y in zip(incidence[i],incidence[j]))+(len(a) if i==j else 0)
         for i,a in enumerate(groups) for j,b in enumerate(groups)]
 total=1326*1225
 if len(groups)==169 and sum(counts)!=total:raise ValueError('full-deck blocker mass differs')
 return counts,[x/total for x in counts]

def kernel(lib,*,samples,seed):
 if type(samples) is not int or not 2<=samples<=100000 or type(seed) is not int or not 0<=seed<2**31:raise ValueError('bounded explicit sample design')
 groups=classes();offset=[0];cards=[]
 for g in groups:cards.extend(c for pair in g for c in pair);offset.append(offset[-1]+len(g))
 size=5*169*169;mean=(C.c_double*size)();variance=(C.c_double*size)();start=time.monotonic()
 if lib.abstract_kernel(169,ints(offset),ints(cards),samples,seed,mean,variance):raise ValueError('kernel calculation failed')
 return {'seed':seed,'samples_per_class_pair':samples,'mean':list(mean),'variance':list(variance),'seconds':time.monotonic()-start,
  'models':['allin_showdown','flop_controller_2','flop_controller_5','flop_controller_18','flop_controller_42'],
  'confidence':.99,'simultaneous_kernel_radius_chips':min(200.,200*math.sqrt(math.log(2*size/.01)/(2*samples))),
  'sampling_scope':'conditional uniform compatible hole combos and board without replacement; swapped-seat paired worlds',
  'full_game_accuracy_verified':False}

def tree():
 nodes=[]
 def terminal(value,matched=False):
  index=len(nodes);nodes.append({'actor':-1,'value':value,'matched':matched,'actions':[],'children':[]});return index
 def node(sb,bb,actor,raises,history):
  index=len(nodes);n={'actor':actor,'contributions':[sb,bb],'raises':raises,'history':list(history),'actions':[],'children':[]};nodes.append(n)
  facing=(sb if actor==0 else bb)<max(sb,bb)
  if facing:n['actions'].append('fold');n['children'].append(terminal(-sb if actor==0 else bb))
  n['actions'].append('call' if facing else 'check')
  if not history and actor==0:n['children'].append(node(2,2,1,0,(*history,'call')))
  else:n['children'].append(terminal(max(sb,bb),True))
  if raises<4:
   target=(5,18,42,100)[raises]
   if target<=max(sb,bb) or target-max(sb,bb)<(2 if raises==0 else (3,13,24)[raises-1]):raise ValueError('illegal abstract raise')
   n['actions'].append('raise_to_'+str(target));n['children'].append(node(target if actor==0 else sb,target if actor==1 else bb,1-actor,raises+1,(*history,'raise_to_'+str(target))))
  return index
 node(1,2,0,0,());return nodes

def solve(lib,payoffs,probability,nodes,*,iterations,n=169):
 if type(iterations) is not int or not 1<=iterations<=1000000 or not 1<=n<=169:raise ValueError('bounded full-tree CFR iterations')
 m=len(nodes)
 if len(probability)!=n*n or len(payoffs)!=m*n*n or any(not math.isfinite(x) for x in (*probability,*payoffs)) or any(x<0 for x in probability) or not math.isclose(sum(probability),1,abs_tol=1e-12):raise ValueError('normalized finite game required')
 actors=ints([x['actor'] for x in nodes]);counts=ints([len(x['actions']) for x in nodes]);children=ints([c for x in nodes for c in (x['children']+[-1]*3)[:3]])
 if any(x['actor'] not in (-1,0,1) or len(x['actions'])>3 or len(x['actions'])!=len(x['children']) or any(not i<c<m for c in x['children']) for i,x in enumerate(nodes)):raise ValueError('acyclic bounded tree required')
 strategy=(C.c_double*(m*3*n))();ev=(C.c_double*(m*3*n))();reach=(C.c_double*(m*n))();metrics=(C.c_double*4)();start=time.monotonic()
 if lib.abstract_solve(n,m,actors,counts,children,doubles(probability),doubles(payoffs),iterations,strategy,ev,reach,metrics):raise ValueError('CFR calculation failed')
 if metrics[3]<-1e-8 or metrics[1]+1e-8<metrics[0] or metrics[0]+1e-8<metrics[2]:raise ValueError('information-constrained BR bounds differ')
 return {'iterations':iterations,'seconds':time.monotonic()-start,'strategy':list(strategy),'action_ev_chips':list(ev),'reach':list(reach),
  'profile_sb_ev_bb':metrics[0]/2,'br_sb_ev_bb':metrics[1]/2,'br_bb_min_sb_ev_bb':metrics[2]/2,'abstract_nashconv_bb':metrics[3]/2,
  'full_game_gto_verified':False}

def payoffs(k,mode,nodes):
 if mode not in ('checkdown','flop_controller'):raise ValueError('explicit continuation model')
 size=169*169;out=[]
 for node in nodes:
  if node['actor']>=0:out.extend([0.]*size)
  elif not node['matched']:out.extend([float(node['value'])]*size)
  else:
   x=node['value'];plane=0 if mode=='checkdown' or x==100 else (2,5,18,42).index(x)+1
   scale=x/100 if plane==0 else 1
   out.extend(v*scale for v in k['mean'][plane*size:(plane+1)*size])
 return out

def ranges(result,nodes):
 selected={}
 for index,node in enumerate(nodes):
  if node['actor']<0 or 'call' in node['history']:continue
  name=('rfi','vs_open','vs_3bet','vs_4bet','vs_5bet')[node['raises']]
  hands={}
  for h,label in enumerate(CLASSES):
   frequency=[result['strategy'][(index*3+a)*169+h] for a in range(len(node['actions']))]
   values=[result['action_ev_chips'][(index*3+a)*169+h]/2 for a in range(len(node['actions']))]
   if not math.isclose(sum(frequency),1,abs_tol=1e-10) or any(p<0 for p in frequency):raise ValueError('strategy frequency differs')
   hands[label]={'frequencies':frequency,'action_ev_bb':values,'ev_bb':sum(p*v for p,v in zip(frequency,values)),'reach_mass':result['reach'][index*169+h]}
  selected[name]={'actor':node['actor'],'actions':node['actions'],'history':node['history'],'hands':hands,'coverage':169}
 return selected


def heldout(lib,policy,k,mode,nodes,probability,*,failure=.005):
 """Fixed policy global EV, independent sampled kernel, weighted Hoeffding.

 Each unordered class pair shares paired worlds/all continuation planes. Bound
 that entire group's correlated payoff once; groups/worlds are IID PRNG draws.
 Do not use this bound for learned best responses or real-game abstraction error.
 """
 n=169;m=len(nodes);leaf=payoffs(k,mode,nodes)
 ev=(C.c_double*(m*3*n))();reach=(C.c_double*(m*n))();metrics=(C.c_double*4)()
 lib.abstract_evaluate(n,m,ints([x['actor'] for x in nodes]),ints([len(x['actions']) for x in nodes]),
  ints([c for x in nodes for c in (x['children']+[-1]*3)[:3]]),doubles(probability),doubles(leaf),doubles(policy),ev,reach,metrics)
 weights=[0.]*(n*n)
 def visit(v,r0,r1):
  node=nodes[v]
  if node['actor']<0:
   if node['matched']:
    for i in range(n):
     for j in range(n):weights[i*n+j]+=probability[i*n+j]*r0[i]*r1[j]
   return
  for a,child in enumerate(node['children']):
   r=[x*policy[(v*3+a)*n+h] for h,x in enumerate(r0 if node['actor']==0 else r1)]
   visit(child,r if node['actor']==0 else r0,r1 if node['actor']==0 else r)
 visit(0,[1.]*n,[1.]*n)
 squares=sum((weights[i*n+j]+(weights[j*n+i] if i!=j else 0))**2 for i in range(n) for j in range(i,n))
 radius=100*math.sqrt(math.log(2/failure)*squares/(2*k['samples_per_class_pair']))
 return {'seed':k['seed'],'profile_sb_ev_bb':metrics[0]/2,'confidence':1-failure,
  'interval_bb':[max(-50.,metrics[0]/2-radius),min(50.,metrics[0]/2+radius)],
  'radius_bb':radius,'fixed_policy_digest':hashlib.sha256(doubles(policy)).hexdigest(),
  'method':'weighted Hoeffding over independent unordered class-pair/world groups; all shared planes/seat swaps bounded jointly',
  'real_game_approximation_error_bb':None,'full_game_gto_verified':False}
