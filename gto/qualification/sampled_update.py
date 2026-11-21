"""Chance-sampled update: both owners use the SAME pre-draw-update strategy.

Sharing a chance draw is safe for simultaneous fixed-profile gradients. Updating
owner0 first and evaluating owner1 against its draw-dependent new strategy is
not the fixed-profile expectation checked by the independent path oracle.
"""
import numpy as np

def step(q):
    pi=q.policy(False);q.t+=1
    for owner in (0,1):
        q.evaluate_owner(pi,owner)
        for start,t,n,k in q.rows:
            if q.nodes[k]['actor']!=owner:continue
            sl=slice(start,start+t*n);np.add(q.R[sl],q.grad[sl],out=q.R[sl]);np.maximum(q.R[sl],0,out=q.R[sl]);q.A[sl]+=q.t*q.avg[sl];q.visits[sl]=np.minimum(65535,q.visits[sl].astype(np.uint32)+(q.den[sl]>0))
