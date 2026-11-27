"""Pinned historical recovery and bounded matched ablations of the existing solver."""
import argparse,gc,gzip,json,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import integrated_solver as u,integrated_study as old,sparse_solver as s,integrated_br as br
from gto.qualification.policy import sha
from gto.qualification.native_mccfr import digest
from gto.qualification.evaluate import atomic
from gto.qualification.sparse_study import archive_save,archive_restore
ROOT=Path('docs/qa/integrated-audit-20261126');BASE=old.ROOT/'support-preserved'

def archive_save(q,folder):
    # Same raw checkpoint/identity; fast lossless encoding, no solver change.
    import subprocess,tempfile,shutil
    start=time.monotonic();folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='joint-fast-checkpoint-') as d:
        q.save(d);temp=folder/'checkpoint.tmp.zst'
        with temp.open('wb') as out:subprocess.run(['zstd','-1','-q','-c',str(Path(d)/'checkpoint.bin')],stdout=out,check=True)
        temp.replace(folder/'checkpoint.bin.zst');shutil.copyfile(Path(d)/'checkpoint.json',folder/'checkpoint.json')
    q.checkpoint_wall_seconds=getattr(q,'checkpoint_wall_seconds',0.)+time.monotonic()-start


def make(seed,coarse=False,signed=False,rebase=False,linear=True,baseline=False,lazy=False):
    rules,native=old.load('/tmp/native-qualification');m=s.load(next(Path('/tmp/sparse').glob('*.so')));im=old.module(next(Path('/tmp/integrated-audit').glob('*.so')))
    w,origin=s.warm(m,seed);q=u.Solver(im,w,origin,seed+2100000,extra_support=[dict(round=0,history=[],actions=[18,19])],rows=500000,root_integration=True,coarse=coarse,signed_regret=signed,linear_average=linear,baseline=baseline,lazy_rows=lazy)
    q.import_preflop_checkpoint(old.OLD/str(seed)/'compact/best',rules);q.add_support(0,[],[16]);q.native=native
    if rebase:q.rebase_warm()
    return q,m,rules

def historical(seed,which):
    q,m,rules=make(seed);folder=BASE/str(seed)/which;meta=json.loads((folder/'checkpoint.json').read_text());raw=gzip.decompress((folder/'checkpoint.bin.gz').read_bytes())
    import hashlib,tempfile
    if hashlib.sha256(raw).hexdigest()!=meta['sha256']:raise ValueError('historical raw SHA')
    for path,pin in meta['identity']['sources'].items():
        actual=Path(path)
        if actual.name in ('integrated_native.cc','integrated_solver.py'):actual=ROOT/'source-before'/actual.name
        if sha(actual)!=pin:raise ValueError('historical pinned source')
    if q.identity['prior_tables_digest']!=meta['identity']['prior_tables_digest']:raise ValueError('historical prior')
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'old.bin';p.write_bytes(raw);q.core.restore(str(p),digest(meta['identity']))
    q.iteration=meta['iterations'];q.identity['migration']=dict(old_identity_digest=digest(meta['identity']),old_raw_sha256=meta['sha256'],scope='explicit source/binary migration; same legacy options, nextstep must be checked')
    return q,m,rules

def layout(rules):
    meta=json.loads(Path('docs/qa/public-chance-20261125/warm/17120101/policy.json').read_text());nodes=meta['nodes'];return nodes,br.observations(nodes,rules)


def metric(q,nodes,obs,boards):
    rows,projection=br.snapshot(q,nodes,obs,boards);measure=br.measure(q.ranklib,nodes,boards,rows,physical=q.identity.get('physical_BR_primary',False))
    return dict(**measure,projection=projection)


def history(seed):
    records=[];boards=[[0,5,10,15,20],[0,5,10,16,21]]
    for name in ('best','last'):
        q,m,rules=historical(seed,name);nodes,obs=layout(rules);start=time.monotonic();v=metric(q,nodes,obs,boards);records.append(dict(which=name,t=q.iteration,metric=v,seconds=time.monotonic()-start,stats=q.core.stats()));del q;gc.collect()
    atomic(ROOT/f'history-{seed}.json',dict(records=records,boards=boards,scope='explicit projected884-public-node/2board game, not full native NC'));print(json.dumps(records),flush=True)


def ablation(seed,coarse,signed,rebase=False,linear=True,baseline=False,lazy=False):
    tag=('coarse' if coarse else 'fine')+('-signed' if signed else '-clip')+('-rebased' if rebase else '')+('' if linear else '-uniform')+('-baseline' if baseline else '')+('-physical' if lazy else '');folder=ROOT/'ablations'/str(seed)/tag
    if folder.exists() and any(folder.iterdir()):raise FileExistsError('preserve old trial')
    folder.mkdir(parents=True,exist_ok=True);q,m,rules=make(seed,coarse,signed,rebase,linear,baseline,lazy);q.identity['physical_BR_primary']=lazy;q.identity['audit_source_sha256']=sha(Path(__file__));nodes,obs=layout(rules)
    import random
    rng=random.Random(17138101);boards=[rng.sample(range(52),5) for _ in range(2)]
    initial=metric(q,nodes,obs,boards);best=initial['NashConv_bb'];archive_save(q,folder/'best');curve=[dict(t=0,pure_seconds=0.,metric=initial)];pure=0.;reason='BUDGET'
    for target in (4,16,64,256):
        while q.iteration<target and pure<30:
            start=time.process_time();r=q.step(5);pure+=time.process_time()-start
            if not r['complete']:reason='INCOMPLETE_PAIR';break
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>1500*1024**2:reason='MEMORY';break
        value=metric(q,nodes,obs,boards);row=dict(t=q.iteration,pure_seconds=pure,metric=value,stats=q.core.stats());curve.append(row);print(json.dumps(dict(seed=seed,tag=tag,**row)),flush=True)
        if reason=='BUDGET':
            archive_save(q,folder/'last')
            if value['NashConv_bb']<best:best=value['NashConv_bb'];archive_save(q,folder/'best')
        else:archive_save(q,folder/'halted');break
        if q.iteration>=16 and value['NashConv_bb']>initial['NashConv_bb']*1.25:reason='EARLY_REGRESSION';break
        if pure>=30:break
    archive_restore(q,folder/'best');rng=random.Random(17138601 if lazy else 17138201);final_boards=[rng.sample(range(52),5) for _ in range(2)];final=metric(q,nodes,obs,final_boards)
    atomic(folder/'result.json',dict(seed=seed,tag=tag,initial=initial,curve=curve,selected=q.iteration,pure_seconds=pure,checkpoint_wall_seconds=getattr(q,'checkpoint_wall_seconds',None),final=final,selection_boards=boards,final_boards=final_boards,reason=reason,policy_digest=q.policy_digest,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,full_native_BR_upper=None,formal_acceptance=0))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);a.add_argument('--history',action='store_true');a.add_argument('--coarse',action='store_true');a.add_argument('--signed',action='store_true');a.add_argument('--rebase',action='store_true');a.add_argument('--uniform',action='store_true');a.add_argument('--baseline',action='store_true');a.add_argument('--physical',action='store_true');x=a.parse_args();history(x.seed) if x.history else ablation(x.seed,x.coarse,x.signed,x.rebase,not x.uniform,x.baseline,x.physical)
