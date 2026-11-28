"""Reuse existing sparse CP, PCS and conditional native evaluators on fixed splits."""
import argparse,copy,gc,gzip,importlib.util,json,resource,shutil,subprocess,tempfile,time
from pathlib import Path
import numpy as np
from gto.qualification import sparse_solver as s,integrated_solver as u,fullstreet_solver as f
from gto.qualification.sparse_study import rb_value,samples,archive_save,archive_restore,Force
from gto.qualification.build import load
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.coupled_evaluate import Extra
from gto.qualification.range_study import GeneralNuts
from gto.qualification.native_mccfr import digest,betting
from gto.qualification.public_response import observe
from gto.qualification.policy import sha,act
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed
from gto.qualification.action_native import interval
from gto.native.training import NativeGame

ROOT=Path('docs/qa/integrated-solver-20261126')
OLD=Path('docs/qa/sparse-generalization-20261124/hu-final')

def module(path):
    spec=importlib.util.spec_from_file_location('_integrated_qualification',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def expanded(folder,stage):
    meta=json.loads((folder/'checkpoint.json').read_text());raw=Path(stage)/'checkpoint.bin'
    with raw.open('wb') as out:subprocess.run(['zstd','-d','-q','-c',str(folder/'checkpoint.bin.zst')],stdout=out,check=True)
    if sha(raw)!=meta['sha256']:raise ValueError('original sparse raw SHA')
    return meta,raw

def old_policy(m,w,origin,seed):
    folder=OLD/str(seed)/'compact/best'
    with tempfile.TemporaryDirectory() as stage:
        meta,raw=expanded(folder,stage);identity=meta['identity']
        for path,h in identity['sources'].items():
            if sha(Path(path))!=h:raise ValueError('protected old source')
        q=s.Solver(m,w,origin,identity['seed'],sharing=True,extra_support=identity['extra_support'],rows=250000)
        if q.identity['prior_tables_digest']!=identity['prior_tables_digest']:raise ValueError('old prior digest')
        q.core.restore(str(raw),digest(identity));q.iteration=meta['iterations'];q.checkpoint_hash=meta['sha256']
        q.identity=dict(identity,binary_sha256=sha(Path(m.__file__)),evaluation_migration_from=digest(identity))
    return q

def bootstrap(q,seed,rules):
    with tempfile.TemporaryDirectory() as stage:
        meta,raw=expanded(OLD/str(seed)/'compact/best',stage)
        (Path(stage)/'checkpoint.bin.gz').write_bytes(gzip.compress(raw.read_bytes(),mtime=0));(Path(stage)/'checkpoint.json').write_text(json.dumps(meta))
        return s.bootstrap_preflop(q,stage,rules)

def probes(q):return [Extra(q,'open3p5'),Force(q,18),Extra(q,'threebet10p5'),Extra(q,'river_jam'),GeneralNuts(q),Extra(q,'fold')]
KINDS=['open3p5','open8','threebet10p5','river_jam','river_nuts','fold']
SIGNS=[1,1,-1,-1,-1,1]

def selection(q,native,m,worlds):
    values=[[] for _ in range(7)];game=NativeGame([100,100])
    for deck,tape in worlds:
        for policy,row in zip([q]+probes(q),values):row.append(rb_value(policy,native,game,deck,tape,m))
    gains=[float(np.mean(sign*(np.array(v)-values[0]))) for sign,v in zip(SIGNS,values[1:])]
    return dict(EV=float(np.mean(values[0])),gains=dict(zip(KINDS,gains)),score=max(0,*gains))

def current(seed,out,restore=True):
    rules,native=load('/tmp/native-qualification');m=s.load(next(Path('/tmp/sparse').glob('*.so')));im=module(next(Path('/tmp/integrated-v3').glob('*.so')));w,origin=s.warm(m,seed)
    q=u.Solver(im,w,origin,seed+2000000,extra_support=[dict(round=0,history=[],actions=[18,19])],rows=500000,root_integration=True);q.native=native
    parent=ROOT/str(seed)/'best';meta=json.loads((parent/'checkpoint.json').read_text());identity=meta['identity']
    for path,pin in identity['sources'].items():
        path=Path(path);actual=ROOT/'source-v2'/path.name if path.name in ('integrated_solver.py','integrated_native.cc') else path
        if sha(actual)!=pin:raise ValueError('parent source identity: '+str(actual))
    if q.identity['prior_tables_digest']!=identity['prior_tables_digest'] or q.identity['rank_binary_sha256']!=identity['rank_binary_sha256']:raise ValueError('parent prior/rank identity')
    q.identity.update(study_source_sha256=sha(Path(__file__)),continued_from=dict(identity=identity,raw_sha256=meta['sha256'],scope='same game and keys; private/root expectation integrated beforeclip; capacity migration'))
    with tempfile.TemporaryDirectory() as stage:
        raw=Path(stage)/'parent.bin';raw.write_bytes(gzip.decompress((parent/'checkpoint.bin.gz').read_bytes()))
        if sha(raw)!=meta['sha256']:raise ValueError('parent raw identity')
        q.core.restore(str(raw),digest(identity));q.iteration=meta['iterations']
    if q.core.stats()['halted']:raise ValueError('only complete selected parent checkpoint can continue')
    folder=Path(out)/str(seed)
    if restore:
        chosen=json.loads((folder/'best/checkpoint.json').read_text())
        for entry in chosen['identity'].get('adaptive_support',[]):q.add_support(entry['round'],entry['history'],entry['actions'])
        archive_restore(q,folder/'best')
    return q,m,native,rules

def train(seed,out):
    folder=Path(out)/str(seed)
    if folder.exists() and any(folder.iterdir()):raise FileExistsError('fresh root-integrated trial required')
    folder.mkdir(parents=True,exist_ok=True);q,m,native,rules=current(seed,out,False)
    # Validate the source migration against the untouched frozen v2 trajectory.
    old_values=json.loads(gzip.decompress((ROOT/str(seed)/'final-values.json.gz').read_bytes()))['values'][2][0]
    game=NativeGame([100,100]);migration=[]
    for (deck,tape),expected in zip(samples(17136201,64),old_values):
        v=rb_value(q,native,game,deck,tape,m);migration.append(abs(v-expected))
    if max(migration)>1e-12:raise ValueError('migration changed frozen policy')
    b=betting(rules);o=observe(b,(48,49),[]);initial=q.core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,True)
    omitted=[a for a in o.actions if a>1 and a not in initial['actions']];discovery=[];ds=samples(17136601,32)
    base=[rb_value(q,native,game,d,t,m) for d,t in ds]
    for action in omitted:
        v=[rb_value(Force(q,action),native,game,d,t,m)-x for (d,t),x in zip(ds,base)]
        discovery.append(dict(action=action,mean=float(np.mean(v)),error_upper=None))
    worst=max(discovery,key=lambda r:r['mean'])['action'];before=np.array(q.row(o,True));q.add_support(0,[],[worst]);np.testing.assert_allclose(before,q.row(o,True),atol=1e-14)
    atomic(folder/'support.json',dict(before=initial['actions'],added=worst,ranking=discovery,discovery_seed=17136601,n=32,scope='exploration only; no safety/exploit confidence proof',migration_value_max_error=max(migration)))
    worlds=samples(17136701,512);start=selection(q,native,m,worlds);best=start;archive_save(q,folder/'best');curve=[];pure=io=0.;reason='PILOT';maxinverse=0.;improvements=0;startt=q.iteration
    for budget in (10.,30.,90.):
        if budget>10 and improvements<2:reason='NO_REPEATED_SELECTION_TREND';break
        for target in (budget/2,budget):
            while pure<target:
                begin=time.monotonic();r=q.step(10.);pure+=time.monotonic()-begin;maxinverse=max(maxinverse,r.get('max_inverse_proposal',0))
                if not r['complete']:reason='INCOMPLETE_PAIR_HALT';break
                if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>768*1024**2:reason='MEMORY_STOP';break
            metric=selection(q,native,m,worlds);row=dict(iterations=q.iteration,new_updates=q.iteration-startt,pure_seconds=pure,selection=metric,stats=q.core.stats(),max_effective_inverse_proposal=maxinverse);curve.append(row);print(json.dumps(dict(seed=seed,**row)),flush=True)
            if metric['score']<best['score']-.01 and metric['gains']['open3p5']<=start['gains']['open3p5']+.1 and metric['EV']>=start['EV']-.25:
                best=metric;improvements+=1;begin=time.monotonic();archive_save(q,folder/'best');io+=time.monotonic()-begin
            atomic(folder/'curve.json',dict(initial=start,curve=curve,formal_pass=False))
            if reason in ('INCOMPLETE_PAIR_HALT','MEMORY_STOP'):break
        if reason in ('INCOMPLETE_PAIR_HALT','MEMORY_STOP'):break
    archive_save(q,folder/'last');last=q.iteration;archive_restore(q,folder/'best');frozen=q.policy_digest
    freq={}
    from gto.abstract import model
    for name,prefix in [('rfi',[]),('vs_open3',[8]),('vs_open3p5',[9]),('vs_3bet10',[8,22]),('vs_3bet10p5',[8,23])]:
        b=betting(rules)
        for a in prefix:act(b,a)
        freq[name]={label:dict(actions=observe(b,g[0],[]).actions,frequency=q.row(observe(b,g[0],[]),True),native_action_EV_interval=None) for label,g in zip(model.CLASSES,model.classes())}
    compressed(folder/'169-frequencies.json.gz',dict(policy_digest=frozen,rows=freq,formal_precision_cells=0))
    atomic(folder/'training.json',dict(seed=seed,parent_iterations=startt,selected_iterations=q.iteration,last_iterations=last,curve=curve,initial=start,best=best,pure_training_seconds=pure,timed_best_IO_seconds=io,stop_reason=reason,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,policy_digest=frozen,full_native_BR_upper=None,full_native_NashConv=None,formal_acceptance=0))
    return q

