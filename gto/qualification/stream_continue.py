"""Continue exact optimizer state after the 13-stratum pilot, at most720 CPU sec.
The point-floor selector is retained as a control, never a release decision.
"""
import argparse,gc,hashlib,json,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import stream_study as st,stream_br,stream_gate,sparse_solver,integrated_study as old
from gto.qualification.build import load
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed

def run(seed):
    root=st.ROOT/str(seed);pilot=json.load(open(root/'result.json'));folder=root/'continuation'
    if folder.exists():raise FileExistsError('preserve prior continuation')
    folder.mkdir();q,identity=st.restore(pilot['last']['checkpoint']);rules,native=load('/tmp/native-qualification');m=sparse_solver.load(next(Path('/tmp/sparse').glob('*.so')));w,origin=sparse_solver.warm(m,seed);fallback=old.old_policy(m,w,origin,seed);fallback.native=native
    identity=dict(identity,sources=dict(identity['sources']));identity['sources'].update({str(Path(p)):sha(Path(p)) for p in (__file__,stream_gate.__file__)})
    initial=np.load(root/'initial.npz');saved=(q.R,q.A,q.visits,q.t);q.R=initial['R'];q.A=initial['A'];q.visits=initial['visits'];q.t=0
    iv,ip=stream_gate.values(q,fallback,dict(identity,evaluation='initial'),m,native);q.R,q.A,q.visits,q.t=saved;initial.close();compressed(folder/'selection-initial.json.gz',dict(values=iv.tolist(),digest=ip,seed=17151201))
    pure=pilot['CPU_seconds'];curve=[];best=None;reason='CPU720';before=pilot['last']['NC']['NashConv_bb']
    for budget in (360.,720.):
        if curve and (curve[-1]['gate']['detected_harm'] or curve[-1]['NC']['NashConv_bb']>before*.85):reason='NO_EXTENSION_TREND_OR_HARM';break
        before=curve[-1]['NC']['NashConv_bb'] if curve else before
        while pure<budget:
            tick=time.process_time();q.step();pure+=time.process_time()-tick
        nc=stream_br.finite_measure(q);target=folder/('t'+str(int(budget)));st.checkpoint(q,target,identity)
        meta=json.load(open(target/'identity.json'));v,pdigest=stream_gate.values(q,fallback,meta,m,native);gate=stream_gate.compare(v,iv);compressed(target/'selection-values.json.gz',dict(values=v.tolist(),policy_digest=pdigest,evaluation_seed=17151201))
        record=dict(CPU_seconds=pure,t=q.t,NC=nc,gate=gate,checkpoint=str(target),policy_digest=pdigest);curve.append(record)
        if not gate['detected_harm'] and (best is None or nc['NashConv_bb']<best['NC']['NashConv_bb']):best=record
        atomic(folder/'curve.json',dict(curve=curve,best=best,selection_rule='minimum finite NC among stages without detected paired harm; NOT safety/noninferiority',stop=reason));print(json.dumps(dict(seed=seed,budget=budget,t=q.t,CPU=pure,NC=nc['NashConv_bb'],harm=gate['detected_harm'],RSS=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)),flush=True)
    fine=stream_br.finite_measure(q,physical=True)
    atomic(folder/'result.json',dict(seed=seed,curve=curve,best=best,last=curve[-1],fine_last=fine,stop=reason,CPU_seconds=pure,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,formal_pass=0,full_native_BR_upper=None,selection_data_not_final=True,initial_point_selector_best_t=pilot['best']['t']))
    # Compare exact next-step hashes across a separately reconstructed instance.
    q.step();hashes=[hashlib.sha256(x.tobytes()).hexdigest() for x in (q.R,q.A,q.visits)];del q;gc.collect();q,_=st.restore(curve[-1]['checkpoint']);q.step()
    assert hashes==[hashlib.sha256(x.tobytes()).hexdigest() for x in (q.R,q.A,q.visits)]
    atomic(folder/'replay.json',dict(nextstep_exact=True,R_A_visits_hashes=hashes,source_sha256=sha(Path(__file__)),RNG='none: fixed stratified catalog exact integration'))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);run(a.parse_args().seed)
