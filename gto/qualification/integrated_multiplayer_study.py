"""Existing6/9 CP warmstart; same-budget chance-batch integration, native holdout."""
import copy,gzip,json,random,resource,time
from pathlib import Path
import numpy as np
from gto.qualification.integrated_solver import Multiplayer
from gto.qualification.multiplayer_joint import checked_config,scoped_actions,sparse_key
from gto.qualification.multiplayer_scope import OfflineProfile,replay
from gto.qualification.build import load
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
from gto.qualification.action_native import interval
from gto.native.training import NativeGame

ROOT=Path('docs/qa/integrated-solver-20261126/multiplayer')
OLD=Path('docs/qa/sparse-generalization-20261124/multiplayer-lazy')

def restore(native,n,seed,batch):
    path=OLD/f'{n}max-{seed}-final.json.gz';state=json.loads(gzip.decompress(path.read_bytes()));identity=state['identity']
    if state['digest']!=digest({k:v for k,v in state.items() if k!='digest'}):raise ValueError('old N CP integrity')
    if sha(Path('gto/qualification/multiplayer_joint.py'))!=identity['source_sha256']:raise ValueError('protected N source')
    game=NativeGame(identity['config']['stacks'],bba=2,rake_num=1,rake_den=20)
    q=Multiplayer(native,game,seed=seed,chance_batch=batch,average_mode='lazy',max_nodes=20000,max_seconds=5,max_infosets=20000)
    if checked_config(game)!=identity['config']:raise ValueError('N game')
    q.identity['migration']=dict(old_checkpoint_sha256=sha(path),old_identity_digest=digest(identity),old_native_binary=identity['native_binary_sha256'])
    state['identity']=q.identity;state['digest']=digest({k:v for k,v in state.items() if k!='digest'});q.restore(state);return q,game

def run(out=ROOT,nworlds=512):
    out=Path(out)
    if out.exists() and any(out.iterdir()):raise FileExistsError('fresh N trial required')
    out.mkdir(parents=True,exist_ok=True);_,native=load('/tmp/native-qualification');results=[]
    for n in (6,9):
        for seed in (17124101,17124102):
            qs=[];records=[]
            for batch in (1,2):
                q,game=restore(native,n,seed,batch);initial=q.t;st=time.monotonic();reason='TIME';maxCF=0.
                while time.monotonic()-st<3:
                    try:r=q.step();maxCF=max(maxCF,r['max_CF_scale'])
                    except ValueError as e:reason=str(e);break
                sec=time.monotonic()-st;path=out/f'{n}max-{seed}-batch{batch}.json.gz';q.export(path)
                # Actual new checkpoint state replay, same native build and RNG.
                other,_=restore(native,n,seed,batch);other.restore(q.state());before=copy.deepcopy(q.state());q.step();other.step();assert q.state()==other.state();q.restore(before)
                records.append(dict(batch=batch,initial_iterations=initial,iterations=q.t,seconds=sec,reason=reason,infosets=len(q.actions),max_CF_scale=maxCF,checkpoint_sha256=sha(path),policy_digest=q.policy_digest,actual_next_step_replay=True));qs.append(q)
            rng=random.Random(17136501);worlds=[(rng.sample(range(52),52),rng.getrandbits(128)) for _ in range(nworlds)];profiles=[q.profile() for q in qs]
            values=[[] for _ in range(4)];st=time.monotonic()
            # Legal off-tree minraise at seat2's first preflop turn, heldout only.
            deviated=[]
            for q in qs:
                pi=q.policy()
                def provider(o,pi=pi):
                    a=scoped_actions(o,'preflop');p=pi.get(sparse_key(o),np.ones(len(a))/len(a))
                    if o.actor==2 and o.round==0 and not any(h[1]==2 for h in o.history):
                        raises=[x for x in o.actions if x>1]
                        if raises:return {min(raises):1.}
                    return dict(zip(a,p.tolist()))
                deviated.append(OfflineProfile(game,provider,players=n,provider_digest=digest(dict(base=q.policy_digest,probe='seat2-first-native-minraise'))))
            for deck,tape in worlds:
                if time.monotonic()-st>90:raise RuntimeError('N final budget; no complete receipt')
                for profile,row in zip(profiles+deviated,values):row.append(np.array(replay(native,game,profile,deck=deck,seed=tape)['net_chips'])/2)
            delta=.001/200;metrics=[]
            for i in range(2):
                metrics.append(dict(batch=i+1,EV=[interval([float(v[p]) for v in values[i]],-50,450,delta) for p in range(n)],seat2_minraise_gain=interval([float(a[2]-b[2]) for a,b in zip(values[2+i],values[i])],-500,500,delta)))
            result=dict(players=n,seed=seed,n=nworlds,evaluation_seed=17136501,training=records,metrics=metrics,paired_batch2_minus_batch1=[interval([float(a[p]-b[p]) for a,b in zip(values[1],values[0])],-500,500,delta) for p in range(n)],evaluation_seconds=time.monotonic()-st,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,full_native_BR_upper=None,full_native_NashConv=None,formal_acceptance=0,ordinary_registry_admission=False)
            results.append(result);atomic(out/'results.json',dict(records=results,formal_acceptance=0));print(json.dumps(dict(players=n,seed=seed,training=records,seconds=result['evaluation_seconds'])),flush=True)
    return results

if __name__=='__main__':run()
