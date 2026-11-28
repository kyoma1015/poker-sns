"""Public/own signal features and training-only policy transfer.

Uniform strength sums ALL compatible unknown opponents. No actual opponent is
an input. Every model is evaluated with this same rich own-signal partition.
"""
import math
from collections import Counter
from gto.abstract.continuation_learning import key as coarse_key,FrozenContinuation
from gto.abstract.flop_conditional import Observation
from gto.native.ev_audit import rank_five

def uniform_strength(m):
 n=m['n'];out={}
 for i,p in enumerate(m['pairs']):
  total=0;count=0
  for j,q in enumerate(m['pairs']):
   if not set(p)&set(q):total+=2*m['win'][i*n+j]+m['tie'][i*n+j];count+=1
  if count!=1081:raise ValueError('full legal unknown-opponent prior required')
  out[tuple(sorted(p))]=total/(1980*count)
 return out

def signal(obs,strength):
 h=tuple(obs.holes);f=tuple(obs.flop);cards=h+f
 if len(h)!=2 or len(f)!=3 or len(set(cards))!=5:raise ValueError('legal own cards and public flop required')
 rs=sorted(c//4+2 for c in f);ranks={c//4+2 for c in cards};wheel=ranks|({1} if 14 in ranks else set());boardset=set(rs)|({1} if 14 in rs else set())
 paired=3-len(set(rs));suit=max(sum(c%4==s for c in f) for s in range(4));connected=max(len(boardset.intersection(range(k,k+5))) for k in range(1,11));made=rank_five(cards);primary=made[1] if made[0] in (1,2,3,6,7) else 0;relative=3 if primary>rs[-1] else 2 if primary==rs[-1] else 1 if primary>=rs[1] else 0
 missing={next(iter(set(range(k,k+5))-wheel)) for k in range(1,11) if len(set(range(k,k+5))-wheel)==1};straightdraw=0 if made[0]>=4 else min(2,len(missing));over=sum(c//4+2>rs[-1] for c in h)
 target=max(range(4),key=lambda s:sum(c%4==s for c in cards));flushn=sum(c%4==target for c in cards);ownflush=max((c//4+2 for c in h if c%4==target),default=0);nut=0 if flushn<4 else 3 if ownflush==14 else 2 if ownflush>=12 else 1
 eq=strength[tuple(sorted(h))]
 if not 0<=eq<=1:raise ValueError('own-uniform strength outside bounds')
 # Legacy6prefix preserves own-strength semantics for existing fixed opponents.
 public=(paired,suit,connected,*rs,round(obs.remaining_stack_bb/obs.pot_bb,8))
 private=(made[0],relative,over,straightdraw,nut,(max(c//4+2 for c in h)-2)//5,min(7,int(eq*8)))
 return (*coarse_key(obs),*public,*private)

# After prefix[0:6],7public and7private values. Prefix first3 are exact stage/role.
SCALES=(1,1,1,2,3,3,14,14,14,3,8,3,2,2,3,2,7)

def distance_parts(a,b):
 if a[:3]!=b[:3]:return math.inf,math.inf
 pub=math.fsum(((a[i]-b[i])/s)**2 for i,s in zip(range(6,13),SCALES[3:10]))
 private=math.fsum(((a[i]-b[i])/s)**2 for i,s in zip((*range(3,6),*range(13,20)),(*SCALES[:3],*SCALES[10:])))
 return private,pub

class TransferPolicy:
 def __init__(self,records,config,coarse=None):self.records=records;self.config=config;self.coarse=coarse;self.cache={}
 def probabilities(self,k):
  if k in self.cache:return self.cache[k]
  if self.config['kind']=='coarse':p=self.coarse.table.get(k[:6],(.25,)*4)
  else:
   scores=[]
   for index,row in enumerate(self.records):
    q=tuple(row['key'])
    if k[:3]!=q[:3]:continue
    private,public=distance_parts(k,q);scores.append((private*self.config['private_weight']+public*self.config['board_weight'],index))
   if not scores:p=(.25,)*4
   else:
    top=sorted(scores)[:self.config['neighbors']];weights=[1/(d+1e-6) for d,_ in top];z=math.fsum(weights);p=tuple(math.fsum(w*self.records[idx]['probabilities'][a] for w,(_,idx) in zip(weights,top))/z for a in range(4))
  total=math.fsum(p);p=tuple(x/total for x in p);self.cache[k]=p;return p
 def materialize(self,g):return FrozenContinuation({k:self.probabilities(k) for k in g['hkeys']+g['vkeys']})
