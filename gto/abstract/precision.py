"""Frozen-policy conditional EV integration and stratified confidence bounds.

Opponent classes and public action branches are enumerated, not sampled.
Remaining uncertainty concerns sampled continuation kernels ONLY, never poker
abstraction error. No CFR training or increased sample count is performed here.
"""
import gzip,hashlib,json,math
from pathlib import Path
from gto.hand169 import CLASSES
from gto.abstract.model import chance,classes,tree,CONDITION

STAGES=('rfi','vs_open','vs_3bet','vs_4bet')

def frozen_rows(policy,nodes,n):
 if len(policy)!=len(nodes)*3*n:raise ValueError('policy/tree shape differs')
 for v,node in enumerate(nodes):
  for h in range(n):
   if node['actor']<0:continue
   values=[policy[(v*3+a)*n+h] for a in range(len(node['actions']))]
   if any(not math.isfinite(x) or x<0 for x in values) or not math.isclose(math.fsum(values),1,abs_tol=1e-12):raise ValueError('normalized fixed policy required')

def integrate_action(nodes,policy,probability,n,v,h,action,*,mode):
 """Return deterministic BB value and coefficients on five CHIP payoff planes.

 The conditioning likelihood includes opponents' complete action prefix. Own
 prior action factors cancel for a known own type; future choices retain them.
 Coefficients are nonnegative, preserving covariance-safe moment bounds.
 """
 actor=nodes[v]['actor'];prefix=[1.]*n
 def locate(at,weights):
  if at==v:return weights
  node=nodes[at]
  for a,child in enumerate(node['children']):
   if child<=v:
    branch=[w*policy[(at*3+a)*n+j] for j,w in enumerate(weights)] if node['actor']==1-actor else weights
    found=locate(child,branch)
    if found is not None:return found
  return None
 prefix=locate(0,prefix)
 if prefix is None:raise ValueError('target public history not reached')
 raw=[probability[h*n+j]*prefix[j] if actor==0 else probability[j*n+h]*prefix[j] for j in range(n)]
 denominator=math.fsum(raw)
 if denominator<=0:raise ValueError('unknown conditional opponent reach')
 posterior=[x/denominator for x in raw];coefficient=[[0.]*5 for _ in range(n)];constant=[]
 immediate=nodes[nodes[v]['children'][action]]
 if immediate['actor']<0 and not immediate['matched']:
  return (1 if actor==0 else -1)*immediate['value']/2,coefficient,denominator
 def visit(at,own,opponent):
  node=nodes[at]
  if node['actor']<0:
   if not node['matched']:
    constant.append((1 if actor==0 else -1)*node['value']/2*own*math.fsum(p*q for p,q in zip(posterior,opponent)))
   else:
    x=node['value'];plane=0 if mode=='checkdown' or x==100 else (2,5,18,42).index(x)+1
    scale=x/100 if plane==0 else 1.
    for j in range(n):coefficient[j][plane]+=posterior[j]*own*opponent[j]*scale
   return
  for a,child in enumerate(node['children']):
   if node['actor']==actor:visit(child,own*policy[(at*3+a)*n+h],opponent)
   else:visit(child,own,[x*policy[(at*3+a)*n+j] for j,x in enumerate(opponent)])
 visit(nodes[v]['children'][action],1.,[1.]*n)
 if math.fsum(math.fsum(c) for c in coefficient)>1+1e-10:raise ValueError('conditional continuation mass exceeds one')
 return math.fsum(constant),coefficient,denominator

def bound(constant,coefficients,means,variances,samples,failure,*,caps=None):
 """Simultaneous-safe intersection of stratified Hoeffding and Bernstein.

 For group g, Z=sum_k a_gk X_gk, A=sum a. Jensen gives E[Z²] <=
 A sum a E[X²]. Estimate this entire weighted second-moment sum; its group
 range is10000 A². Covariances between planes need not be known. An independent-
 group Hoeffding bound on that moment sum plus Bernstein gives a variance-aware
 bound without assuming samples within a shared world/plane are independent.
 """
 if samples<2 or not 0<failure<1 or len(coefficients)!=len(means) or len(means)!=len(variances):raise ValueError('bounded stratified moments required')
 caps=[100.]*5 if caps is None else caps
 if len(caps)!=5 or any(not math.isfinite(c) or not 0<c<=100 for c in caps):raise ValueError('positive verified payoff caps required')
 a=[];q=[];terms=[]
 for weights,mu,var in zip(coefficients,means,variances):
  if not len(weights)==len(mu)==len(var)==5 or any(not math.isfinite(x) for x in (*weights,*mu,*var)) or any(x<0 for x in (*weights,*var)) or any(abs(x)>100 for x in mu):raise ValueError('invalid bounded continuation moments')
  # Use the actual pot-dependent utility span, not a50BB stack span for every leaf.
  weights=[w*c/100 for w,c in zip(weights,caps)];mu=[m*100/c for m,c in zip(mu,caps)];var=[v*(100/c)**2 for v,c in zip(var,caps)]
  if any(abs(m)>100+1e-8 for m in mu):raise ValueError('payoff cap violated')
  mass=math.fsum(weights);a.append(mass)
  second=[((samples-1)*v+samples*m*m)/samples for m,v in zip(mu,var)]
  if any(x>10000+1e-7 for x in second):raise ValueError('payoff second moment exceeds utility bound')
  q.append(mass*math.fsum(w*s for w,s in zip(weights,second)))
  terms.extend(w*m/2 for w,m in zip(weights,mu))
 center=constant+math.fsum(terms)
 if not any(a):return {'ev_bb':center,'interval_bb':[center,center],'radius_bb':0.,'method':'exact_no_sampled_leaf'}
 a2=math.fsum(x*x for x in a);a4=math.fsum(x**4 for x in a)
 hoeff=100*math.sqrt(math.log(4/failure)*a2/(2*samples))
 moment_upper=min(10000*a2,math.fsum(q)+10000*math.sqrt(math.log(8/failure)*a4/(2*samples)))
 variance_upper=moment_upper/samples;b=200*max(a)/samples
 bern=(math.sqrt(2*variance_upper*math.log(8/failure))+(2/3)*b*math.log(8/failure))/2
 # Small explicit arithmetic allowance; not statistical or abstraction error.
 radius=math.nextafter(min(hoeff,bern)+1e-10,math.inf)
 return {'ev_bb':center,'interval_bb':[max(-50.,math.nextafter(center-radius,-math.inf)),min(50.,math.nextafter(center+radius,math.inf))],
  'radius_bb':radius,'hoeffding_radius_bb':hoeff,'bernstein_radius_bb':bern,
  'method':'stratified_second_moment_Bernstein' if bern<hoeff else 'conditional_weighted_Hoeffding'}

