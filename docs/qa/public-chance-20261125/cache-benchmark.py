import json,time,statistics
import numpy as np
from pathlib import Path
from gto.qualification import public_chance_solver as p,fullstreet_solver as f
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.native_mccfr import betting
from gto.qualification.public_response import observe
from gto.qualification.evaluate import atomic
root=Path('docs/qa/public-chance-20261125/warm/17120101');st=time.monotonic();lib=p.build('/tmp/pcs');build=time.monotonic()-st
st=time.monotonic();meta=json.loads((root/'policy.json').read_text());d=np.load(root/'policy.npz');base=load_policy('/tmp/native-qualification',f.old.ARTIFACT);q=f.Policy(meta,d['pi'],d['average_mass'],lib,base);load=time.monotonic()-st
obs=observe(betting(base.rules),(48,49),[]);q.row(obs);times=[]
for _ in range(1000):
 st=time.perf_counter_ns();q.row(obs);times.append(time.perf_counter_ns()-st)
r=dict(compressed_policy_bytes=(root/'policy.npz').stat().st_size,build_seconds=build,load_seconds=load,root_cached_row_median_us=statistics.median(times)/1000,root_cached_row_p95_us=sorted(times)[949]/1000,scope='isolated Python in-process frozen policy lookup, NOT app/network/on-demand solve/GTO accuracy SLA',cache_miss_certified_solve_seconds=None,full_release_compute_seconds=None)
atomic('docs/qa/public-chance-20261125/cache-feasibility.json',r);print(r)
