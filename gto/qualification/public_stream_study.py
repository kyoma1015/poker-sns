"""Full52 public-chance CFR through the successful active/private-vector kernel.
Fresh, independently stratified13-board batch EVERY optimizer update. Persistent
R/A are carried exactly; a new draw never clears optimizer history. Full native
legal-size/abstraction BR bounds remain UNKNOWN.
"""
import argparse,gc,hashlib,io,json,random,resource,subprocess,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from gto.qualification import active_chance as ac,active_resume,stream_chance as sc,stream_sampling as ss,stream_features,stream_br,sampling_policy,stream_gate,sparse_solver,integrated_study as old
from gto.qualification.build import load
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
ROOT=Path('docs/qa/public-stream-20261127')

def plain(x):
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,(list,tuple)):return [plain(y) for y in x]
    return x

def freeze(x):return tuple(freeze(y) for y in x) if isinstance(x,list) else x

def layout(q):
    ids={};keys=[];which=[]
    for row in q.keys:
        if row is None:which.append(-1);continue
        key=id(row)
        if key not in ids:ids[key]=len(keys);keys.append(plain(row))
        which.append(ids[key])
    return dict(keysets=keys,node_keyset=which)

def save(q,folder,identity,rng):
    folder=Path(folder)
    if folder.exists():raise FileExistsError('immutable public-stream checkpoint')
    folder.mkdir(parents=True);start=time.monotonic();entries=[]
    # Shards stay well below GitHub's per-blob limit; lossless zstd reused.
    for field in ('R','A','prior','visits'):
        array=getattr(q,field)
        for offset in range(0,q.S,500000):
            stream=io.BytesIO();np.save(stream,array[offset:offset+500000],allow_pickle=False);path=folder/f'{field}-{offset}.npy.zst'
            with path.open('wb') as out:subprocess.run(['zstd','-q','-1','-c'],input=stream.getvalue(),stdout=out,check=True)
            entries.append(dict(field=field,offset=offset,path=path.name,sha256=sha(path)))
    meta=dict(identity,blocks=[{k:b[k] for k in ('board','weight','stratum')} for b in q.blocks],S=q.S,t=q.t,rng=plain(rng.getstate()),layout=layout(q),arrays=entries)
    raw=json.dumps(meta,sort_keys=True,separators=(',',':')).encode();path=folder/'identity.json.zst'
    with path.open('wb') as out:subprocess.run(['zstd','-q','-1','-c'],input=raw,stdout=out,check=True)
    atomic(folder/'receipt.json',dict(identity_sha256=sha(path),t=q.t,S=q.S,policy_A_sha256=hashlib.sha256(q.A.tobytes()).hexdigest(),seconds=time.monotonic()-start,formal_pass=False))
    return meta

def restore(folder):
    folder=Path(folder);receipt=json.load(open(folder/'receipt.json'));path=folder/'identity.json.zst'
    if sha(path)!=receipt['identity_sha256']:raise ValueError('stream identity SHA')
    meta=json.loads(subprocess.check_output(['zstd','-q','-d','-c',str(path)]))
    for p,h in meta['sources'].items():
        if sha(Path(p))!=h:raise ValueError('public-stream source identity '+p)
    lib=ac.build('/tmp/public-stream-resume-'+str(meta['seed']))
    if sha(Path(lib._name))!=meta['binary_sha256']:raise ValueError('CF build identity')
    if sha(Path(stream_features.build()._name))!=meta['feature_binary_sha256']:raise ValueError('feature build identity')
    from gto.qualification.public_chance_solver import block
    blocks=[dict(block(lib,b['board'],b['weight']),stratum=b['stratum']) for b in meta['blocks']]
    keysets=[[freeze(k) for k in row] for row in meta['layout']['keysets']];keys=[None if j<0 else keysets[j] for j in meta['layout']['node_keyset']]
    bases=[];rows=[];S=0
    for k,n in enumerate(meta['nodes']):
        bases.append(S)
        if n['actor']>=0:count=len(n['children']);rows.append((S,len(keys[k]),count,k));S+=len(keys[k])*count
    if S!=meta['S']:raise ValueError('active layout size')
    stub=SimpleNamespace(keys=keys,nodes=meta['nodes'],rows=rows,base=bases,t=meta['t'],R=np.zeros(S),A=np.zeros(S),prior=np.zeros(S),visits=np.zeros(S,dtype=np.uint16))
    for entry in meta['arrays']:
        p=folder/entry['path']
        if sha(p)!=entry['sha256']:raise ValueError('optimizer shard SHA')
        a=np.load(io.BytesIO(subprocess.check_output(['zstd','-q','-d','-c',str(p)])),allow_pickle=False);dest=getattr(stub,entry['field']);off=entry['offset'];dest[off:off+len(a)]=a
    q=ss.Game(lib,meta['nodes'],blocks,meta['splits'],previous=stub)
    if q.S!=S:raise ValueError('last bank added unexpected infosets')
    q.initial_average=np.zeros(S);q.initial_regret=np.zeros(S);rng=random.Random();rng.setstate(freeze(meta['rng']))
    return q,meta,rng

