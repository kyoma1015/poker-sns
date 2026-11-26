"""Stage30 continuation of the SAME root-integrated solver; no final selection."""
import argparse,gc,gzip,json,resource,tempfile,time
from pathlib import Path
from gto.qualification import integrated_solver as u,sparse_solver as s,integrated_study as study
from gto.qualification.policy import sha
from gto.qualification.native_mccfr import digest
from gto.qualification.evaluate import atomic
from gto.qualification.sparse_study import samples,archive_save,archive_restore

ROOT=study.ROOT/'extension'

def make(seed,restore=False):
    rules,native=study.load('/tmp/native-qualification')
    base=study.ROOT/'root-integrated'/str(seed)/'best';meta=json.loads((base/'checkpoint.json').read_text());parent=meta['identity']
    for path,h in parent['sources'].items():
        if sha(Path(path))!=h:raise ValueError('root parent source')
    m=s.load(next(Path('/tmp/sparse').glob('*.so')));im=study.module(next(Path('/tmp/integrated-v3').glob('*.so')));w,origin=s.warm(m,seed)
    q=u.Solver(im,w,origin,seed+2000000,extra_support=[dict(round=0,history=[],actions=[18,19])],rows=1500000,root_integration=True)
    if q.identity['binary_sha256']!=parent['binary_sha256'] or q.identity['prior_tables_digest']!=parent['prior_tables_digest']:raise ValueError('same estimator/build/prior required')
    q.identity=dict(parent,rows=1500000,capacity_continuation=dict(parent_sha256=meta['sha256'],parent_identity_digest=digest(parent),driver_sha256=sha(Path(__file__)),memory_limit=1536*1024**2,seconds=30))
    with tempfile.TemporaryDirectory() as stage:
        raw=Path(stage)/'parent.bin';raw.write_bytes(gzip.decompress((base/'checkpoint.bin.gz').read_bytes()))
        if sha(raw)!=meta['sha256']:raise ValueError('root parent bytes')
        q.core.restore(str(raw),digest(parent));q.iteration=meta['iterations']
    if restore:archive_restore(q,ROOT/str(seed)/'best')
    q.native=native
    return q,m

def train(seed):
    folder=ROOT/str(seed)
    if folder.exists() and any(folder.iterdir()):raise FileExistsError('fresh extension required')
    folder.mkdir(parents=True,exist_ok=True);q,m=make(seed);initial=q.iteration;worlds=samples(17136701,512);best=study.selection(q,q.native,m,worlds);archive_save(q,folder/'best');curve=[];pure=0.;reason='STAGE30_LIMIT';maxinverse=0
    for target in (15.,30.):
        while pure<target:
            st=time.monotonic();r=q.step(10.);pure+=time.monotonic()-st;maxinverse=max(maxinverse,r['max_inverse_proposal'])
            if not r['complete']:reason='INCOMPLETE_PAIR_HALT';break
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>1536*1024**2:reason='MEMORY_STOP';break
        metric=study.selection(q,q.native,m,worlds);row=dict(iterations=q.iteration,selection=metric,pure_seconds=pure,stats=q.core.stats(),max_effective_inverse_proposal=maxinverse);curve.append(row);print(json.dumps(row),flush=True)
        if metric['score']<best['score']-.01 and metric['gains']['open3p5']<=best['gains']['open3p5']+.1:
            best=metric;archive_save(q,folder/'best')
        atomic(folder/'curve.json',dict(curve=curve,formal_pass=False))
        if reason!='STAGE30_LIMIT':break
    archive_save(q,folder/'last');last=q.iteration;archive_restore(q,folder/'best')
    atomic(folder/'training.json',dict(seed=seed,start_iterations=initial,last_iterations=last,selected_iterations=q.iteration,best=best,curve=curve,pure_seconds=pure,stop_reason=reason,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,policy_digest=q.policy_digest,full_native_BR_upper=None,formal_acceptance=0,scope='same solver;26..50 replay included in elapsed/iterations, not claimed new twice'))
    return q
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,default=17120102);a.add_argument('--evaluate',action='store_true');x=a.parse_args()
    if x.evaluate:
        q,_=make(x.seed,True);study.evaluate(x.seed,ROOT,16384,provided=q,evaluation_seed=17137001)
    else:train(x.seed)