class Track:
    def __init__(self,q):self.q=q;self.count={r:dict(queries=0,regret=0,average=0,both=0) for r in range(4)}
    def row(self,o,average=False):
        q=self.q;c=self.count[o.round];c['queries']+=1
        r=q.core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,True)
        a=r['visits']>0;b=r['averages']>0;c['regret']+=a;c['average']+=b;c['both']+=a and b
        p=r['probabilities'];assert abs(sum(p)-1)<1e-10;return p

def evaluate(seed,out,n=16384,provided=None,evaluation_seed=17136201):
    folder=Path(out)/str(seed);rules,native=load('/tmp/native-qualification');m=s.load(next(Path('/tmp/sparse').glob('*.so')));w,origin=s.warm(m,seed)
    old=old_policy(m,w,origin,seed);old.native=native
    if provided is not None:q=provided
    else:
        q,_,_,_=current(seed,out,True)
    q.native=native
    base=load_policy('/tmp/native-qualification',f.old.ARTIFACT);pcsfolder=Path('docs/qa/public-chance-20261125/warm')/str(seed);meta=json.loads((pcsfolder/'policy.json').read_text());data=np.load(pcsfolder/'policy.npz');pi=data['pi'];mass=(data['average_mass']>0).astype(np.uint8);data.close()
    pcs=f.Policy(meta,pi,mass,q.ranklib,base);pcs._digest=meta['policy_digest'];del w,pi,mass;gc.collect()
    profiles=[old,pcs,q];names=['old_sparse','old_PCS','integrated'];ids=[x.policy_digest for x in profiles];track=Track(q)
    values=[[[] for _ in range(7)] for _ in profiles];st=time.monotonic();game=NativeGame([100,100]);worlds=samples(evaluation_seed,n)
    for i,(deck,tape) in enumerate(worlds):
        if time.monotonic()-st>120:raise RuntimeError('native final budget; no completed receipt')
        for j,policy in enumerate(profiles):
            for p,row in zip([track if j==2 else policy]+probes(policy),values[j]):row.append(rb_value(p,native,game,deck,tape,m))
        if (i+1)%2048==0:print(json.dumps(dict(seed=seed,final_worlds=i+1,seconds=time.monotonic()-st)),flush=True)
    delta=.001/100;reports=[]
    for name,policy,v in zip(names,profiles,values):
        reports.append(dict(name=name,policy_digest=policy.policy_digest,EV=interval(v[0],-50,50,delta),deviations={k:interval([sign*(a-b) for a,b in zip(row,v[0])],-100,100,delta) for k,sign,row in zip(KINDS,SIGNS,v[1:])}))
    changes=[]
    for a,b in ((1,0),(2,0)):
        changes.append(dict(candidate=names[a],control=names[b],EV=interval([x-y for x,y in zip(values[a][0],values[b][0])],-100,100,delta),open3p5_gain_change=interval([(x-y)-(p-qv) for x,y,p,qv in zip(values[a][1],values[a][0],values[b][1],values[b][0])],-200,200,delta)))
    assert ids==[x.policy_digest for x in profiles]
    compressed(folder/'final-values.json.gz',dict(seed=evaluation_seed,policy_digests=ids,values=values))
    record=dict(seed=seed,evaluation_seed=evaluation_seed,n=n,reports=reports,paired=changes,query_coverage=track.count,seconds=time.monotonic()-st,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,confidence_family=.999,allocated_events=100,full_native_BR_upper=None,full_native_NashConv=None,formal_precision_cells=0,ordinary_registry_admission=False)
    atomic(folder/'final.json',record);print(json.dumps(record),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);a.add_argument('--out',default=str(ROOT/'root-integrated'));a.add_argument('--evaluate',action='store_true');a.add_argument('--n',type=int,default=16384);x=a.parse_args();(evaluate(x.seed,x.out,x.n,evaluation_seed=17136801) if x.evaluate else train(x.seed,x.out))
