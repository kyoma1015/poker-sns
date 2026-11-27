"""Research continuation gate, separate from independent final evaluation.
A max(0, noisy point estimate) score can lock an untrained t0 at zero. Instead,
rank finite-game NC and screen paired native harm with simultaneous intervals.
Absence of detected harm is NOT noninferiority, safety or formal acceptance.
"""
from pathlib import Path
import numpy as np
from gto.qualification import stream_policy,integrated_study as old
from gto.qualification.sparse_study import samples,rb_value,Force
from gto.qualification.action_native import interval
from gto.native.training import NativeGame
from gto.qualification.variance_study import compressed

def values(q,fallback,identity,module,native):
    p=stream_policy.Policy(q,fallback,identity);v=[[] for _ in range(8)];game=NativeGame([100,100])
    for deck,tape in samples(17151201,1024):
        for arm,row in zip([p,*old.probes(p),Force(p,16)],v):row.append(rb_value(arm,native,game,deck,tape,module))
    return np.asarray(v),p.policy_digest

def compare(current,initial):
    out={}
    for kind,sign,j in zip(old.KINDS+['open7'],old.SIGNS+[1],range(1,8)):
        out[kind]=interval((sign*((current[j]-current[0])-(initial[j]-initial[0]))).tolist(),-200,200,.01/16)
    return dict(paired_gain_differences=out,detected_harm=any(x['interval'][0]>0 for x in out.values()),selection_only=True,safety_proof=False,formal_pass=False)
