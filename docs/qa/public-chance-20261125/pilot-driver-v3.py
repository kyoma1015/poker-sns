"""Bounded PCS learning/selection/final evaluation. All outputs UNVERIFIED."""
import argparse,gc,json,random,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import public_chance_solver as p,fullstreet_solver as f
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed
from gto.qualification.native_mccfr import digest


def run(seed,out,seconds=10,warm_state=False):
    out=Path(out)/str(seed);out.mkdir(parents=True,exist_ok=True);lib=p.build('/tmp/pcs')
    parent=Path('docs/qa/fullstreet-generalization-20261121/corrected')/str(seed)
    meta=json.loads((parent/'policy-best.json').read_text());data=np.load(parent/'policy-best.npz')
    assert sha(parent/'policy-best.npz')==meta['array_sha256']
    prior=data['pi'].astype(np.float32);data.close()
    offset=2400000 if warm_state else 2200000
    rng=random.Random(seed+offset);selection=[rng.sample(range(52),5) for _ in range(2)]
    final=[rng.sample(range(52),5) for _ in range(2)];rng=random.Random(seed+offset+100000)
    validation=[p.block(lib,b,.5) for b in selection]
    q=p.Game(lib,meta['nodes'],[p.draw(lib,rng)],prior=prior);del prior;gc.collect()
    warm_t=0
    if warm_state:
        q.restore(parent/'best-checkpoint.npz');warm_t=q.t;q.t=0;q.visits[:]=0
    q.use_blocks(validation);initial=q.measure();q.save(out/'best.npz');best=initial['restricted_NC_bb']
    curve=[];train=0.;io=0.;reason='PILOT_TIME';excluded={tuple(b) for b in selection+final}
    def save():
        nonlocal io
        st=time.monotonic();q.save(out/'best.npz');io+=time.monotonic()-st
    for target in (4,8,16,32,64,128):
        while q.t<target and train<seconds:
            st=time.monotonic()
            b=p.draw(lib,rng)
            while tuple(b['board']) in excluded:b=p.draw(lib,rng)
            q.use_blocks([b]);q.step();train+=time.monotonic()-st
        q.use_blocks(validation);m=q.measure();curve.append(dict(t=q.t,training_seconds=train,selection_NC_bb=m['restricted_NC_bb']))
        if m['restricted_NC_bb']<best-1e-8:best=m['restricted_NC_bb'];save()
        elif len(curve)>=3 and m['restricted_NC_bb']>1.5*initial['restricted_NC_bb']:reason='SEVERE_SELECTION_REGRESSION';break
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>768*1024**2:reason='MEMORY_LIMIT';break
        if train>=seconds:break
    q.restore(out/'best.npz');pi=q.policy();np.savez_compressed(out/'policy.npz',pi=pi,average_mass=q.A,visits=q.visits)
    ident=dict(source_py_sha256=sha(Path(f.__file__)),source_cpp_sha256=sha(Path(f.__file__).with_name('fullstreet_core.cc')),
      binary_sha256=sha(Path(lib._name)),PCS_sources={str(Path(x)):sha(Path(x)) for x in ('gto/qualification/public_chance_solver.py','gto/qualification/public_chance_core.cc','gto/qualification/public_chance_study.py')},
      parent_array_sha256=meta['array_sha256'],warm_checkpoint_sha256=sha(parent/'best-checkpoint.npz') if warm_state else None,warm_old_iterations=warm_t,warm_scope='arbitrary finite initial R/A, not current-chance history',seed=seed,sampling_seed=seed+offset+100000,nodes=q.nodes,bases=q.base,
      iterations=q.t,array_sha256=sha(out/'policy.npz'),chance='uniform ordered full public board, exact all compatible private pairs',
      formal_acceptance=0,ordinary_registry_admission=False)
    ident['policy_digest']=digest(ident);atomic(out/'policy.json',ident)
    atomic(out/'split.json',dict(selection=selection,final=final,training_rng_state=rng.getstate(),selected_before_final=True))
    # Final boards are evaluated once, only after checkpoint/policy freeze.
    q.use_blocks([p.block(lib,b,.5) for b in final]);new=q.measure();old=q.evaluate_owner(q.prior.astype(float),0);oldbb=q.evaluate_owner(q.prior.astype(float),1)
    rows={}
    for start,t,n,k in q.rows:
        if q.nodes[k]['round']==0:rows[str(k)]=dict(native_prefix=q.nodes[k]['native_prefix'],native_actions=q.nodes[k]['native_actions'],frequency=pi[start:start+t*n].reshape(t,n).tolist(),conditional_model_action_EV_bb=new['action_EV_bb'][str(k)],native_EV_precision=None)
    compressed(out/'169-frequency-EV.json.gz',dict(policy_digest=ident['policy_digest'],contexts=rows,formal_precision_cells=0))
    result=dict(seed=seed,initial_selection_NC_bb=initial['restricted_NC_bb'],curve=curve,selected=q.t,stop_reason=reason,training_seconds=train,checkpoint_IO_seconds=io,
      new_final=new,old_same_final=dict(EV_bb=old[0],restricted_NC_bb=old[1]+oldbb[1]),policy_digest=ident['policy_digest'],
      checkpoint_sha256=sha(out/'best.npz'),peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
      full_native_BR_upper=None,full_native_NashConv=None,model_error_upper=None,omitted_size_error_upper=None,formal_precision_cells=0,formal_acceptance=0)
    atomic(out/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('new_final','curve')}),flush=True)
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);a.add_argument('--out',required=True);a.add_argument('--seconds',type=float,default=10);a.add_argument('--warm-state',action='store_true')
    x=a.parse_args();run(x.seed,x.out,x.seconds,x.warm_state)
