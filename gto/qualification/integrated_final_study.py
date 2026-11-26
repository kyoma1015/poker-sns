"""Corrected single integrated solver: exact inherited support/R/A, root/private integration."""
import argparse,gc,json,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import integrated_study as study,integrated_solver as u,sparse_solver as s
from gto.qualification.policy import sha,act
from gto.qualification.native_mccfr import betting
from gto.qualification.public_response import observe
from gto.qualification.evaluate import atomic
from gto.qualification.sparse_study import archive_save,archive_restore,samples,Force
from gto.qualification.variance_study import compressed
from gto.native.training import NativeGame
ROOT=study.ROOT/'support-preserved'


def make(seed,restore=False):
    rules,native=study.load('/tmp/native-qualification');m=s.load(next(Path('/tmp/sparse').glob('*.so')));im=study.module(next(Path('/tmp/integrated-v3').glob('*.so')));w,origin=s.warm(m,seed)
    q=u.Solver(im,w,origin,seed+2100000,extra_support=[dict(round=0,history=[],actions=[18,19])],rows=500000,root_integration=True);q.native=native
    imported=q.import_preflop_checkpoint(study.OLD/str(seed)/'compact/best',rules);q.identity['study_source_sha256']=sha(Path(__file__));del w;gc.collect()
    if restore:
        meta=json.loads((ROOT/str(seed)/'best/checkpoint.json').read_text())
        for e in meta['identity'].get('adaptive_support',[]):q.add_support(e['round'],e['history'],e['actions'])
        archive_restore(q,ROOT/str(seed)/'best')
    return q,m,rules,imported

def train(seed):
    folder=ROOT/str(seed)
    if folder.exists() and any(folder.iterdir()):raise FileExistsError('preserve all previous trial states')
    folder.mkdir(parents=True,exist_ok=True);q,m,rules,imported=make(seed);game=NativeGame([100,100]);o=observe(betting(rules),(48,49),[])
    before=q.core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,True)
    worlds=samples(17137301,32);baseline=[study.rb_value(q,q.native,game,d,t,m) for d,t in worlds];ranking=[]
    for a in o.actions:
        if a<=1 or a in before['actions']:continue
        v=[study.rb_value(Force(q,a),q.native,game,d,t,m)-x for (d,t),x in zip(worlds,baseline)];ranking.append(dict(action=a,mean=float(np.mean(v))))
    a=max(ranking,key=lambda x:x['mean'])['action'];p=q.row(o,True);q.add_support(0,[],[a]);np.testing.assert_allclose(p,q.row(o,True),atol=1e-14)
    atomic(folder/'inheritance-support.json',dict(imported=imported,before=before['actions'],added=a,ranking=ranking,scope='all inherited action sets/R/A preserved; discovery only, not safety proof'))
    worlds=samples(17137401,512);initial=study.selection(q,q.native,m,worlds);best=initial;archive_save(q,folder/'best');pure=0.;curve=[];reason='PILOT_LIMIT';trend=0
    for target in (5.,10.,30.):
        if target>10 and trend<2:reason='NO_REPEATED_SELECTION_TREND';break
        while pure<target:
            st=time.monotonic();r=q.step(10);pure+=time.monotonic()-st
            if not r['complete']:reason='INCOMPLETE_PAIR_HALT';break
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>768*1024**2:reason='MEMORY_LIMIT';break
        metric=study.selection(q,q.native,m,worlds);row=dict(iterations=q.iteration,selection=metric,pure_seconds=pure,stats=q.core.stats());curve.append(row);print(json.dumps(dict(seed=seed,**row)),flush=True)
        if metric['score']<initial['score']-.05 and metric['gains']['open3p5']<=initial['gains']['open3p5']+.1:trend+=1
        if metric['score']<best['score']-.01 and metric['gains']['open3p5']<=initial['gains']['open3p5']+.1 and metric['EV']>=initial['EV']-.25:
            best=metric;archive_save(q,folder/'best')
        if reason in ('INCOMPLETE_PAIR_HALT','MEMORY_LIMIT'):break
    archive_save(q,folder/'last');last=q.iteration;archive_restore(q,folder/'best')
    atomic(folder/'training.json',dict(seed=seed,initial=initial,best=best,curve=curve,pure_seconds=pure,last_iterations=last,selected_iterations=q.iteration,policy_digest=q.policy_digest,stop_reason=reason,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,formal_acceptance=0,full_native_BR_upper=None))
    return q
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);a.add_argument('--evaluate',action='store_true');a.add_argument('--precision',action='store_true');x=a.parse_args()
    if x.evaluate:
        q,_,_,_=make(x.seed,True);study.evaluate(x.seed,ROOT,16384,provided=q,evaluation_seed=17137501)
    elif x.precision:
        from gto.qualification.integrated_precision import certificate
        q,m,rules,_=make(x.seed,True);certificate(q,rules,m,ROOT/str(x.seed),x.seed)
    else:train(x.seed)
