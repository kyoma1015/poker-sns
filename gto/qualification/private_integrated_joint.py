"""Small finite N-game integration gate for the existing external sampler.
Integrate chance and opponent proposals BEFORE CFR+ clipping. Never used as a
6/9-player full-tree implementation or full-native quality certificate.
"""
import random
import numpy as np
from gto.qualification.multiplayer_joint import SparseJoint
from gto.qualification.policy import sha
from pathlib import Path

class FiniteIntegratedJoint(SparseJoint):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.N!=3 or self.decks is None or self.average_mode!='sampled':
            raise ValueError('finite three-player oracle gate only')
        self.identity['integration']='finite chance and opponent-action expectation before clipping'
        self.identity['integration_source_sha256']=sha(Path(__file__))
    def collect(self,owner,deck,stream,pi,*,audit=False,budget=None):
        out=dict(grad={},avg={},actions={},owners={},info={},max_average_weight=0.,max_CF_scale=0.)
        for world,weight in zip(self.decks,self.weights):
            part=super().collect(owner,world,random.Random(stream.getrandbits(128)),pi,audit=True,budget=budget)
            for key in ('grad','avg'):
                for k,v in part[key].items():
                    if k not in out[key]:out[key][k]=np.zeros(len(v))
                    out[key][k]+=weight*v
            for key in ('actions','owners','info'):
                for k,v in part[key].items():
                    if k in out[key] and out[key][k]!=v:raise ValueError('shared information constraint mismatch')
                    out[key][k]=v
            for key in ('max_average_weight','max_CF_scale'):out[key]=max(out[key],part[key])
        return out
