"""Target-probability systematic allocation of a bounded public chance batch.
Every batch is unbiased for uniform52 public chance after conditional draws.
Unlike one-per-small-stratum, rare categories do not consume half the budget.
"""
import random
from gto.qualification.stream_multiplayer import systematic_indices
from gto.qualification.stream_chance import strata,flop_features
from gto.qualification.fullstreet_solver import public_code
from gto.qualification.public_chance_solver import block

def catalog(lib,seed,K=13):
    if not 1<=K<=64:raise ValueError('bounded public chance batch')
    rng=random.Random(seed);table=sorted(strata().items());ids=systematic_indices([p for _,p in table],K,rng.random());out=[]
    for j in ids:
        (p,m,c),weight=table[j]
        for trial in range(200000):
            board=rng.sample(range(52),5)
            if public_code(board)==p and flop_features(board)[1:]==(m,c):break
        else:raise ValueError('conditional board draw cap')
        b=block(lib,board,1/K);b['stratum']=[p,m,c];out.append(b)
    return out
