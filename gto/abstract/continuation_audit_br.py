"""Independent recursive own-information BR for weighted conditional private chance."""
import math

def independent(g,policy,m,e):
 ns=g['tree']['nodes'];h,v=g['h'],g['v'];size=h*v
 def profile(k):
  n=ns[k]
  if n['actor']<0:return [n['c0']*x+n['c1']*y for x,y in zip(m,e)]
  q=[profile(c) for c in n['children']]
  return [math.fsum(policy[g['offsets'][k]+(i if n['actor']==0 else j)*len(q)+a]*x[i*v+j] for a,x in enumerate(q)) for i in range(h) for j in range(v)]
 def br(k,r,owner):
  n=ns[k]
  if n['actor']<0:return [math.fsum(r[j]*(n['c0']*m[i*v+j]+n['c1']*e[i*v+j]) for j in range(v)) for i in range(h)] if owner==0 else [math.fsum(-r[i]*(n['c0']*m[i*v+j]+n['c1']*e[i*v+j]) for i in range(h)) for j in range(v)]
  qs=[]
  for a,c in enumerate(n['children']):
   nr=r if n['actor']==owner else [x*policy[g['offsets'][k]+t*len(n['actions'])+a] for t,x in enumerate(r)];qs.append(br(c,nr,owner))
  return [max(q[t] for q in qs) if n['actor']==owner else math.fsum(q[t] for q in qs) for t in range(h if owner==0 else v)]
 value=math.fsum(profile(0));upper=math.fsum(br(0,[1.]*v,0));lower=-math.fsum(br(0,[1.]*h,1));return {'profile_hero_ev_bb':value,'hero_br_ev_bb':upper,'villain_br_hero_ev_bb':lower,'restricted_nashconv_bb':max(0.,upper-lower)}
