"""Own/public-only whole-plan transfer with matched feature and teacher factors."""
import math
from gto.abstract.generalization_features import distance_parts
from gto.abstract.continuation_learning import FrozenContinuation
from gto.abstract.factorial_game import structure_key


def category(cards):
 rs=[c//4+2 for c in cards];ss=[c%4 for c in cards];n=len(set(rs));s=len(set(ss))
 if n==1:return 'trips'
 if n==2:
  if s==2:return 'paired_twotone'
  return 'paired_rainbow_high' if next(r for r in rs if rs.count(r)==2)>=12 else 'paired_rainbow_low'
 if s==1:return 'monotone'
 if s==3:return 'rainbow'
 return 'twotone_connected' if max(rs)-min(rs)<=4 else 'twotone_disconnected'


def distance(k,q,use_range):
 p,b=distance_parts(k,q);d=8*p+.5*b
 if use_range:
  if k[22]!=q[22]:return math.inf
  d+=32*(((k[20]-q[20])/15)**2+.5*((k[21]-q[21])/3)**2)
 return d


def mixture(scored,records):
 if not scored:raise ValueError('empty training support; no silent uniform fallback')
 ws=[1/(d+1e-6) for d,_ in scored];z=math.fsum(ws)
 out=tuple(math.fsum(w*records[i]['probabilities'][a] for w,(_,i) in zip(ws,scored))/z for a in range(4));total=math.fsum(out)
 return tuple(x/total for x in out)


class Transfer:
 def __init__(self,records,method,use_range,geometry=None):
  self.records=records;self.method=method;self.use_range=use_range;self.geometry=geometry if geometry is not None else {};self.cache={}
  # All keys/provenance, no probability values, define shared seed-independent geometry.
  self.identity=tuple((tuple(r['key']),tuple(r['training_flop']),r['category']) for r in records)
 def probabilities(self,k,flop):
  query=k if self.use_range else k[:20];cat=category(flop);ck=(query,tuple(flop))
  if ck in self.cache:return self.cache[ck]
  key=(self.identity,self.method,self.use_range,query,cat)
  if key not in self.geometry:
   q=structure_key(query) if self.method=='structure_expert_knn9' else query
   records=self.records;idx=[i for i,r in enumerate(records) if tuple(r['key'])[:3]==q[:3] and (self.method!='structure_expert_knn9' or r['category']==cat)]
   if self.method=='board_interpolation3x5':
    byboard={}
    for i in idx:byboard.setdefault(tuple(records[i]['training_flop']),[]).append(i)
    boards=sorted((distance_parts(q,tuple(records[ids[0]]['key']))[1],b,ids) for b,ids in byboard.items())[:3];groups=[]
    for bd,_,ids in boards:
     scored=sorted((distance(q,tuple(records[i]['key']),self.use_range),i) for i in ids)[:5];groups.append((bd,scored))
    self.geometry[key]=groups
   else:self.geometry[key]=sorted((distance(q,tuple(records[i]['key']),self.use_range),i) for i in idx)[:9]
  geom=self.geometry[key]
  if self.method=='board_interpolation3x5':
   weights=[1/(bd+1e-6) for bd,_ in geom];ps=[mixture(sc,self.records) for _,sc in geom];z=math.fsum(weights);p=tuple(math.fsum(w*x[a] for w,x in zip(weights,ps))/z for a in range(4))
  else:p=mixture(geom,self.records)
  self.cache[ck]=p;return p
 def materialize(self,g):return FrozenContinuation({k:self.probabilities(k,g['flop']) for k in g['hkeys']+g['vkeys']})