def evaluate(policy,kernel,mode,*,nodes=None,probability=None,n=169,labels=None,failure=.005):
 nodes=tree() if nodes is None else nodes
 probability=chance(classes())[1] if probability is None else probability
 labels=CLASSES if labels is None else labels
 frozen_rows(policy,nodes,n)
 if len(probability)!=n*n or len(labels)!=n or any(not math.isfinite(x) or x<0 for x in probability) or not math.isclose(math.fsum(probability),1,abs_tol=1e-12):raise ValueError('private chance shape differs')
 contexts={};size=n*n;per_interval_failure=failure/(4*n*4)
 for v,node in enumerate(nodes):
  if node['actor']<0 or 'call' in node['history'] or node['raises']>=4:continue
  stage=STAGES[node['raises']];hands={}
  for h,label in enumerate(labels):
   indices=[h*n+j if node['actor']==0 else j*n+h for j in range(n)]
   means=[[kernel['mean'][plane*size+idx]*(1 if node['actor']==0 else -1) for plane in range(5)] for idx in indices]
   variance=[[kernel['variance'][plane*size+idx] for plane in range(5)] for idx in indices]
   actions=[];combined=[[0.]*5 for _ in range(n)];constants=[];freq=[]
   for action in range(len(node['actions'])):
    constant,coeff,denom=integrate_action(nodes,policy,probability,n,v,h,action,mode=mode)
    exact_terms=[]
    if 'exact_mask' in kernel:
     for j,idx in enumerate(indices):
      for plane in range(5):
       if kernel['exact_mask'][plane*size+idx]:
        exact_terms.append(coeff[j][plane]*means[j][plane]/2);coeff[j][plane]=0.
    constant+=math.fsum(exact_terms)
    result=bound(constant,coeff,means,variance,kernel['samples_per_class_pair'],per_interval_failure,caps=(100,4,10,36,84))
    actions.append(result);weight=policy[(v*3+action)*n+h];freq.append(weight);constants.append(weight*constant)
    for j in range(n):
     for plane in range(5):combined[j][plane]+=weight*coeff[j][plane]
   profile=bound(math.fsum(constants),combined,means,variance,kernel['samples_per_class_pair'],per_interval_failure,caps=(100,4,10,36,84))
   hands[label]={'frequencies':freq,'actions':actions,'profile':profile,'conditional_opponent_mass':denom}
  contexts[stage]={'actor':node['actor'],'actions':node['actions'],'hands':hands,'coverage':n}
 return {'contexts':contexts,'validation_seed':kernel['seed'],'samples_per_class_pair':kernel['samples_per_class_pair'],
  'simultaneous_confidence':1-failure,'intervals_accounted':4*n*4,'full_game_gto_verified':False,'real_game_error':None}

def from_archive(root):
 root=Path(root);evidence=json.loads((root/'evidence.json').read_text());seed=evidence['validation_seed']
 k=json.load(gzip.open(root/f'kernel-{seed}.json.gz','rt'));out={}
 for mode in ('checkdown','flop_controller'):
  frozen=json.loads((root/f"policy-{evidence['seeds'][0]}-{mode}.json").read_text())
  if frozen['tree']!=tree() or frozen['condition']!=CONDITION:raise ValueError('frozen policy condition/tree differs')
  observed=next(r for r in evidence['runs'] if r['seed']==evidence['seeds'][0] and r['mode']==mode)
  digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  if digest(frozen['strategy'])!=observed['policy_digest'] or frozen['kernel_digest']!=observed['payoff_digest']:raise ValueError('frozen policy identity differs')
  out[mode]=evaluate(frozen['strategy'],k,mode)
 return {'schema':'pokerid-conditional-model-ev-v1','confidence':.99,'models':out,
  'kernel_sha256':hashlib.sha256(json.dumps({key:k[key] for key in ('seed','samples_per_class_pair','mean','variance')},sort_keys=True,separators=(',',':')).encode()).hexdigest(),
  'full_game_gto_verified':False,'reference_solution_comparison':'UNPERFORMED','real_game_error':None}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=from_archive(a.archive);a.output.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
 print(json.dumps({mode:{stage:max(row['profile']['radius_bb'] for row in c['hands'].values()) for stage,c in m['contexts'].items()} for mode,m in r['models'].items()},sort_keys=True))