def metric(q,seed,physical=False):
    # Frozen policy is snapshotted onto an independent selection/final catalog.
    # The inherited parent rule is frozen before drawing this evaluation bank.
    blocks=sc.catalog(q.lib,seed);snapshot=ss.replace_bank(q,blocks,average_snapshot=True)
    value=stream_br.finite_measure(snapshot,physical=physical);del snapshot;gc.collect();return value

def selector_values(q,fallback,identity,m,native):
    # Same native row algorithm; unseen known-node parents are uniform in both
    # training and serving, so gradients and evaluated policy have one definition.
    from gto.qualification.sparse_study import samples,rb_value,Force
    from gto.native.training import NativeGame
    p=sampling_policy.Policy(q,fallback,identity);v=[[] for _ in range(8)];game=NativeGame([100,100])
    for deck,tape in samples(17151201,1024):
        for arm,row in zip([p,*old.probes(p),Force(p,16)],v):row.append(rb_value(arm,native,game,deck,tape,m))
    return np.asarray(v),p.policy_digest

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
    sources=[Path(__file__),Path(ss.__file__),Path(ss.__file__).with_name('stream_index.py'),Path(stream_features.__file__),Path(stream_features.__file__).with_name('stream_feature_core.cc'),Path(sc.__file__),Path(stream_br.__file__),Path(sampling_policy.__file__),Path(sampling_policy.__file__).with_name('stream_policy.py'),Path(ac.__file__),Path(ac.__file__).with_name('active_chance_core.cc'),Path(active_resume.__file__)]
    identity=dict(schema='public52-stratified-active-v1',seed=seed,nodes=q.nodes,splits=sorted(q.splits),sources={str(p):sha(p) for p in sources},binary_sha256=sha(Path(lib._name)),feature_binary_sha256=sha(Path(stream_features.build()._name)),warm_checkpoint_sha256=meta['checkpoint_sha256'],target='full52 uniform public chance, exact conditional private pairs, fixed bounded action/infoset game',optimizer_initialization='new target: preserve behavior only, R/A zero; subsequent independent banks carry exact R/A',formal_profile=False,ordinary_registry_admission=False)
    save(q,folder/'initial',identity,rng);iv,initial_digest=selector_values(q,fallback,identity,m,native);curve=[];total=index_cpu=CF_cpu=0.;draws=[];best=None;reason='CPU720';last_log=time.monotonic()
    for budget in (0.,60.,180.,360.,720.):
        if budget>180 and (curve[-1]['NC']['NashConv_bb']>curve[0]['NC']['NashConv_bb']*.9 or curve[-1]['gate']['detected_harm']):reason='NO_EXTENSION_GATE';break
        while total<budget:
            rngbefore=rng.getstate();tick=time.process_time()
            try:
                bank_seed=rng.getrandbits(64);bs=sc.catalog(lib,bank_seed);nextq=ss.replace_bank(q,bs);mid=time.process_time()
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
    bank_seed=rng.getrandbits(64);nextq=ss.replace_bank(q,sc.catalog(lib,bank_seed));nextq.step();expected=[hashlib.sha256(x.tobytes()).hexdigest() for x in (nextq.R,nextq.A,nextq.visits)];del nextq,q;gc.collect();q,_,rng=restore(curve[-1]['checkpoint']);seed2=rng.getrandbits(64);assert seed2==bank_seed;nextq=ss.replace_bank(q,sc.catalog(q.lib,seed2));nextq.step();assert expected==[hashlib.sha256(x.tobytes()).hexdigest() for x in (nextq.R,nextq.A,nextq.visits)]
    atomic(folder/'replay.json',dict(next_fresh_bank_and_step_exact=True,hashes=expected,bank_seed=bank_seed))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);a.add_argument('--warm',required=True);x=a.parse_args();run(x.seed,x.warm)
