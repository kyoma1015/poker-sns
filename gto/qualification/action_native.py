"""Independent native paired holdout; no training, BR upper or GTO admission."""
import argparse,gzip,json,math,random,time
from pathlib import Path
from gto.qualification.action_baseline import ActionBaselineSolver
from gto.qualification.build import load
from gto.qualification.native_mccfr import choose
from gto.qualification.public_response import Observation
from gto.native.training import NativeGame
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed


def native_value(s,native,game,deck,seed):
    state=native.NativeState(game);rng=random.Random(seed)
    for c in deck[:4]:state.apply_action(c)
    while not state.is_terminal():
        if state.is_chance_node():state.apply_action(deck[4+len(state.audit()['board'])]);continue
        a=state.audit();p=state.current_player()
        o=Observation(p,tuple(sorted(a['holes'][p])),tuple(a['board']),a['round'],a['price'],a['last_full'],
            tuple(a['remaining']),tuple(a['street']),tuple(a['live']),tuple(a['dead']),tuple(a['folded']),
            tuple(tuple(h) for h in a['history']),tuple(state.legal_actions()))
        state.apply_action(choose(o.actions,s.row(o,True),rng))
    net=[v/2 for v in state.returns()]
    assert sum(net)==0 and all(-50<=v<=50 for v in net)
    return net[0]


def interval(values,lo,hi,delta):
    n=len(values);mean=math.fsum(values)/n
    var=math.fsum((x-mean)**2 for x in values)/(n-1)
    radius=math.sqrt(2*var*math.log(2/delta)/n)+7*(hi-lo)*math.log(2/delta)/(3*(n-1))
    return dict(n=n,mean=mean,variance=var,radius=radius,interval=[max(lo,mean-radius),min(hi,mean+radius)])


def load_solver(rules,native,path):
    d=json.loads(gzip.decompress(Path(path).read_bytes()));i=d['identity']
    s=ActionBaselineSolver(rules,native,baseline=i['use_predictions'],targeted=i['targeted'],current=i['behavior']=='current')
    s.restore(d);return s


def evaluate(build,folder,seed=17118090,n=32768):
    folder=Path(folder);rules,native=load(build);game=NativeGame([100,100])
    names=['zero-standard','baseline-standard','zero-reach','baseline-reach']
    solvers=[load_solver(rules,native,folder/(name+'-checkpoint.json.gz')) for name in names]
    for name,index in (('zero-standard-current',0),('baseline-reach-current',3)):
        names.append(name);solvers.append(solvers[index].current_view())
        compressed(folder/(name+'-checkpoint.json.gz'),solvers[-1].snapshot())
    ids=[s.policy_digest for s in solvers];master=random.Random(seed);samples=[[] for _ in solvers];start=time.monotonic()
    for k in range(n):
        if time.monotonic()-start>90:
            atomic(folder/'native-paired.json',dict(status='INCOMPLETE_TIME_LIMIT',n=k,policy_digests=ids));return
        deck=master.sample(range(52),9);tape=master.getrandbits(128)
        for s,v in zip(solvers,samples):v.append(native_value(s,native,game,deck,tape))
        if (k+1)%4096==0:atomic(folder/'native-progress.json',dict(completed_worlds=k+1,fixed_target=n,elapsed_seconds=time.monotonic()-start))
    assert ids==[s.policy_digest for s in solvers]
    delta=.001/11;profiles=[]
    for name,s,v in zip(names,solvers,samples):
        ev=interval(v,-50,50,delta);gain=[-.5-ev['interval'][1],-.5-ev['interval'][0]]
        profiles.append(dict(name=name,policy_digest=s.policy_digest,ev_bb=ev,fold_gain_interval_bb=gain,
            fold_weakness_resolved=gain[1]<=0,full_br_gain_lower_bb=max(0,gain[0]),nashconv_lower_bb=max(0,gain[0]),
            full_br_upper_bb=None,nashconv_bb=None,nashconv_upper_bb=None))
    comparisons=[]
    for a,b in ((1,0),(2,0),(3,0),(5,4),(4,0)):
        change=interval([x-y for x,y in zip(samples[a],samples[b])],-100,100,delta)
        comparisons.append(dict(candidate=names[a],control=names[b],paired_ev_change_bb=change,
            stage_gate=(change['interval'][0]>.1 and (a,b)!=(4,0)
                and profiles[a]['fold_gain_interval_bb'][1]<profiles[b]['fold_gain_interval_bb'][1]-.1)))
    atomic(folder/'native-paired.json',dict(status='COMPLETE_UNVERIFIED',seed=seed,profiles=profiles,comparisons=comparisons,
        confidence_family=.999,events=11,method='iid bounded empirical Bernstein; paired CRN differences',
        completed_worlds=n,native_paths=n*len(solvers),elapsed_seconds=time.monotonic()-start,
        ordinary_registry_admission=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--folder',required=True);a=p.parse_args();evaluate(a.build,a.folder)
