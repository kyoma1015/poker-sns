import itertools,tempfile,unittest
import numpy as np
from gto.qualification import active_chance as ac,public_chance_solver as pcs,stream_sampling as ss,stream_measure as old,symmetry_br as sym
class Symmetry(unittest.TestCase):
 def test_quotient_matches_explicit_all144_symmetry_worlds(self):
  with tempfile.TemporaryDirectory() as tmp:
   lib=ac.build(tmp);board=[0,5,10,15,20];nodes=[dict(actor=0,children=[1,2],round=0),dict(actor=-1,children=[],round=0,c0=-.5),dict(actor=1,children=[3,4],round=3),dict(actor=-1,children=[],round=3,c0=-3,c1=6),dict(actor=-1,children=[],round=3,c0=2)]
   blocks=[]
   for p in itertools.permutations(range(4)):
    cv=lambda c:4*(c//4)+p[c%4]
    for flop in itertools.permutations(board[:3]):blocks.append(pcs.block(lib,list(map(cv,flop+tuple(board[3:]))),1/144))
   a=ss.Game(lib,nodes,[pcs.block(lib,board,1.)]);rng=np.random.default_rng(17161401);a.A[:]=rng.random(a.S);a.R[:]=a.A;pi=a.policy();b=ss.Game(lib,nodes,blocks)
   for st,t,n,k in b.rows:
    for j,key in enumerate(b.keys[k]):
     idx=a.keys[k].index(key);b.A[st+j*n:st+(j+1)*n]=pi[a.base[k]+idx*n:a.base[k]+(idx+1)*n]
   x=sym.measure(a);y=old.measure(b,True)
   for name in ('EV_bb','BR_SB_bb','BR_BB_bb','NashConv_bb'):self.assertAlmostEqual(x[name],y[name],places=9)
   raw=old.measure(a,True);self.assertGreaterEqual(raw['NashConv_bb']+1e-10,x['NashConv_bb'])
