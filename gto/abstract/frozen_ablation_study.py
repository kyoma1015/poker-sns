"""Real frozen HU50BB inputs, explicit fixed-model ablations; never GTO certification.

No test fixtures or learned-flop-policy claims. Existing kernel plane0 averages
unconditional public boards given compatible preflop classes. Higher planes are
stored card-dependent fixed flop controllers, also averaged over boards.
"""
import argparse,gzip,hashlib,json,math
from dataclasses import asdict
from pathlib import Path
from gto.abstract.model import tree,chance,classes
from gto.abstract.precision_archive import unpack
from gto.abstract.precision import integrate_action
from gto.abstract.study import digest
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.flop_tree_ablation import Policy,evaluate_flop
from gto.abstract.frozen_flop_ablation import evaluate_frozen_ablation

N=169;SIZE=N*N;CAPS=(100.,4.,10.,36.,84.)
PROTOCOLS={'bet_call':Policy(1,0,1,1),'raise_call':Policy(1,1,1,1)}


def kernel_identity(k):
 return hashlib.sha256(json.dumps({key:k.get(key) for key in ('seed','samples_per_class_pair','mean','exact_mask')},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate_kernel(k):
 if type(k.get('samples_per_class_pair')) is not int or k['samples_per_class_pair']<2 or len(k.get('mean',[]))!=5*SIZE:raise ValueError('complete sampled five-plane HU kernel required')
 if 'exact_mask' in k and (len(k['exact_mask'])!=5*SIZE or any(x not in (0,1) for x in k['exact_mask'])):raise ValueError('exact mask shape differs')
 for plane,cap in enumerate(CAPS):
  if any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>cap+1e-10 for x in k['mean'][plane*SIZE:(plane+1)*SIZE]):raise ValueError('finite bounded payoff plane required')
 for i in range(N):
  for j in range(N):
   if not math.isclose(k['mean'][i*N+j],-k['mean'][j*N+i],rel_tol=0,abs_tol=1e-10):raise ValueError('paired zero-rake showdown antisymmetry required')


def estimate(k,coeff,constant,failure):
 """Paired unordered-world Hoeffding; NO false independence across seats/planes.

 Shared all-in seats are exactly antisymmetric. Other planes may correlate,
 so sum their absolute ranges inside the same unordered group before squaring.
 Exact expectations are constants. Bound is on sampling only, not abstraction.
 """
 mean=k['mean'];mask=k.get('exact_mask',[0]*(5*SIZE));terms=[];ranges=[]
 for i in range(N):
  for j in range(i,N):
   ij=i*N+j;ji=j*N+i;span=0.
   # Each row's point uses original directed coordinates, never hero clairvoyance.
   for plane in range(5):
    positions=(ij,) if i==j else (ij,ji)
    for pos in positions:terms.append(coeff[plane*SIZE+pos]*mean[plane*SIZE+pos])
    if plane==0:
     if i==j:continue # exact0 by same-class seat-exchange symmetry
     a=coeff[ij] if not mask[ij] else 0.;b=coeff[ji] if not mask[ji] else 0.
     span+=100*abs(a-b)
    else:
     span+=CAPS[plane]*math.fsum(abs(coeff[plane*SIZE+pos]) for pos in positions if not mask[plane*SIZE+pos])
   ranges.append(span)
 center=constant+math.fsum(terms)
 radius=math.sqrt(2*math.log(2/failure)*math.fsum(x*x for x in ranges)/k['samples_per_class_pair']) if any(ranges) else 0.
 if radius:radius=math.nextafter(radius+1e-10,math.inf)
 return {'ev_bb':center,'sampling_radius_bb':radius,'sampling_interval_bb':[math.nextafter(center-radius,-math.inf),math.nextafter(center+radius,math.inf)] if radius else [center,center],
  'method':'paired_unordered_world_Hoeffding','model_approximation_error_bb':None,'external_gto_deviation_bb':None}


def weights(reach):
 p=reach['class_probability'];hero=reach['hero_reach'];villain=reach['villain_reach'];mass=reach['conditional_mass'];out=[0.]*SIZE
 for i in range(N):
  for j in range(N):
   # Convert hero-first probabilities back to the kernel's SB-row/BB-column order.
   pos=i*N+j if reach['hero_actor']==0 else j*N+i
   out[pos]=p[i*N+j]*hero[i]*villain[j]/mass
 if not math.isclose(math.fsum(out),1.,rel_tol=0,abs_tol=1e-12):raise ValueError('conditional distribution not normalized')
 return out


def decision_coefficients(policy,stage):
 """Entire facing node: fold/call/raises and every later preflop response.

 Non-all-in leaf controllers change; all-in and fold payouts remain unchanged.
 Own class distribution includes own past actions; opponent posterior includes
 its complete history. Hero observes only its own type and public actions.
 """
 nodes=tree();r=frozen_reach(stage,policy);v=r['node_index'];actor=r['hero_actor'];sign=1 if actor==0 else -1
 p0=chance(classes())[1];p=r['class_probability'];mass=r['conditional_mass']
 names=('checkdown','saved_card',*PROTOCOLS);co={name:[0.]*(5*SIZE) for name in names};constants={name:[] for name in names}
 transforms={}
 for name,proto in PROTOCOLS.items():
  transforms[name]=[(0.,1.)]
  for x in (2,5,18,42):
   low=evaluate_flop(0.,proto,proto,pot=2*x,effective_stack=100-x)
   high=evaluate_flop(1.,proto,proto,pot=2*x,effective_stack=100-x)
   transforms[name].append((low+(high-low)/2-x,(high-low)/200))
 for h in range(N):
  ownmass=r['hero_reach'][h]*math.fsum(p[h*N+j]*r['villain_reach'][j] for j in range(N))/mass
  for a in range(len(nodes[v]['actions'])):
   factor=ownmass*policy[(v*3+a)*N+h]
   if not factor:continue
   constant,coeff,_=integrate_action(nodes,policy,p0,N,v,h,a,mode='flop_controller')
   for name in names:constants[name].append(factor*constant)
   for j,values in enumerate(coeff):
    idx=h*N+j if actor==0 else j*N+h
    for plane,c in enumerate(values):
     weight=factor*sign*c/2
     co['saved_card'][plane*SIZE+idx]+=weight
     x=(100,2,5,18,42)[plane]
     co['checkdown'][idx]+=weight*x/100
     for name in PROTOCOLS:
      intercept,slope=transforms[name][plane];co[name][idx]+=weight*slope
      constants[name].append(weight*intercept)
 return co,{name:math.fsum(values) for name,values in constants.items()}


def study(packet,kernel=None):
 original,policies=unpack(packet);k=original if kernel is None else kernel
 validate_kernel(k)
 if k['seed']!=original['seed'] or k['samples_per_class_pair']!=original['samples_per_class_pair']:raise ValueError('kernel must retain frozen heldout sample design')
 rows=[];delta=.01/(2*2*18) # all72reported intervals jointly>=99%, union bound
 for policy_name,policy in policies.items():
  for stage in ('vs_3bet','vs_4bet'):
   r=frozen_reach(stage,policy,after_call=True);w=weights(r);x=r['matched_contribution_bb'];pot=r['post_call_pot_bb'];remaining=r['remaining_stack_bb'];sign=1 if r['hero_actor']==0 else -1
   old=[0.]*(5*SIZE);flop=[0.]*(5*SIZE);plane=(2,5,18,42).index(int(pot))+1
   for pos,weight in enumerate(w):old[pos]=sign*weight*x/100;flop[plane*SIZE+pos]=sign*weight/2
   old_result=estimate(k,old,0.,delta);flop_result=estimate(k,flop,0.,delta);difference=estimate(k,[b-a for a,b in zip(old,flop)],0.,delta)
   experiments={}
   for name,fixed in PROTOCOLS.items():
    def value(e):
     kwargs=dict(effective_stack=remaining/pot)
     return evaluate_flop(e,fixed,fixed,**kwargs) if r['hero_actor']==0 else 1.-evaluate_flop(1.-e,fixed,fixed,**kwargs)
    intercept=value(0.);slope=value(1.)-intercept
    coeff=[0.]*(5*SIZE)
    for pos,weight in enumerate(w):coeff[pos]=sign*weight*pot*slope/200
    constant=pot*(intercept+slope/2)-x
    new=estimate(k,coeff,constant,delta);change=estimate(k,[b-a for a,b in zip(old,coeff)],constant,delta)
    independent=evaluate_frozen_ablation(stage,policy,k,fixed,fixed,condition_on_call=True)
    if not math.isclose(new['ev_bb'],independent['new_net_before_blinds_bb'],rel_tol=0,abs_tol=1e-10) or not math.isclose(change['ev_bb'],independent['model_delta_bb'],rel_tol=0,abs_tol=1e-10):raise ValueError('independent class-loop and affine EV disagree')
    versus_saved=estimate(k,[b-a for a,b in zip(flop,coeff)],constant,delta)
    experiments[name]={'hero_policy':asdict(fixed),'villain_policy':asdict(fixed),'policy_source':'deterministic experimental protocol; NOT a learned/played flop policy','new_net_before_blinds':new,'delta_vs_checkdown':change,'delta_vs_saved_card_controller':versus_saved,'bet_bb':min(pot*.5,remaining),'raise_to_bb':min(pot*.5*3,remaining)}
   dc,dk=decision_coefficients(policy,stage)
   decision={'conditioning':'facing decision node BEFORE current action; all frozen fold/call/raise continuations included',
    'old_checkdown':estimate(k,dc['checkdown'],dk['checkdown'],delta),'saved_card_flop':estimate(k,dc['saved_card'],dk['saved_card'],delta),
    'saved_card_delta_vs_checkdown':estimate(k,[b-a for a,b in zip(dc['checkdown'],dc['saved_card'])],dk['saved_card']-dk['checkdown'],delta),'experimental':{}}
   for name in PROTOCOLS:
    decision['experimental'][name]={'new':estimate(k,dc[name],dk[name],delta),
     'delta_vs_checkdown':estimate(k,[b-a for a,b in zip(dc['checkdown'],dc[name])],dk[name]-dk['checkdown'],delta),
     'delta_vs_saved_card_controller':estimate(k,[b-a for a,b in zip(dc['saved_card'],dc[name])],dk[name]-dk['saved_card'],delta)}
   rows.append({'facing_decision':decision,'frozen_preflop_model':policy_name,'policy_digest':packet['policies'][policy_name]['policy_digest'],'stage':stage,'hero_actor':r['hero_actor'],
    'conditioning':'complete preflop action prefix AND hero call; turn/river not a fixed board','before_call_reach_mass':r['before_call_mass'],'post_call_reach_mass':r['conditional_mass'],'conditional_probability_sum':math.fsum(w),
    'pot_bb':pot,'remaining_stack_bb':remaining,'old_checkdown_net_before_blinds':old_result,'existing_card_flop_net_before_blinds':flop_result,'existing_card_flop_delta':difference,'experimental_flop_tree':experiments})
 counts,p=chance(classes())
 return {'schema':'pokerid-real-frozen-ablation-v1','condition':packet['condition'],'input_packet_sha256':hashlib.sha256(json.dumps(packet,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
  'kernel_identity_sha256':kernel_identity(k),'kernel_seed':k['seed'],'samples_per_class_pair':k['samples_per_class_pair'],'compatible_combo_deals':sum(counts),'chance_sha256':digest(p),
  'simultaneous_sampling_confidence':.99,'simultaneous_interval_count':72,'rows':rows,'ev_basis':'net BB before blinds; new minus old; preflop sunk contributions cancel in deltas',
  'equity_is_conditioned_on_specific_flop':False,'equity_source':'existing showdown kernel averaged over public boards for compatible preflop classes',
  'flop_policy_is_trained':False,'model_approximation_error_bb':None,'external_gto_deviation_bb':None,'full_game_gto_verified':False,'formal_acceptance_complete':0,
  'method_source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('frozen_ablation_study.py','frozen_flop_ablation.py','frozen_flop_reach.py','flop_reach_adapter.py','flop_tree_ablation.py')}}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,default=Path('docs/qa/ev-precision-20261030/frozen-inputs.json'));p.add_argument('--kernel',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 packet=json.loads(a.inputs.read_text());k=None
 if a.kernel:
  with (gzip.open(a.kernel,'rt') if str(a.kernel).endswith('.gz') else a.kernel.open()) as f:k=json.load(f)
 result=study(packet,k);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 for r in result['rows']:print(json.dumps({'model':r['frozen_preflop_model'],'stage':r['stage'],'saved_flop_delta_bb':r['existing_card_flop_delta']['ev_bb'],'protocol_deltas':{n:v['delta_vs_checkdown']['ev_bb'] for n,v in r['experimental_flop_tree'].items()}}))
