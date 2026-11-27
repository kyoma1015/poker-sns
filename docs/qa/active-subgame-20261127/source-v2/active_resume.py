"""Restore the complete deterministic active-solver bundle, including warm prior.
An R/A-only file is insufficient when all positive regrets vanish. The immutable
initial A rows encode the split warm prior; both files must pass their SHA pins.
"""
from pathlib import Path
import json
import numpy as np
from gto.qualification.policy import sha
from gto.qualification import active_chance as ac,public_chance_solver as pcs

def restore_prior(q,initial):
    with np.load(initial) as data:
        q.initial_average=data['A'].copy();q.initial_regret=data['R'].copy()
        for st,t,n,k in q.rows:
            a=data['A'][st:st+t*n].reshape(t,n);z=a.sum(axis=1)[:,None]
            if np.any(z<=0):raise ValueError('initial warm average must cover every indexed row')
            q.prior[st:st+t*n]=(a/z).ravel()

def restore(folder,directory):
    folder=Path(folder);identity=json.loads((folder/'identity.json').read_text())
    for name,key in (('checkpoint.npz','checkpoint_sha256'),('initial.npz','initial_sha256')):
        if sha(folder/name)!=identity[key]:raise ValueError('checkpoint bundle SHA: '+name)
    for p,h in identity['sources'].items():
        if sha(Path(p))!=h:
            # Only the experiment driver changed after execution (vectorized
            # initialization). All policy/kernel dependencies still match.
            archived=folder.parents[1]/'source-v1'/Path(p).name
            if Path(p).name!='active_study.py' or not archived.exists() or sha(archived)!=h:raise ValueError('source identity: '+p)
    lib=ac.build(directory)
    if sha(Path(lib._name))!=identity['binary_sha256']:raise ValueError('build identity')
    blocks=[pcs.block(lib,b,.5) for b in identity['boards']]
    q=ac.Game(lib,identity['nodes'],blocks,identity['splits']);q.restore(folder/'checkpoint.npz');restore_prior(q,folder/'initial.npz')
    return q,identity
