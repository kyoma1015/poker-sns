"""Fixed-flop private-card posterior and exact990 runouts; research, not GTO.

Hole pairs are sampled WITH replacement from the exact blocker/history posterior.
Turn/river are fully enumerated. A continuation provider sees only its own cards.
"""
import argparse,bisect,hashlib,json,math,random
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from gto.abstract.model import classes
from gto.hand169 import CLASSES
from gto.abstract.precision_archive import unpack
from gto.abstract.precision_runouts import build,exact
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.flop_tree_ablation import Policy,evaluate_flop

@dataclass(frozen=True)
class Observation:
 holes: tuple
 flop: tuple
 actor: int
 pot_bb: float
 remaining_stack_bb: float

class ContinuationProvider(Protocol):
 def __call__(self, observation: Observation) -> Policy: ...

def validate_flop(flop):
 if len(flop)!=3 or len(set(flop))!=3 or any(type(c) is not int or not 0<=c<52 for c in flop):raise ValueError('three distinct public cards required')

def legal_groups(flop):
 validate_flop(flop);blocked=set(flop)
 return [[p for p in g if not blocked.intersection(p)] for g in classes()]

def candidates(groups,h,villain):
 deals=[];cdf=[];total=0.
 for a in groups[h]:
  for j,group in enumerate(groups):
   if not villain[j]:continue
   for b in group:
    if len(set(a+b))==4:
     total+=villain[j];deals.append(a+b);cdf.append(total)
 return deals,cdf,total

def posterior(flop,hero,villain):
 """Exact class masses; each concrete ordered deal has equal prior weight.

 Flop likelihood is constant 1/C(48,3) for every compatible concrete deal.
 Normalize only AFTER public/private removal and full frozen action likelihood.
 """
 if len(hero)!=169 or len(villain)!=169 or any(not math.isfinite(x) or x<0 or x>1 for x in (*hero,*villain)):raise ValueError('169 finite reach probabilities required')
 groups=legal_groups(flop);masses=[];counts=[]
 for h in range(169):
  total=0.;count=0
  for a in groups[h]:
   for j,g in enumerate(groups):
    n=sum(len(set(a+b))==4 for b in g);count+=n;total+=n*villain[j]
  masses.append(hero[h]*total);counts.append(count)
 z=math.fsum(masses)
 if z<=0:raise ValueError('zero board-conditioned reach')
 return groups,[x/z for x in masses],counts

