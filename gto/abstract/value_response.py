"""Conditional arm targets and own-information-only bounded response planning."""
import ctypes as C
import math,subprocess
from pathlib import Path
from gto.abstract import continuation_game as base,range_features as feature
from gto.abstract.continuation_learning import FrozenContinuation
from gto.abstract.model import doubles,DP
CONFIG={'name':'common_knn9','family':'range','method':'knn','neighbors':9,'private_weight':8,'board_weight':.5,'range_weight':32}


def conditional_targets(g,policy):
 """Integrate opponent types/actions BEFORE choosing an own-type action.

EV uses utility to the corresponding owner (villain sign reversed). Dividing by
OWN marginal mass, not each opponent-pair mass, preserves the correct posterior.
Zero-mass entries explicitly have no conditional EV/regret target.
"""
 p,q=base.strategies(g,policy);nh,nv=len(p),len(q);a=g['tensor'];out={}
 for side,keys,ps in [('hero',g['hkeys'],p),('villain',g['vkeys'],q)]:
  for i,k in enumerate(keys):
   if side=='hero':
    mass=math.fsum(g['chance_mass'][i*nv+j] for j in range(nv));values=[math.fsum(a[i][j][x][y]*q[j][y] for j in range(nv) for y in range(4)) for x in range(4)]
   else:
    mass=math.fsum(g['chance_mass'][j*nv+i] for j in range(nh));values=[-math.fsum(a[j][i][x][y]*p[j][x] for j in range(nh) for x in range(4)) for y in range(4)]
   ev=[v/mass for v in values] if mass>0 else None;profile=math.fsum(v*w for v,w in zip(ev,ps[i])) if ev is not None else None
   out[k]={'own_marginal_mass':mass,'conditional_arm_ev_bb':ev,'conditional_regret_bb':[v-profile for v in ev] if ev is not None else None,'probabilities':list(ps[i])}
 return out


class TargetTransfer:
 def __init__(self,records,config,geometry=None):
  if not records or any(r['own_marginal_mass']<=0 for r in records):raise ValueError('common positive own-support records required')
  self.records=records;self.config=config;self.geometry=geometry if geometry is not None else feature.Neighbors([CONFIG]);self.cache={}
 def predict(self,k,target):
  ns=self.geometry.get(self.records,k)[CONFIG['name']]
  if not ns:raise ValueError('unsupported own/public type; no fabricated targets')
  return tuple(math.fsum(w*self.records[i][target][a] for i,w in ns) for a in range(4))
 def probabilities(self,k):
  if k in self.cache:return self.cache[k]
  cfg=self.config;prior=self.predict(k,'probabilities')
  if cfg['family'] in ('probability','response'):p=prior
  elif cfg['target']=='conditional_regret_bb':
   v=[max(0.,x) for x in self.predict(k,cfg['target'])];z=math.fsum(v);p=tuple(x/z for x in v) if z else prior
  else:
   v=self.predict(k,cfg['target']);m=max(v);t=cfg['temperature_bb']
   if t:ws=[math.exp((x-m)/t) for x in v]
   else:ws=[float(m-x<=1e-12) for x in v]
   z=math.fsum(ws);p=tuple(x/z for x in ws)
  z=math.fsum(p);self.cache[k]=tuple(x/z for x in p);return self.cache[k]
 def materialize(self,g):return FrozenContinuation({k:self.probabilities(k) for k in g['hkeys']+g['vkeys']})


def build(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);src=Path(__file__).with_suffix('.cc');dest=root/'value-response.so';subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(src),'-o',str(dest)],check=True);lib=C.CDLL(str(dest.resolve()));lib.warm_response.argtypes=[C.c_int,C.c_int,DP,DP,C.c_int,DP,DP];lib.warm_response.restype=C.c_int;return lib


def respond(lib,g,prior,iterations):
 if type(iterations) is not int or not 1<=iterations<=10000000:raise ValueError('fixed positive bounded iteration count required')
 keys=g['hkeys']+g['vkeys']
 if any(k not in prior.table for k in keys):raise ValueError('complete explicit own-type prior required')
 p,q=base.strategies(g,prior);flat=[v for row in g['tensor'] for cell in row for arm in cell for v in arm];start=[v for row in p+q for v in row];avg=(C.c_double*(len(keys)*4))();reg=(C.c_double*(len(keys)*4))()
 if lib.warm_response(len(p),len(q),doubles(flat),doubles(start),iterations,avg,reg):raise ValueError('invalid response game or prior')
 result=FrozenContinuation({k:tuple(v/math.fsum(avg[i*4:i*4+4]) for v in avg[i*4:i*4+4]) for i,k in enumerate(keys)});metrics=base.evaluate(g,result);bound=math.fsum(max(0.,max(reg[i*4:i*4+4])) for i in range(len(keys)))/iterations
 if metrics['restricted_nashconv_bb']>bound+1e-7:raise ValueError('response external-regret identity failed')
 metrics.update(iterations=iterations,positive_external_regret_bound_bb=bound,first_iteration='transferred prior; zero initial regrets',transductive_board_specific_planning=True,global_model_updated=False)
 return result,metrics
