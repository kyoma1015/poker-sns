"""Information-set-respecting best response bounds in a FIXED continuation game.

Terminal confidence events hold simultaneously before maximization. Thus choosing
an adaptive best response cannot exploit unaccounted validation noise. Opponent
private types are beliefs, never observable state available to the responder.
"""
import math
from gto.abstract.model import tree,classes,chance
from gto.abstract.precision import bound,frozen_rows


def evaluate(policy,kernel,mode,*,nodes=None,probability=None,n=169,failure=.0025):
 nodes=tree() if nodes is None else nodes
 probability=chance(classes())[1] if probability is None else probability
 frozen_rows(policy,nodes,n);size=n*n
 mask=kernel.get('exact_mask',[False]*(5*size))
 leaves=sum(node['actor']<0 for node in nodes)
 delta=failure/(2*n*leaves);results=[]
 for hero in (0,1):
  total=[[],[],[],[]]
  for h in range(n):
   raw=[probability[h*n+j] if hero==0 else probability[j*n+h] for j in range(n)]
   prior=math.fsum(raw)
   if not prior:continue
   def visit(v,posterior):
    node=nodes[v]
    if node['actor']<0:
     if not node['matched']:
      value=(1 if hero==0 else -1)*node['value']/2
      return value,value,value,value
     x=node['value'];plane=0 if mode=='checkdown' or x==100 else (2,5,18,42).index(x)+1
     scale=x/100 if plane==0 else 1.;coeff=[];mu=[];var=[];exact=[]
     for j,p in enumerate(posterior):
      idx=h*n+j if hero==0 else j*n+h;weights=[0.]*5
      means=[kernel['mean'][k*size+idx]*(1 if hero==0 else -1) for k in range(5)]
      if mask[plane*size+idx]:exact.append(p*scale*means[plane]/2)
      else:weights[plane]=p*scale
      coeff.append(weights);mu.append(means);var.append([kernel['variance'][k*size+idx] for k in range(5)])
     r=bound(math.fsum(exact),coeff,mu,var,kernel['samples_per_class_pair'],delta,caps=(100,4,10,36,84))
     return r['ev_bb'],*r['interval_bb'],r['ev_bb']
    branches=[];weights=[]
    for a,child in enumerate(node['children']):
     if node['actor']==hero:
      branches.append(visit(child,posterior));weights.append(policy[(v*3+a)*n+h])
     else:
      raw=[p*policy[(v*3+a)*n+j] for j,p in enumerate(posterior)];mass=math.fsum(raw)
      if mass:
       branches.append(visit(child,[p/mass for p in raw]));weights.append(mass)
    profile=math.fsum(w*b[3] for w,b in zip(weights,branches))
    if node['actor']==hero:return *(max(b[k] for b in branches) for k in range(3)),profile
    return *(math.fsum(w*b[k] for w,b in zip(weights,branches)) for k in range(3)),profile
   row=visit(0,[p/prior for p in raw])
   for k,value in enumerate(row):total[k].append(prior*value)
  values=[math.fsum(x) for x in total]
  results.append({'hero':hero,'best_response_ev_bb':values[0],'interval_bb':values[1:3],'profile_ev_bb':values[3]})
 lower=max(0.,math.fsum(r['interval_bb'][0] for r in results)-1e-9)
 upper=min(100.,math.fsum(r['interval_bb'][1] for r in results)+1e-9)
 return {'confidence':1-failure,'players':results,'nashconv_point_bb':math.fsum(r['best_response_ev_bb'] for r in results),
  'nashconv_interval_bb':[lower,upper],'expected_game_convergence_verified':False,'real_game_gto_verified':False,
  'scope':'Global information-set best response against fixed opponent in fixed continuation-controller game only; uniform terminal confidence before maximization; not real-game exploitability'}
