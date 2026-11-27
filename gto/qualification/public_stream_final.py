"""Confirmed research proposal: target-CDF public streaming,64 updates/1000CPU max.
Sampler choice used frozen-gradient development data only. Selection catalogs
and native selection worlds are separate from final native/BR data.
"""
from gto.qualification.public_stream_study import *
from gto.qualification import public_stream_study as base,public_stream_batch as proposal,stream_measure as measurement
ROOT=Path('docs/qa/public-stream-final-20261127')
save=base.save
restore=base.restore

def metric(q,seed,physical=False):
    snapshot=ss.replace_bank(q,sc.catalog(q.lib,seed),average_snapshot=True)
    result=measurement.measure(snapshot,physical);del snapshot;gc.collect();return result

def run(seed,warm):
    folder=ROOT/str(seed)
    if folder.exists():raise FileExistsError('preserve prior public-stream run')
    folder.mkdir(parents=True);start=time.monotonic();rules,native=load('/tmp/native-qualification');lib=ac.build('/tmp/public-stream-'+str(seed));meta=json.load(open(Path(warm)/'identity.json'))
    # Fast, oracle-equivalent active layout; original checkpoint bytes untouched.
    for p,h in meta['sources'].items():
        if sha(Path(p))!=h:raise ValueError('warm executed source '+p)
    if sha(Path(warm)/'checkpoint.npz')!=meta['checkpoint_sha256']:raise ValueError('warm checkpoint SHA')
    if sha(Path(lib._name))!=meta['binary_sha256']:raise ValueError('warm CF binary SHA')
    if sha(Path(meta['initial_checkpoint']))!=meta['initial_sha256']:raise ValueError('warm prior SHA')
    from gto.qualification.public_chance_solver import block
    blocks=[dict(block(lib,b['board'],b['weight']),stratum=b['stratum']) for b in meta['blocks']]
    q=ss.Game(lib,meta['nodes'],blocks,meta['splits']);ac.Game.restore(q,Path(warm)/'checkpoint.npz');active_resume.restore_prior(q,meta['initial_checkpoint']);ss.reset_target(q)
    rng=random.Random(seed+17155101);m=sparse_solver.load(next(Path('/tmp/sparse').glob('*.so')));w,origin=sparse_solver.warm(m,seed);fallback=old.old_policy(m,w,origin,seed);fallback.native=native
    sources=[Path(__file__),Path(proposal.__file__),Path(measurement.__file__),Path(base.__file__),Path(ss.__file__),Path(ss.__file__).with_name('stream_index.py'),Path(stream_features.__file__),Path(stream_features.__file__).with_name('stream_feature_core.cc'),Path(sc.__file__),Path(stream_br.__file__),Path(sampling_policy.__file__),Path(sampling_policy.__file__).with_name('stream_policy.py'),Path(ac.__file__),Path(ac.__file__).with_name('active_chance_core.cc'),Path(active_resume.__file__)]
    identity=dict(schema='public52-target-CDF-active-v1',proposal='systematic target-CDF13; same full52 target; same active CF kernel',seed=seed,nodes=q.nodes,splits=sorted(q.splits),sources={str(p):sha(p) for p in sources},binary_sha256=sha(Path(lib._name)),feature_binary_sha256=sha(Path(stream_features.build()._name)),warm_checkpoint_sha256=meta['checkpoint_sha256'],target='full52 uniform public chance, exact conditional private pairs, fixed bounded action/infoset game',optimizer_initialization='new target: preserve behavior only, R/A zero; subsequent independent banks carry exact R/A',formal_profile=False,ordinary_registry_admission=False)
    save(q,folder/'initial',identity,rng);iv,initial_digest=selector_values(q,fallback,identity,m,native);curve=[];total=index_cpu=CF_cpu=0.;draws=[];best=None;reason='MAX64_UPDATES_OR_CPU1000';last_log=time.monotonic()
    for target_updates in (0,16,32,64):
        budget=target_updates
        if target_updates>32 and (curve[-1]['NC']['NashConv_bb']>curve[-2]['NC']['NashConv_bb']*.95 or curve[-1]['gate']['detected_harm']):reason='NO_POST_BURNIN_TREND_OR_DETECTED_HARM';break
        while q.t<target_updates and total<1000:
            rngbefore=rng.getstate();tick=time.process_time()
            try:
                bank_seed=rng.getrandbits(64);bs=proposal.catalog(lib,bank_seed);nextq=ss.replace_bank(q,bs);mid=time.process_time()
                if nextq.S>10000000:raise MemoryError('10M persistent-cell budget')
                nextq.step();end=time.process_time()
            except (MemoryError,ValueError):rng.setstate(rngbefore);reason='BUDGET_OR_INCOMPLETE_UPDATE';raise
            index_cpu+=mid-tick;CF_cpu+=end-mid;total=index_cpu+CF_cpu;q=nextq;del nextq;draws.append(dict(seed=bank_seed,boards=[b['board'] for b in bs]));gc.collect()
            if time.monotonic()-last_log>30:print(json.dumps(dict(seed=seed,t=q.t,CPU=total,cells=q.S,RSS=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)),flush=True);last_log=time.monotonic()
        nc=metric(q,17153201+seed);v,pdigest=selector_values(q,fallback,identity,m,native);gate=stream_gate.compare(v,iv);target=folder/('t'+str(int(budget)));save(q,target,identity,rng)
        record=dict(CPU_seconds=total,index_CPU_seconds=index_cpu,CF_CPU_seconds=CF_cpu,t=q.t,cells=q.S,NC=nc,gate=gate,checkpoint=str(target),policy_digest=pdigest);curve.append(record)
        if not gate['detected_harm'] and (best is None or nc['NashConv_bb']<best['NC']['NashConv_bb']):best=record
        atomic(folder/'curve.json',dict(curve=curve,best=best,stop=reason,selection_seed=17153201+seed,final_seed_unused=17153301+seed));atomic(folder/'training-boards.json',dict(batches=draws));print(json.dumps(dict(seed=seed,budget=budget,t=q.t,CPU=total,NC=nc['NashConv_bb'],harm=gate['detected_harm'],RSS=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)),flush=True)
    atomic(folder/'result.json',dict(seed=seed,curve=curve,best=best,last=curve[-1],CPU=total,index_CPU=index_cpu,CF_CPU=CF_cpu,drawn_boards=13*len(draws),unique_boards=len({tuple(b) for x in draws for b in x['boards']}),strata=13,stop=reason,wall_seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,formal_pass=0,full_native_BR_upper=None,final_data_not_used=True))
    # Restored object must reproduce the next fresh draw AND the exact next update.
    bank_seed=rng.getrandbits(64);nextq=ss.replace_bank(q,proposal.catalog(lib,bank_seed));nextq.step();expected=[hashlib.sha256(x.tobytes()).hexdigest() for x in (nextq.R,nextq.A,nextq.visits)];del nextq,q;gc.collect();q,_,rng=restore(curve[-1]['checkpoint']);seed2=rng.getrandbits(64);assert seed2==bank_seed;nextq=ss.replace_bank(q,proposal.catalog(q.lib,seed2));nextq.step();assert expected==[hashlib.sha256(x.tobytes()).hexdigest() for x in (nextq.R,nextq.A,nextq.visits)]
    atomic(folder/'replay.json',dict(next_fresh_bank_and_step_exact=True,hashes=expected,bank_seed=bank_seed))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);a.add_argument('--warm',required=True);x=a.parse_args();run(x.seed,x.warm)
