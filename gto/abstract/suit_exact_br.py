"""Independent Python private-information BR; integrate opponent before maximizing."""
import math

def evaluate(nodes,policy,prob,payoff,n=169):
 size=n*n
 def profile(k):
  node=nodes[k]
  if node['actor']<0:return payoff[k*size:(k+1)*size]
  children=[profile(c) for c in node['children']];actor=node['actor']
  return [math.fsum(policy[(k*3+a)*n+(i if actor==0 else j)]*v[i*n+j] for a,v in enumerate(children)) for i in range(n) for j in range(n)]
 def respond(k,opponent_reach,seat):
  node=nodes[k]
  if node['actor']<0:return payoff[k*size:(k+1)*size]
  children=[]
  for a,c in enumerate(node['children']):
   r=opponent_reach if node['actor']==seat else [x*policy[(k*3+a)*n+h] for h,x in enumerate(opponent_reach)];children.append(respond(c,r,seat))
  if node['actor']!=seat:
   return [math.fsum(policy[(k*3+a)*n+(j if seat==0 else i)]*v[i*n+j] for a,v in enumerate(children)) for i in range(n) for j in range(n)]
  best=[]
  for h in range(n):
   scores=[math.fsum(prob[h*n+j]*opponent_reach[j]*v[h*n+j] for j in range(n)) if seat==0 else math.fsum(prob[i*n+h]*opponent_reach[i]*v[i*n+h] for i in range(n)) for v in children];best.append(max(range(len(scores)),key=lambda a:(1 if seat==0 else -1)*scores[a]))
  return [children[best[i if seat==0 else j]][i*n+j] for i in range(n) for j in range(n)]
 expectation=lambda values:math.fsum(p*v for p,v in zip(prob,values))/2
 value=expectation(profile(0));sb=expectation(respond(0,[1.]*n,0));bb=expectation(respond(0,[1.]*n,1))
 return {'profile_sb_ev_bb':value,'br_sb_ev_bb':sb,'br_bb_min_sb_ev_bb':bb,'abstract_nashconv_bb':max(0.,sb-bb)}
