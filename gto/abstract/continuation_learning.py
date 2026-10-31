"""Research contextual normal-form regret learner, NOT full-game CFR/GTO.

Arms are entire one-street policies, mixed as plans (never averaged parameters).
Observation features use only own cards and public flop/position/pot/stack.
Train/heldout partitions are disjoint UNORDERED concrete hole assignments.
"""
import bisect,hashlib,math,random
from gto.abstract.flop_conditional import Observation,strong
from gto.abstract.flop_tree_ablation import Policy,evaluate_flop
from gto.abstract.frozen_flop_reach import frozen_reach
ARMS=(Policy(0,0,1,1),Policy(1,0,1,1),Policy(1,1,1,1),Policy(1,0,0,0))

def key(obs):
 top=max(c//4 for c in obs.flop);cards=obs.holes+obs.flop
 return (obs.actor,obs.pot_bb,obs.remaining_stack_bb,int(strong(obs.holes,obs.flop)),int(all(c//4>top for c in obs.holes)),int(max(sum(c%4==s for c in cards) for s in range(4))>=4))

def partition(a,b,flop):
 # Swapped seats share the same split: cannot leak a matchup via orientation.
 pair=sorted((tuple(sorted(a)),tuple(sorted(b))))
 return int.from_bytes(hashlib.sha256(bytes((*sorted(flop),*pair[0],*pair[1]))).digest()[:8],'big')%5

def draw_worlds(m,reach,*,count,seed,heldout):
 rng=random.Random(seed);pairs=m['pairs'];labels=m['labels'];v=[reach['villain_reach'][h] for h in labels];cardmass=[0.]*52;total=math.fsum(v);by_pair={}
 for p,w in zip(pairs,v):
  for c in p:cardmass[c]+=w
  by_pair[tuple(sorted(p))]=w
 hm=[reach['hero_reach'][h]*max(0.,total-cardmass[p[0]]-cardmass[p[1]]+by_pair[tuple(sorted(p))]) for p,h in zip(pairs,labels)]
 def cdf(ws):
  z=0.;out=[]
  for w in ws:z+=w;out.append(z)
  if z<=0:raise ValueError('empty conditional distribution')
  return out
 hc,vc=cdf(hm),cdf(v);out=[];attempts=0
 while len(out)<count:
  attempts+=1
  if attempts>count*100000:raise ValueError('partition unreachable')
  i=bisect.bisect_right(hc,rng.random()*hc[-1]);a=pairs[i]
  while True:
   j=bisect.bisect_right(vc,rng.random()*vc[-1]);b=pairs[j]
   if not set(a)&set(b):break
  if (partition(a,b,m['flop'])==0)!=heldout:continue
  e=(m['win'][i*m['n']+j]+m['tie'][i*m['n']+j]/2)/990
  out.append((i,j,e))
 return out

def payoff(e,a,b,actor,pot,remaining):
 cash=evaluate_flop(e,a,b,pot=pot,effective_stack=remaining) if actor==0 else pot-evaluate_flop(1-e,b,a,pot=pot,effective_stack=remaining)
 return cash-pot/2

def dataset(m,reach,worlds):
 out=[]
 for i,j,e in worlds:
  args=(m['flop'],reach['hero_actor'],reach['post_call_pot_bb'],reach['remaining_stack_bb'])
  a=Observation(m['pairs'][i],*args);b=Observation(m['pairs'][j],args[0],1-args[1],*args[2:])
  matrix=[[payoff(e,x,y,args[1],args[2],args[3]) for y in ARMS] for x in ARMS]
  out.append((key(a),key(b),matrix))
 return out

def match(regrets):
 v=[max(0.,x) for x in regrets];z=math.fsum(v)
 return [x/z for x in v] if z else [1/len(v)]*len(v)

class FrozenContinuation:
 """Distribution of complete plans conditional ONLY on supplied Observation."""
 def __init__(self,table):self.table={k:tuple(v) for k,v in table.items()}
 def __call__(self,observation):return self.table.get(key(observation),(.25,)*4)

def train(data,*,epochs=12,seed=17):
 if not data or epochs<1:raise ValueError('nonempty training split and positive epochs required')
 regrets={k:[0.]*4 for a,b,_ in data for k in (a,b)};average={k:[0.]*4 for k in regrets};rng=random.Random(seed)
 for _ in range(epochs):
  order=list(range(len(data)));rng.shuffle(order)
  for idx in order:
   a,b,m=data[idx];p=match(regrets[a]);q=match(regrets[b]);u=[math.fsum(m[i][j]*q[j] for j in range(4)) for i in range(4)];v=[-math.fsum(p[i]*m[i][j] for i in range(4)) for j in range(4)];base=math.fsum(x*y for x,y in zip(p,u))
   for i in range(4):regrets[a][i]+=u[i]-base;regrets[b][i]+=v[i]+base;average[a][i]+=p[i];average[b][i]+=q[i]
 table={k:[x/math.fsum(v) for x in v] for k,v in average.items()}
 return FrozenContinuation(table)

def evaluate(data,policy):
 values=[]
 for a,b,m in data:
  p=policy.table.get(a,(.25,)*4);q=policy.table.get(b,(.25,)*4)
  values.append(math.fsum(p[i]*q[j]*m[i][j] for i in range(4) for j in range(4)))
 mean=math.fsum(values)/len(values);radius=100*math.sqrt(math.log(2/.001)/(2*len(values)))
 return {'self_play_ev_bb':mean,'heldout_sampling_interval_bb':[mean-radius,mean+radius],'samples':len(values),'confidence':.999,'external_gto_comparison':None,'full_game_convergence_verified':False}

def experiment(m,policy,stage,seed):
 reach=frozen_reach(stage,policy,after_call=True);worlds=draw_worlds(m,reach,count=1024,seed=seed,heldout=False);heldout=draw_worlds(m,reach,count=2048,seed=seed+900001,heldout=True)
 td=dataset(m,reach,worlds);ed=dataset(m,reach,heldout);trained=train(td,epochs=12,seed=seed)
 def fingerprint(xs):return hashlib.sha256(repr(xs).encode()).hexdigest()
 training=evaluate(td,trained);training.pop('heldout_sampling_interval_bb');training.pop('confidence');training['evaluation_kind']='in-sample descriptive only; no confidence guarantee'
 return {'training_seed':seed,'evaluation_seed':seed+900001,'training_samples':len(td),'training_partition':'sha256(unordered hole pairs,flop)%5 !=0','evaluation_partition':'same hash%5 ==0','training_dataset_sha256':fingerprint(worlds),'evaluation_dataset_sha256':fingerprint(heldout),'epochs':12,'features':'own/public only: actor,pot,stack,strength,overcards,flush-draw','scope':'four-arm restricted one-street normal-form regret learner; NOT existing CFR; no real-game GTO claim','policy':[{ 'observation_key':list(k),'arm_probabilities':list(v)} for k,v in sorted(trained.table.items())],'heldout':evaluate(ed,trained),'training_self_play':training,'external_gto_deviation_bb':None}
