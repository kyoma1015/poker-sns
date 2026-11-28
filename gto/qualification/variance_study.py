"""Fixed-budget convergence ablations. No complete BR substitute or admission."""
import argparse
import gzip
import json
import math
import random
import time
from pathlib import Path
from gto.qualification.build import load
from gto.qualification.evaluate import atomic
from gto.qualification.native_mccfr import digest, matching
from gto.qualification.variance_mccfr import VarianceSolver, canonical, canonical_cards
from gto.qualification.public_response import Observation


def compressed(path,data):
    raw=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
    temporary=path.with_suffix('.tmp');temporary.write_bytes(gzip.compress(raw,mtime=0));temporary.replace(path)


def study(build,source,output,seconds=2.,iterations=512,diagnostic_paths=512):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    rules,native=load(build);data=json.loads(Path(source).read_text());arms=[]
    for suits in (False,True):
        for control in (False,True):
            name=('orbit' if suits else 'raw')+('-cv' if control else '-zero')
            frozen=VarianceSolver(rules,native,suits=suits,control=control);frozen.migrate(data)
            # Identical source strategy and random stream within baseline pairs.
            frozen.rng.seed(17112026);norms=[];start=time.monotonic()
            strategy=digest({k:matching(v['R']) for k,v in frozen.rows.items()})
            for i in range(diagnostic_paths):
                if time.monotonic()-start>5:break
                norms.append(frozen.trajectory(i%2,update=False))
            n=len(norms);squared_mean=math.fsum(x*x for row in frozen.gradient_sums.values() for x in row)/n
            variance=(math.fsum(norms)-squared_mean)/(n-1)
            diagnostics=dict(paths=n,seconds=time.monotonic()-start,strategy_digest=strategy,
                             cf_gradient_trace_sample_variance=variance)
            solver=VarianceSolver(rules,native,suits=suits,control=control);solver.migrate(data)
            initial=len(solver.rows);start=time.monotonic();i=0
            while i<iterations and time.monotonic()-start<seconds:
                solver.step();i+=1
                if i%32==0:compressed(out/(name+'-checkpoint.json.gz'),solver.snapshot())
            elapsed=time.monotonic()-start;compressed(out/(name+'-checkpoint.json.gz'),solver.snapshot())
            arms.append(dict(name=name,suits=suits,control=control,source_infosets=len(data['rows']),
                migrated_infosets=initial,training_seconds=elapsed,new_iterations=i,
                policy_digest=solver.policy_digest,coverage=solver.coverage(),diagnostic=diagnostics))
            atomic(out/'comparison.json',dict(source_digest=digest(data),arms=arms,status='RUNNING'))
    # Equal policy and seeds for each control-variate comparison; no hidden
    # approximation game or branch pruning in any arm.
    gates={}
    for prefix in ('raw','orbit'):
        a,b=[x for x in arms if x['name'].startswith(prefix)]
        assert a['diagnostic']['strategy_digest']==b['diagnostic']['strategy_digest']
        assert a['diagnostic']['paths']==b['diagnostic']['paths']
        gates[prefix+'_cv_variance_ratio']=b['diagnostic']['cf_gradient_trace_sample_variance']/a['diagnostic']['cf_gradient_trace_sample_variance']
    atomic(out/'comparison.json',dict(source_digest=digest(data),arms=arms,gates=gates,
        status='BLOCKED_UNVERIFIED',expanded_learning=False,full_br_upper_bb=None,nashconv_bb=None))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--source',required=True)
    p.add_argument('--output',required=True);a=p.parse_args();study(a.build,a.source,a.output)
