import json,time,random
import numpy as np
from gto.qualification.private_integrated_joint import FiniteIntegratedJoint
from gto.qualification.multiplayer_joint import Joint,expanded_decks,path_oracle,path_br,sparse_key
from gto.qualification.public_response import Observation
from gto.qualification.build import load
from gto.native.training import NativeGame
from gto.qualification.evaluate import atomic
_,native=load('/tmp/native-qualification');game=NativeGame([24,22,20]);ds=expanded_decks(3)
exact=Joint(native,game,ds,[.25]*4,action_scope='preflop',max_nodes=5000,max_seconds=30)
q=FiniteIntegratedJoint(native,game,decks=ds,weights=[.25]*4,action_scope='preflop',max_nodes=100000,max_seconds=30)
def canonical(k):
 d=json.loads(k)
 if d['round']==0:
  lo,hi=sorted(c//4 for c in d['own']);suited=d['own'][0]%4==d['own'][1]%4;d['own']=[4*lo,4*hi+(0 if lo!=hi and suited else 1)]
 return json.dumps(d,sort_keys=True,separators=(',',':'))
def policy():return {k:q.policy().get(canonical(k),np.ones(len(a))/len(a)) for k,a in exact.actions.items()}
curve=[];st=time.monotonic()
for t in (0,8,32):
 while q.t<t:q.step()
 pi=policy();ev=exact.weights@exact.values(pi)[0];br=[path_br(exact,pi,p) for p in range(3)];curve.append(dict(t=t,gain_sum=float(sum(np.array(br)-ev)),EV=ev.tolist(),BR=br))
print(curve,'seconds',time.monotonic()-st)
atomic('docs/qa/public-chance-20261125/multiplayer-integrated.json',dict(curve=curve,seconds=time.monotonic()-st,full_native_BR_upper=None,scope='finite 3-player ordinary preflop/checkcall continuation; not6/9 tree',formal_acceptance=0))
q.export('docs/qa/public-chance-20261125/multiplayer-integrated-checkpoint.json.gz')
