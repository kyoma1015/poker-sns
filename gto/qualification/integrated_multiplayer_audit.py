"""Paired full-deck chance stratification on the existing multiway sampler."""
import copy,json,random,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import integrated_multiplayer_study as prior
from gto.qualification.build import load
from gto.qualification.multiplayer_scope import replay
from gto.qualification.action_native import interval
from gto.qualification.evaluate import atomic
ROOT=Path('docs/qa/integrated-audit-20261126/multiplayer')

def run():
    if ROOT.exists() and any(ROOT.iterdir()):raise FileExistsError('fresh evidence required')
    ROOT.mkdir(parents=True,exist_ok=True);_,native=load('/tmp/native-qualification');results=[]
    for n in (6,9):
        for seed in (17124101,17124102):
            qs=[];training=[]
            for mode in ('iid','seat_rotation'):
                q,game=prior.restore(native,n,seed,2);q.chance_mode=mode;q.identity['chance_mode']=mode;start=time.process_time();before=q.t;reason='CPU_BUDGET'
                while time.process_time()-start<6:
                    try:q.step()
                    except ValueError as e:reason=str(e);break
                pure_cpu=time.process_time()-start;io_start=time.monotonic();path=ROOT/f'{n}max-{seed}-{mode}.json.gz';q.export(path);other,_=prior.restore(native,n,seed,2);other.chance_mode=mode;other.identity['chance_mode']=mode;other.restore(q.state());saved=copy.deepcopy(q.state());q.step();other.step();assert q.state()==other.state();q.restore(saved)
                training.append(dict(mode=mode,from_iterations=before,iterations=q.t,CPU_training_seconds=pure_cpu,checkpoint_replay_wall_seconds=time.monotonic()-io_start,infosets=len(q.actions),stop=reason,nextstep_exact=True));qs.append(q)
            profiles=[q.profile() for q in qs];rng=random.Random(17138501);values=[[],[]];start=time.monotonic()
            for _ in range(1024):
                deck=rng.sample(range(52),52);tape=rng.getrandbits(128)
                for profile,v in zip(profiles,values):v.append(np.array(replay(native,game,profile,deck=deck,seed=tape)['net_chips'])/2)
            paired=[interval([float(a[p]-b[p]) for a,b in zip(values[1],values[0])],-500,500,.001/100) for p in range(n)]
            record=dict(players=n,seed=seed,training=training,worlds=1024,evaluation_seed=17138501,paired_rotation_minus_iid_EV=paired,evaluation_seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,full_native_BR_upper=None,formal_acceptance=0)
            results.append(record);atomic(ROOT/'results.json',dict(records=results));print(json.dumps(record),flush=True)
if __name__=='__main__':run()
