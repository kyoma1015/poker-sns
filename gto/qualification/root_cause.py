"""Bounded causal diagnostics; never changes the protected native checkpoint."""
import argparse,gzip,json,math,random,time
from collections import Counter,defaultdict
from pathlib import Path
from gto.qualification.blind_oracle import FiniteCFR,assessment,policy
from gto.qualification.action_native import load_solver,native_value,interval
from gto.qualification.build import load
from gto.qualification.evaluate import atomic
from gto.qualification.native_mccfr import betting,digest
from gto.qualification.public_response import observe
from gto.native.training import NativeGame
from gto.abstract.model import classes,CLASSES
from gto.qualification.variance_study import compressed

SOURCE=Path('docs/qa/action-baseline-20261118/baseline-reach-checkpoint.json.gz')

class Ablation:
    def __init__(self,base,learned_seats):
        self.base=base;self.learned_seats=learned_seats;self.path=[]
        self.digest=digest(dict(base=base.policy_digest,learned_seats=learned_seats,
            intervention='uniform only instead of learned rows; unseen prior unchanged'))
    def row(self,o,average=False):
        o=self.base.observation(o);r=self.base.rows.get(o.key)
        supported=bool(r and math.fsum(r['S'])>0)
        self.path.append((o.actor,o.round,supported,len(o.actions)))
        if o.actor in self.learned_seats:return self.base.row(o,True)
        return [1/len(o.actions)]*len(o.actions)

def finite_study(out):
    rows=[];initial=assessment({})
    for seed in (17118031,17118032,17118033):
        for method in ('outcome','external','exact'):
            s=FiniteCFR(method,seed);start=time.monotonic()
            while s.iteration<100000 and time.monotonic()-start<1.:s.step()
            elapsed=time.monotonic()-start
            result=assessment(policy(s.rows,True))
            name=f'finite-{method}-{seed}-checkpoint.json.gz';compressed(out/name,s.snapshot())
            rows.append(dict(method=method,seed=seed,iterations=s.iteration,seconds=elapsed,**result))
            atomic(out/'finite-comparison.json',dict(initial=initial,profiles=rows,status='COMPLETE' if len(rows)==9 else 'RUNNING',scope=initial['scope']))

def root_coverage(s):
    b=betting(s.rules);hist=[]
    for label,group in zip(CLASSES,classes()):
        o=s.observation(observe(b,group[0],[]));r=s.rows.get(o.key)
        count=s.counts.get(o.key,0);ac=s.average_counts.get(o.key,0)
        hist.append(dict(hand=label,mass=len(group)/1326,has_R=bool(r and any(r['R'])),
            has_S=bool(r and sum(r['S'])>0),stage_R_updates=count,stage_S_updates=ac,
            stage_count_note='new stage only; warm ancestor counts reset by original experiment'))
    return hist

def native_study(out,rules,native,s):
    profiles=[Ablation(s,[0,1]),Ablation(s,[0]),Ablation(s,[1]),Ablation(s,[])]
    names=['both-learned','SB-learned','BB-learned','both-uniform'];samples=[[] for _ in profiles]
    events=Counter();first=defaultdict(list);decisions=Counter();master=random.Random(17118034)
    start=time.monotonic();n=8192;before=s.policy_digest;game=NativeGame([100,100])
    for k in range(n):
        if time.monotonic()-start>60:raise RuntimeError('native diagnostic time cap; no completed receipt')
        deck=master.sample(range(52),9);tape=master.getrandbits(128)
        for i,p in enumerate(profiles):
            p.path=[];u=native_value(p,native,game,deck,tape);samples[i].append(u)
            if i==0:
                missing=[x for x in p.path if not x[2]]
                first[str(missing[0][:2]) if missing else 'all-positive-S'].append(u)
                for seat in (0,1):events[f'seat{seat}_any_untrained']+=any(x[0]==seat for x in missing)
                events['any_untrained']+=bool(missing)
                for seat,street,support,na in p.path:decisions[f'{seat}:{street}:{"positive_S" if support else "uniform_prior"}']+=1
        if (k+1)%2048==0:atomic(out/'native-progress.json',dict(worlds=k+1,target=n))
    delta=.001/8;results=[]
    for name,p,v in zip(names,profiles,samples):
        ev=interval(v,-50,50,delta);fold=[-.5-ev['interval'][1],-.5-ev['interval'][0]]
        results.append(dict(name=name,policy_digest=p.digest,source_policy_digest=before,learned_seats=p.learned_seats,
            ev_bb=ev,sb_fold_gain_interval_bb=fold,full_br_gain_lower_bb=max(0,fold[0]),
            nashconv_lower_bb=max(0,fold[0]),full_br_upper_bb=None,nashconv_bb=None,nashconv_upper_bb=None))
    contrasts=[]
    for a,b in ((0,3),(0,1),(0,2),(1,3)):
        contrasts.append(dict(candidate=names[a],control=names[b],paired_ev_change_bb=interval([x-y for x,y in zip(samples[a],samples[b])],-100,100,delta)))
    assert before==s.policy_digest
    atomic(out/'native-attribution.json',dict(status='COMPLETE_DIAGNOSTIC_NOT_A_CANDIDATE',seed=17118034,n=n,
        elapsed_seconds=time.monotonic()-start,profiles=results,contrasts=contrasts,
        event_counts=dict(events),decision_counts=dict(decisions),
        first_untrained_partition={key:dict(n=len(v),conditional_mean_bb=sum(v)/len(v),root_EV_contribution_bb=sum(v)/n) for key,v in first.items()},
        root_coverage=root_coverage(s),confidence_family=.999,events=8,
        full_native_paths=n*4,expanded_training=False,ordinary_registry_admission=False))

def tails(out,s):
    rng=random.Random(17118035);start=time.monotonic();maxd=[];maxw=[];absolute=[]
    before=s.snapshot();reports=[]
    for i in range(1024):
        if time.monotonic()-start>15:raise RuntimeError('sampling-tail time cap')
        g,a=s.collect(i%2,rng.sample(range(52),9),random.Random(rng.getrandbits(128)))
        maxd.append(max((abs(x) for _,_,d,_ in g for x in d),default=0.))
        maxw.append(max((w for _,_,w in a),default=0.))
    # collect changes only diagnostic reach counters, not R/S/masterRNG or policy.
    assert before['rows']==s.rows and before['rng']==s.snapshot()['rng']
    def summary(xs):
        xs=sorted(xs);return {str(q):xs[min(len(xs)-1,int(q*(len(xs)-1)))] for q in (.5,.9,.99,1.)}
    atomic(out/'sampling-tails.json',dict(paths=1024,seed=17118035,seconds=time.monotonic()-start,
        maximum_abs_regret_increment_per_path=summary(maxd),maximum_average_weight_per_path=summary(maxw),
        note='mixed infosets: NOT a global effective sample size, regret bound or bias test'))

def run(build,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);finite_study(out)
    rules,native=load(build);s=load_solver(rules,native,SOURCE)
    native_study(out,rules,native,s);tails(out,s)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.build,a.out)
