"""Predeclared staged stratified active-CFR gate. Unqualified HU50 only."""
import argparse,gc,hashlib,json,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import active_chance as ac,active_resume,stream_chance as sc,stream_br,stream_policy
from gto.qualification import sparse_solver,integrated_study as old
from gto.qualification.sparse_study import samples,rb_value,Force
from gto.qualification.build import load
from gto.native.training import NativeGame
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
ROOT=Path('docs/qa/stream-subgame-20261127')
PARENT=Path('docs/qa/active-subgame-20261127')


def checkpoint(q,out,identity):
    out.mkdir(parents=True,exist_ok=True);st=time.monotonic();q.save(out/'checkpoint.npz')
    atomic(out/'identity.json',dict(identity,checkpoint_sha256=sha(out/'checkpoint.npz'),t=q.t))
    return time.monotonic()-st


def restore(folder):
    folder=Path(folder);identity=json.load(open(folder/'identity.json'));p=folder/'checkpoint.npz'
    if sha(p)!=identity['checkpoint_sha256']:raise ValueError('stream checkpoint SHA')
    for file,h in identity['sources'].items():
        if sha(Path(file))!=h:raise ValueError('stream source identity '+file)
    lib=ac.build('/tmp/stream-resume-'+str(identity['seed']))
    if sha(Path(lib._name))!=identity['binary_sha256']:raise ValueError('stream binary identity')
    from gto.qualification.public_chance_solver import block
    blocks=[dict(block(lib,b['board'],b['weight']),stratum=b['stratum']) for b in identity['blocks']]
    q=sc.Game(lib,identity['nodes'],blocks,identity['splits']);q.restore(p)
    initial=Path(identity['initial_checkpoint'])
    if sha(initial)!=identity['initial_sha256']:raise ValueError('stream initial prior SHA')
    active_resume.restore_prior(q,initial)
    return q,identity


def selection(q,fallback,identity,m,native):
    policy=stream_policy.Policy(q,fallback,identity);v=[[] for _ in range(8)];game=NativeGame([100,100])
    for deck,tape in samples(17151201,1024):
        for arm,row in zip([policy,*old.probes(policy),Force(policy,16)],v):row.append(rb_value(arm,native,game,deck,tape,m))
    gains={kind:float(np.mean(sign*(np.asarray(row)-v[0]))) for kind,sign,row in zip(old.KINDS+['open7'],old.SIGNS+[1],v[1:])}
    score=max(0,gains['open3p5'],gains['open8'],gains['open7'],gains['fold'])+max(0,gains['threebet10p5'],gains['river_jam'],gains['river_nuts'])
    return dict(score=score,EV=float(np.mean(v[0])),gains=gains,policy_digest=policy.policy_digest,scope='selection only; no significance/PASS claim')


def run(seed):
    out=ROOT/str(seed)
    if out.exists():raise FileExistsError('preserve previous experiment')
    out.mkdir(parents=True);start=time.monotonic();rules,native=load('/tmp/native-qualification')
    parent,oldid=active_resume.restore(PARENT/str(seed)/'bounded','/tmp/stream-parent-'+str(seed))
    # Actual saved bytes, source/build and next-step oracle, not just a ledger.
    parent.step();proof=np.load(PARENT/str(seed)/'bounded/nextstep-proof.npz')
    for name in ('R','A','visits'):np.testing.assert_array_equal(getattr(parent,name),proof[name])
    parent.restore(PARENT/str(seed)/'bounded/checkpoint.npz');proof.close()
    nodes=sc.expanded_tree(rules,[0,1,6,7,8,9,10,12,16,18,19,102],[23]);mapping=sc.node_map(parent.nodes,nodes)
    splits=set()
    for oldnode,code in parent.splits:
        k=mapping[oldnode];r=nodes[k]['round'];h=code>>r if code<(169<<r) else (code%(169<<r))>>r
        for public in (0,1,3,7):
            group=public>>(3-r)
            for flags in range(1<<r):splits.add((k,group*(169<<r)+(h<<r)+flags))
    blocks=sc.catalog(parent.lib,17150101+seed);q=sc.Game(parent.lib,nodes,blocks,splits);warm=q.initialize(parent,mapping);del parent;gc.collect()
    if q.S>5000000:raise MemoryError('5M active-cell / checkpoint budget')
    m=sparse_solver.load(next(Path('/tmp/sparse').glob('*.so')));w,origin=sparse_solver.warm(m,seed);fallback=old.old_policy(m,w,origin,seed);fallback.native=native
    sources=[Path(__file__),Path(sc.__file__),Path(stream_br.__file__),Path(stream_policy.__file__),Path(ac.__file__),Path(ac.__file__).with_name('active_chance_core.cc'),Path(ac.__file__).with_name('active_policy.py'),Path(ac.__file__).with_name('public_chance_core.cc')]
    identity=dict(schema='stratified-stream-active-v1',seed=seed,blocks=[{k:b[k] for k in ('board','weight','stratum')} for b in blocks],nodes=nodes,splits=sorted(splits),sources={str(p):sha(p) for p in sources},binary_sha256=sha(Path(q.lib._name)),parent_sha256=oldid['checkpoint_sha256'],formal_profile=False,ordinary_registry_admission=False)
    q.save(out/'initial.npz');identity.update(initial_checkpoint=str(out/'initial.npz'),initial_sha256=sha(out/'initial.npz'))
    curve=[];pure=io=0.;best=None;reason='BUDGET_360';setup=time.monotonic()-start
    for budget in (0.,30.,90.,180.,360.):
        if budget>90 and (curve[-1]['NC']['NashConv_bb']>curve[0]['NC']['NashConv_bb']*.8 or curve[-1]['selection']['score']>curve[0]['selection']['score']+.1):reason='NO_EXTENSION_GATE';break
        if budget==360 and curve[-1]['selection']['score']>min(x['selection']['score'] for x in curve[:3])+.1:reason='SELECTION_WORSENED';break
        while pure<budget:
            st=time.process_time();q.step();pure+=time.process_time()-st
        nc=stream_br.finite_measure(q);sel=selection(q,fallback,identity,m,native)
        stage=out/('t'+str(int(budget)));io+=checkpoint(q,stage,identity)
        record=dict(CPU_seconds=pure,t=q.t,NC=nc,selection=sel,checkpoint=str(stage),peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024);curve.append(record)
        if best is None or sel['score']<best['selection']['score']:best=record
        atomic(out/'curve.json',dict(curve=curve,best=best,stop=reason));print(json.dumps(dict(seed=seed,budget=budget,CPU_seconds=pure,t=q.t,NC=nc['NashConv_bb'],selection=sel['score'],RSS=record['peak_RSS_bytes'])),flush=True)
    # Fine response oracle on final frozen checkpoint, not full-native bound.
    fine=stream_br.finite_measure(q,physical=True)
    atomic(out/'result.json',dict(seed=seed,boards=len(blocks),strata=len(sc.strata()),nodes=len(nodes),cells=q.S,splits=len(splits),warm=warm,curve=curve,best=best,last=curve[-1],fine_last=fine,CPU_seconds=pure,setup_wall_seconds=setup,checkpoint_wall_seconds=io,wall_seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,stop=reason,full_native_BR_upper=None,formal_acceptance=0,verified_RFI=0,verified_3bet=0,parent_actual_nextstep_exact=True))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);run(a.parse_args().seed)
