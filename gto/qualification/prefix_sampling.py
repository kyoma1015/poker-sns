"""Root-opponent quantile stratification of existing N external sampling.
Only the first non-owner root action draw is coupled. The equal-weight union of root quantile strata is uniform, so the combined
raw estimator retains the original counterfactual/importance corrections.
No full-tree expansion; owner-root traversal is run once, never duplicated.
"""
import random
from pathlib import Path
import numpy as np
from gto.qualification.multiplayer_joint import SparseJoint,observation
from gto.qualification.stream_multiplayer import Stratified
from gto.qualification.policy import sha
class FirstDraw(random.Random):
 def __init__(self,seed,u):super().__init__(seed);self.first=u
 def random(self):
  if self.first is not None:u=self.first;self.first=None;return u
  return super().random()

def merge(out,part,weight):
 for field in ('grad','avg'):
  for k,v in part[field].items():out[field][k]=out[field].get(k,np.zeros(len(v)))+weight*v
 for field in ('actions','owners','info'):
  for k,v in part[field].items():
   if k in out[field] and out[field][k]!=v:raise ValueError('prefix information identity')
   out[field][k]=v
 for key in ('max_average_weight','max_CF_scale'):out[key]=max(out[key],part[key])

class Prefix(Stratified):
 def __init__(self,*a,root_batch=2,**kw):
  super().__init__(*a,**kw)
  if type(root_batch) is not int or not 1<=root_batch<=4:raise ValueError('bounded root batch')
  self.root_batch=root_batch;self.identity.update(root_batch=root_batch,prefix_source_sha256=sha(Path(__file__)))
 def collect(self,owner,deck,stream,pi,*,audit=False,budget=None):
  if not self.batch:raise ValueError('declared chance batch required')
  out=dict(grad={},avg={},actions={},owners={},info={},max_average_weight=0.,max_CF_scale=0.)
  for world,w in self.batch:
   state=self.native.NativeState(self.game)
   for c in world[:2*self.N]:state.apply_action(c)
   actor=observation(state).actor;K=1 if actor==owner or audit else self.root_batch;u=stream.random();seed=stream.getrandbits(128)
   for j in range(K):
    rng=random.Random(seed) if K==1 else FirstDraw(seed,(u+j)/K)
    part=SparseJoint.collect(self,owner,world,rng,pi,audit=audit,budget=budget);merge(out,part,w/K)
  return out
 def step(self):
  if self.root_batch!=self.identity['root_batch']:raise ValueError('root proposal changed')
  return super().step()
