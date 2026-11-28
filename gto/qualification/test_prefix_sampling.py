import os,unittest,random
import numpy as np
from gto.qualification.prefix_sampling import FirstDraw,Prefix
from gto.qualification.multiplayer_joint import Joint,expanded_decks,path_oracle
from gto.qualification.build import load
from gto.native.training import NativeGame
class Quantile(unittest.TestCase):
 def test_uniform_marginals_and_independent_downstream_stream(self):
  q=np.array([.1,.3,.6]);K=2;cuts={0.,1.}
  for c in np.cumsum(q):
   for j in range(K):
    u=K*c-j
    if 0<u<1:cuts.add(float(u))
  cuts=sorted(cuts);mass=np.zeros(3)
  for a,b in zip(cuts,cuts[1:]):
   for j in range(K):mass[np.searchsorted(np.cumsum(q),((a+b)/2+j)/K,side='right')]+=(b-a)/K
  np.testing.assert_allclose(mass,q,atol=1e-15)
  r=FirstDraw(41,.2);self.assertEqual(r.random(),.2);self.assertEqual(r.random(),random.Random(41).random())
@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class Oracle(unittest.TestCase):
 def test_three_owner_audit_gradient_and_average_and_resume(self):
  _,native=load(os.environ['QUALIFICATION_BUILD']);game=NativeGame([24,22,20]);decks=expanded_decks(3);joint=Joint(native,game,decks,[.25]*4,max_nodes=5000,action_scope='preflop');pi=joint.policy(False);expect=path_oracle(joint,pi)
  q=Prefix(native,game,decks=decks,weights=[.25]*4,seed=17161101,chance_batch=4,average_mode='lazy',max_nodes=20000,max_seconds=10);q._draw();g={};a={}
  for owner in range(3):
   z=q.collect(owner,decks[0],random.Random(owner),pi,audit=True)
   for k,v in z['grad'].items():g[k]=g.get(k,np.zeros(len(v)))+v
   for k,v in z['avg'].items():a[k]=a.get(k,np.zeros(len(v)))+v/2
  for k,v in expect['grad'].items():np.testing.assert_allclose(g[k],v,atol=1e-10)
  for k,v in expect['avg'].items():np.testing.assert_allclose(a[k],v,atol=1e-10)
  state=q.state();r=Prefix(native,game,decks=decks,weights=[.25]*4,seed=17161101,chance_batch=4,average_mode='lazy',max_nodes=20000,max_seconds=10);r.restore(state);q.step();r.step();self.assertEqual(q.state(),r.state())
