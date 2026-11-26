import json,time
import numpy as np
from gto.qualification.multiplayer_joint import SparseJoint,Joint,expanded_decks,path_br
from gto.qualification.test_private_integrated_joint import canonical
from gto.qualification.build import load
from gto.native.training import NativeGame
from gto.qualification.evaluate import atomic
_,native=load('/tmp/native-qualification');game=NativeGame([24,22,20]);ds=expanded_decks(3)
exact=Joint(native,game,ds,[.25]*4,action_scope='preflop',max_nodes=5000,max_seconds=30);rows=[]
for seed in (17124101,17124102):
 q=SparseJoint(native,game,seed=seed,decks=ds,weights=[.25]*4,action_scope='preflop',max_nodes=100000,max_seconds=30)
 st=time.monotonic()
 while time.monotonic()-st<22.81756:q.step()
 sec=time.monotonic()-st;pi={k:q.policy().get(canonical(k),np.ones(len(a))/len(a)) for k,a in exact.actions.items()};ev=exact.weights@exact.values(pi)[0];br=[path_br(exact,pi,p) for p in range(3)]
 rows.append(dict(seed=seed,seconds=sec,iterations=q.t,gain_sum=float(sum(np.array(br)-ev))))
 print(rows[-1],flush=True)
atomic('docs/qa/public-chance-20261125/multiplayer-same-budget.json',dict(rows=rows,comparison='same finite game, wallclock budget, sampled vs integrated; no6/9 extrapolation'))
