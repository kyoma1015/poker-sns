"""Stratified chance batches for existing N-owner external sampling.
The target remains uniform52 or the original explicit finite law. Private cards,
all seats and action proposals are unchanged; HT weights correct stratum draws.
"""
import random
from pathlib import Path
import numpy as np
from gto.qualification.multiplayer_joint import SparseJoint
from gto.qualification import stream_chance as sc
from gto.qualification.fullstreet_solver import public_code
from gto.qualification.policy import sha

class Stratified(SparseJoint):
    def __init__(self,*args,chance_batch=2,**kwargs):
        super().__init__(*args,**kwargs)
        if type(chance_batch) is not int or not 1<=chance_batch<=13:raise ValueError('stratified chance batch')
        self.chance_batch=chance_batch;self.batch=[];self.strata=sorted(sc.strata().items())
        self.identity.update(chance_batch=chance_batch,chance_proposal='full52 systematic-stratum CDF / finite without-replacement HT; raw integration beforeclip',stratified_source_sha256=sha(Path(__file__)),stratum_source_sha256=sha(Path(sc.__file__)))
    def _draw(self):
        if self.decks is not None:
            count=len(self.decks);K=min(count,self.chance_batch);ids=self.rng.sample(range(count),K)
            self.batch=[(list(self.decks[j]),float(self.weights[j])*count/K) for j in ids]
        else:
            K=min(13,self.chance_batch);ids=systematic_indices([w for _,w in self.strata],K,self.rng.random());self.batch=[]
            for j in ids:
                (p,m,c),weight=self.strata[j]
                for trial in range(200000):
                    board=self.rng.sample(range(52),5)
                    if public_code(board)==p and sc.flop_features(board)[1:]==(m,c):break
                else:raise ValueError('conditional board proposal cap')
                other=[x for x in range(52) if x not in board];self.rng.shuffle(other)
                deck=other[:2*self.N]+board+other[2*self.N:]
                self.batch.append((deck,1/K))
        return self.batch[0][0]
    def collect(self,owner,deck,stream,pi,*,audit=False,budget=None):
        if not self.batch:raise ValueError('draw a declared stratified chance batch first')
        out=dict(grad={},avg={},actions={},owners={},info={},max_average_weight=0.,max_CF_scale=0.)
        for world,weight in self.batch:
            part=super().collect(owner,world,random.Random(stream.getrandbits(128)),pi,audit=audit,budget=budget)
            for key in ('grad','avg'):
                for k,v in part[key].items():out[key][k]=out[key].get(k,np.zeros(len(v)))+weight*v
            for key in ('actions','owners','info'):
                for k,v in part[key].items():
                    if k in out[key] and out[key][k]!=v:raise ValueError('N-owner information identity mismatch')
                    out[key][k]=v
            for key in ('max_average_weight','max_CF_scale'):out[key]=max(out[key],part[key])
        return out

    def step(self):
        if self.chance_batch!=self.identity['chance_batch']:raise ValueError('stratified proposal changed')
        return super().step()


def systematic_indices(weights,K,u):
    w=np.asarray(weights,dtype=float)
    if np.any(w<=0) or abs(w.sum()-1)>1e-12 or not 0<=u<1 or K<1:raise ValueError('normalized systematic strata')
    cdf=np.cumsum(w);cdf[-1]=1.
    positions=np.minimum((u+np.arange(K))/K,np.nextafter(1.,0.))
    return np.searchsorted(cdf,positions,side='right').tolist()
