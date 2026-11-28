"""Conditional caller-range integration with valid dyadic empirical-Bernstein CIs.
A precision proposal only, not formal acceptance. Policy/target/range are frozen.
The sample-variance upper n*mean*(1-mean)/(n-1) is valid for X in[0,1], including
ties. Union-bound dyadic confidence spending makes outcome-dependent stopping
valid. Quantized CDF mass discrepancy is explicitly included in the EV radius.
"""
import ctypes as C,subprocess,tempfile,math,random,itertools
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification.policy import sha
from gto.qualification import integrated_precision as old
_LIB=None

def build():
 global _LIB
 if _LIB is None:
  d=Path(tempfile.mkdtemp(prefix='range-ev-'));p=d/'range-ev.so';subprocess.run(['c++','-std=c++17','-O3','-fno-fast-math','-ffp-contract=off','-shared','-fPIC',str(Path(__file__).with_name('range_ev_core.cc')),'-o',str(p)],check=True);_LIB=C.CDLL(str(p));_LIB.range_equity.argtypes=[model.IP,model.IP,C.c_int,model.IP,model.DP,C.c_int,C.c_uint64,C.c_uint64,model.DP];_LIB.range_equity.restype=C.c_int
 return _LIB

def equity(own,pairs,prob,n,seed,prefix=()):
 cdf=np.cumsum(prob,dtype=float);cdf[-1]=1.;value=C.c_double();a=np.ascontiguousarray(pairs,dtype=np.int32).ravel();lib=build();rc=lib.range_equity(model.ints(own),model.ints(prefix),len(prefix),a.ctypes.data_as(model.IP),cdf.ctypes.data_as(model.DP),len(pairs),n,seed,C.byref(value))
 if rc:raise ValueError('conditional range evaluator '+str(rc))
 # Target normalized float weights vs implemented53bit-CDF distribution.
 # Each cumulative threshold has at most2^-53 probability discrepancy.
 sampled=np.diff(np.r_[0.,cdf]);tv=.5*float(np.abs(sampled-np.asarray(prob)).sum())+len(prob)/2**53
 return value.value,tv

def radius(mean,n,delta):
 if n<2 or not 0<=mean<=1 or not 0<delta<1:raise ValueError('bounded EB arguments')
 log=math.log(4/delta);variance=n*mean*(1-mean)/(n-1)
 return min(1.,math.sqrt(2*variance*log/n)+7*log/(3*(n-1)))

def cell(own,pairs,weights,calls,profit,*,delta,seed,halfwidth=.05,max_power=25):
 mass=np.asarray(weights)*np.asarray(calls);Cmass=float(mass.sum())
 if Cmass<=0:return dict(EV=profit,interval=[profit,profit],halfwidth=0.,exact=True,n=0)
 probs=mass/Cmass;rng=random.Random(seed);total=0.;count=0;trace=[]
 for k,power in enumerate(range(18,max_power+1),1):
  target=2**power;n=target-count;mean,tv=equity(own,pairs,probs,n,rng.getrandbits(64));total+=n*mean;count=target;average=total/count;spend=delta/(2*k*(k+1));eb=radius(average,count,spend);hoeffding=math.sqrt(math.log(2/spend)/(2*count));hw=100*Cmass*(min(eb,hoeffding)+tv)+1e-10;value=profit+Cmass*(100*average-50-profit);trace.append(dict(n=count,halfwidth=hw,EB_halfwidth=100*Cmass*(eb+tv)+1e-10,Hoeffding_halfwidth=100*Cmass*(hoeffding+tv)+1e-10))
  if hw<=halfwidth:break
 return dict(EV=value,interval=[max(-50,value-hw),min(50,value+hw)],halfwidth=hw,n=count,call_mass=Cmass,CDF_bias_upper=100*Cmass*tv,proposal_precision_pass=hw<=halfwidth,exact=False,confidence_spending='delta/(2*k(k+1)) per EB/Hoeffding bound; min radius, union-valid; CDF error included',trace=trace,formal_precision_pass=False)
