"""Matched-budget N-owner stratified integration; independent finite BR/native probes."""
import copy,gzip,json,random,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import stream_multiplayer as sm
from gto.qualification.integrated_solver import Multiplayer
from gto.qualification.multiplayer_joint import Joint,expanded_decks,scoped_actions,sparse_key
from gto.qualification.multiplayer_scope import OfflineProfile,replay
from gto.qualification.build import load
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha
from gto.qualification.action_native import interval
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame
ROOT=Path('docs/qa/stream-subgame-20261127/multiplayer')

def finite(native):
    records=[];game=NativeGame([24,22,20]);decks=expanded_decks(3);exact=Joint(native,game,decks,[.25]*4,max_nodes=5000,action_scope='preflop')
    for seed in (17150201,17150202):
        for mode,cls in [('iid',Multiplayer),('stratified',sm.Stratified)]:
            q=cls(native,game,seed=seed,decks=decks,weights=[.25]*4,chance_batch=4,max_nodes=20000,max_seconds=5,average_mode='lazy');st=time.process_time();reason='CPU12'
            while time.process_time()-st<12:
                try:q.step()
                except ValueError as e:reason=str(e);break
            cpu=time.process_time()-st;learned=q.policy();pi={k:learned.get(k,np.ones(len(a))/len(a)) for k,a in exact.actions.items()};ev=exact.weights@exact.values(pi)[0];br=np.array([exact.br(pi,p) for p in range(3)])
            q.export(ROOT/f'3max-{seed}-{mode}.json.gz');records.append(dict(seed=seed,mode=mode,t=q.t,CPU_seconds=cpu,EV=ev.tolist(),BR=br.tolist(),sum_gain=float((br-ev).sum()),stop=reason));atomic(ROOT/'finite3.json',dict(records=records,existing_exact_reference=.023738946,formal_pass=0));print(json.dumps(records[-1]),flush=True)
    return records

def migrated(native,n,seed,mode):
    path=Path(f'docs/qa/integrated-audit-20261126/multiplayer/{n}max-{seed}-iid.json.gz');state=json.loads(gzip.decompress(path.read_bytes()));identity=state['identity']
    if state['digest']!=digest({k:v for k,v in state.items() if k!='digest'}):raise ValueError('original N-state digest')
    if sha(Path('gto/qualification/multiplayer_joint.py'))!=identity['source_sha256']:raise ValueError('protected N source')
    game=NativeGame(identity['config']['stacks'],bba=2,rake_num=1,rake_den=20)
    cls=Multiplayer if mode=='iid' else sm.Stratified
    q=cls(native,game,seed=identity['seed'],chance_batch=2,average_mode='lazy',max_nodes=20000,max_seconds=5,max_infosets=20000)
    if q.identity['config']!=identity['config']:raise ValueError('original N-game mismatch')
    q.identity['migration']=dict(old_archive_sha256=sha(path),old_identity_digest=digest(identity),target_game_unchanged=True,optimizer_R_A_RNG_unchanged=True)
    state['identity']=q.identity;state['digest']=digest({k:v for k,v in state.items() if k!='digest'});q.restore(state)
    for k,v in state['R'].items():np.testing.assert_array_equal(q.R[k],v)
    return q,game

def probe(q,seat):
    pi=q.policy()
    def provider(o):
        a=scoped_actions(o,'preflop');p=pi.get(sparse_key(o),np.ones(len(a))/len(a))
        if o.actor==seat and o.round==0 and not any(h[1]==seat for h in o.history):
            raises=[x for x in o.actions if x>1]
            if raises:return {min(raises):1.}
        return dict(zip(a,p.tolist()))
    return OfflineProfile(q.game,provider,players=q.N,provider_digest=digest(dict(base=q.policy_digest,seat=seat,probe='first-legal-minraise')))

def run(players=(6,9),finite_gate=True):
    if ROOT.exists():raise FileExistsError('preserve N-study')
    ROOT.mkdir(parents=True);_,native=load('/tmp/native-qualification');records=[]
    if finite_gate:finite(native)
    for n in players:
        for seed in (17124101,17124102):
            qs=[];training=[]
            for mode in ('iid','stratified'):
                q,game=migrated(native,n,seed,mode);before=q.t;st=time.process_time();reason='CPU6'
                while time.process_time()-st<6:
                    try:q.step()
                    except ValueError as e:reason=str(e);break
                cpu=time.process_time()-st;q.export(ROOT/f'{n}max-{seed}-{mode}.json.gz');other,_=migrated(native,n,seed,mode);other.restore(q.state());saved=copy.deepcopy(q.state());outcomes=[]
                for obj in (q,other):
                    try:obj.step();outcomes.append('completed')
                    except ValueError as error:
                        assert obj.state()==saved;outcomes.append('rolled_back:'+str(error))
                assert outcomes[0]==outcomes[1] and q.state()==other.state();q.restore(saved)
                training.append(dict(mode=mode,CPU_seconds=cpu,from_t=before,t=q.t,rows=len(q.actions),stop=reason,nextstep_completed=outcomes[0]=='completed',nextstep_or_failure_rollback_exact=True));qs.append(q)
            profiles=[q.profile() for q in qs];probes=[[probe(q,p) for p in range(n)] for q in qs];rng=random.Random(17151601);base=[[],[]];dev=[[[] for p in range(n)] for q in qs];st=time.monotonic()
            for _ in range(256):
                deck=rng.sample(range(52),52);tape=rng.getrandbits(128)
                for i,q in enumerate(qs):
                    base[i].append(np.asarray(replay(native,game,profiles[i],deck=deck,seed=tape)['net_chips'])/2)
                    for p in range(n):dev[i][p].append(replay(native,game,probes[i][p],deck=deck,seed=tape)['net_chips'][p]/2)
            gains=[[interval([float(x-y[p]) for x,y in zip(dev[i][p],base[i])],-500,500,.001/200) for p in range(n)] for i in range(2)]
            result=dict(players=n,seed=seed,training=training,worlds=256,evaluation_seed=17151601,all_seat_minraise_gains=gains,paired_EV=[interval([float(a[p]-b[p]) for a,b in zip(base[1],base[0])],-500,500,.001/200) for p in range(n)],evaluation_seconds=time.monotonic()-st,full_native_BR_upper=None,formal_pass=0,source_sha256=sha(Path(__file__)),peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
            records.append(result);atomic(ROOT/'results.json',dict(records=records,family_confidence=.999,events=200));print(json.dumps(dict(n=n,seed=seed,training=training,eval_seconds=result['evaluation_seconds'])),flush=True)
if __name__=='__main__':
    import sys
    if '--nine' in sys.argv:
        ROOT=Path('docs/qa/stream-subgame-20261127/multiplayer9');run(players=(9,),finite_gate=False)
    else:run()