def strong(holes,flop):
 cards=holes+flop;r=[c//4 for c in cards];s=[c%4 for c in cards];u=set(r)
 straight=any(set(range(k,k+5))<=u for k in range(9)) or {12,0,1,2,3}<=u
 return len(u)<5 or straight or max(s.count(k) for k in range(4))>=4

def saved_controller(e,hero,villain,flop,actor,x,remaining):
 """Original fixed controller, using only own holes+this actual public flop."""
 a,b=(hero,villain) if actor==0 else (villain,hero)
 sa,sb=strong(a,flop),strong(b,flop);top=max(c//4 for c in flop)
 pa=sa or all(c//4>top for c in a)
 if sb and not sa:sb_value=-x
 elif not sb and pa and not sb:sb_value=x
 else:sb_value=(2*e-1)*(1 if actor==0 else -1)*(x+(min(x,remaining) if sb or pa else 0))
 return sb_value if actor==0 else -sb_value

def new_controller(e,hero,villain,flop,actor,pot,remaining,provider):
 hp=provider(Observation(hero,flop,actor,pot,remaining));vp=provider(Observation(villain,flop,1-actor,pot,remaining))
 cash=evaluate_flop(e,hp,vp,pot=pot,effective_stack=remaining) if actor==0 else pot-evaluate_flop(1-e,vp,hp,pot=pot,effective_stack=remaining)
 return cash-pot/2

def interval(mean,radius):return [mean-radius,mean+radius]

def evaluate(lib,policy,stage,flop,*,samples=32,seed=99101,provider=None):
 if type(samples) is not int or samples<2:raise ValueError('at least two independent hole draws per class')
 if provider is None:provider=lambda obs:Policy(1,1,1,1)
 reach=frozen_reach(stage,policy,after_call=True);groups,weights,counts=posterior(flop,reach['hero_reach'],reach['villain_reach'])
 pot=reach['post_call_pot_bb'];x=pot/2;remaining=reach['remaining_stack_bb'];actor=reach['hero_actor'];rows=[];aggregates=[[],[],[]]
 # Bonferroni across4reports * (169classes*4metrics +4aggregate metrics).
 failure=.01/(4*(169*4+4));log=math.log(2/failure);cache={}
 for h,label in enumerate(CLASSES):
  row={'hand':label,'legal_hole_combos':len(groups[h]),'compatible_opponent_assignments':counts[h],'posterior_probability':weights[h]}
  if weights[h]==0:row.update(status='ZERO_REACH',equity=None);rows.append(row);continue
  deals,cdf,total=candidates(groups,h,reach['villain_reach']);rng=random.Random(seed+h*1000003);values=[[],[],[]];eq=[];wins=[];ties=[]
  for _ in range(samples):
   holes=deals[min(bisect.bisect_right(cdf,rng.random()*total),len(deals)-1)]
   if holes not in cache:cache[holes]=exact(lib,holes,flop)
   w,t,l=cache[holes];e=(w+t/2)/990;eq.append(e);wins.append(w/990);ties.append(t/990)
   old=saved_controller(e,holes[:2],holes[2:],flop,actor,x,remaining)
   new=new_controller(e,holes[:2],holes[2:],flop,actor,pot,remaining,provider)
   for v,value in zip(values,(old,new,new-old)):v.append(value)
  means=[math.fsum(v)/samples for v in values];eqmean=math.fsum(eq)/samples
  row.update(status='EXACT_RUNOUT_SAMPLED_HOLES',samples=samples,equity=eqmean,win_probability=math.fsum(wins)/samples,tie_probability=math.fsum(ties)/samples,equity_interval=[max(0.,eqmean-math.sqrt(log/(2*samples))),min(1.,eqmean+math.sqrt(log/(2*samples)))],old_ev_bb=means[0],new_ev_bb=means[1],delta_bb=means[2])
  # Net payoffs bounded [-50,50]; paired difference bounded [-100,100].
  for key,m,width in zip(('old_interval_bb','new_interval_bb','delta_interval_bb'),means,(100,100,200)):row[key]=interval(m,width*math.sqrt(log/(2*samples)))
  for a,m in zip(aggregates,means):a.append(weights[h]*m)
  rows.append(row)
 means=[math.fsum(v) for v in aggregates];factor=math.sqrt(math.fsum(w*w for w in weights)*log/(2*samples))
 return {'stage':stage,'flop':list(flop),'hero_actor':actor,'conditioning':'frozen history AND hero CALL AND exact public flop; direct call continuation only',
  'pot_bb':pot,'remaining_stack_bb':remaining,'seed':seed,'samples_per_reachable_class':samples,'turn_river_boards_per_draw':990,'unique_hole_pairs_enumerated':len(cache),'rows':rows,
  'aggregate':{key:{'ev_bb':m,'sampling_interval_bb':interval(m,width*factor)} for key,m,width in zip(('old','new','delta'),means,(100,100,200))},
  'equity_is_conditioned_on_specific_flop':True,'runout_sampling_error':0,'hole_sampling_method':'stratified exact-posterior inverse CDF with replacement; seeded Python Random',
  'net_ev_basis':'before blinds; matched preflop contribution subtracted','new_policy':'fixed experimental raise/call, NOT trained','model_approximation_error_bb':None,'external_gto_deviation_bb':None,'full_game_gto_verified':False}

def study(lib,packet,samples=32):
 _,policies=unpack(packet);policy=policies['flop_controller']
 reports=[evaluate(lib,policy,stage,flop,samples=samples,seed=99101+index*10000019) for index,(stage,flop) in enumerate((s,f) for s in ('vs_3bet','vs_4bet') for f in ((48,21,3),(35,31,27)))]
 return {'schema':'pokerid-fixed-flop-v1','condition':packet['condition'],'policy_digest':packet['policies']['flop_controller']['policy_digest'],'input_sha256':hashlib.sha256(json.dumps(packet,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'reports':reports,'simultaneous_sampling_confidence':.99,'formal_acceptance_complete':0,'scope':'two predeclared flops; no extrapolation to all flops or whole facing node','source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('flop_conditional.py','precision_native.cc','precision_runouts.py','frozen_flop_reach.py','flop_tree_ablation.py')}}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--samples',type=int,default=32);a=p.parse_args()
 result=study(build(a.build_dir),json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text()),a.samples);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 for r in result['reports']:print(r['stage'],r['flop'],r['aggregate'])
