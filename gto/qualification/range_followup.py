"""Fresh independent probes and fixed-n EVs for one frozen continuation policy."""
import argparse,json,math,random,time
from pathlib import Path
from gto.qualification.range_continuation import load
from gto.qualification.action_native import native_value,interval
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame
ARTIFACT='docs/qa/release-route-20261118/strategy.json.gz'

class Probe:
    def __init__(self,base,kind):self.base,self.kind=base,kind
    def row(self,o,average=False):
        action=None
        if self.kind=='river_jam' and o.actor==1 and o.round==3 and o.street[1]==o.price and any(a>1 for a in o.actions):action=max(o.actions)
        if self.kind=='flop_half' and o.actor==1 and o.round==1 and not any(h[0]==1 for h in o.history):
            raises=[a for a in o.actions if a>1]
            if raises:action=min(raises,key=lambda a:abs(a-2-max(2,sum(o.live)//2)))
        if self.kind=='open3p5' and o.actor==0 and not o.history and 9 in o.actions:action=9
        if self.kind=='threebet10p5' and o.actor==1 and len(o.history)==1 and o.history[0][:3]==(0,0,6) and 23 in o.actions:action=23
        return [float(a==action) for a in o.actions] if action is not None else self.base.row(o,True)


def probes(build,library,out):
    p=load(build,ARTIFACT,library);rng=random.Random(17118205);game=NativeGame([100,100]);kinds=['river_jam','flop_half','open3p5','threebet10p5'];ps=[Probe(p,k) for k in kinds]
    old=[];base=[];values=[[] for _ in ps];start=time.monotonic();n=256
    for i in range(n):
        if time.monotonic()-start>60:
            atomic(out,dict(status='INCOMPLETE_TIME_LIMIT',worlds=i,policy_digest=p.policy_digest));return
        deck=rng.sample(range(52),9);tape=rng.getrandbits(128)
        old.append(native_value(p.base,p.native,game,deck,tape));base.append(native_value(p,p.native,game,deck,tape))
        for v,q in zip(values,ps):v.append(native_value(q,p.native,game,deck,tape))
        if (i+1)%32==0:atomic(str(out)+'.progress.json',dict(worlds=i+1,target=n,seconds=time.monotonic()-start,policy_digest=p.policy_digest))
    delta=.001/5;results=[]
    for kind,v in zip(kinds,values):
        player=0 if kind=='open3p5' else 1;g=[(b-a) if player==0 else (a-b) for a,b in zip(base,v)]
        result=interval(g,-100,100,delta);results.append(dict(deviation=kind,player=player,gain_bb=result,independent_BR_gain_lower_bb=max(0,result['interval'][0])))
    atomic(out,dict(status='COMPLETE_UNVERIFIED',n=n,seed=17118205,native_paths=n*6,seconds=time.monotonic()-start,policy_digest=p.policy_digest,
        old_EV=sum(old)/n,new_EV=sum(base)/n,EV_change_bb=interval([a-b for a,b in zip(base,old)],-100,100,delta),
        confidence_family=.999,events=5,deviations=results,
        nashconv_lower_bb=max(r['independent_BR_gain_lower_bb'] for r in results),full_BR_upper_bb=None,nashconv_bb=None,nashconv_upper_bb=None,
        ordinary_registry_admission=False,verified_strategy_count=0))


def ev(build,library,out,resume=None):
    p=load(build,ARTIFACT,library);rng=random.Random(17118204);old=[];new=[];prior=0.;start=time.monotonic();game=NativeGame([100,100]);n=2048
    if resume:
        s=json.loads(Path(resume).read_text())
        if s['policy_digest']!=p.policy_digest:raise ValueError('resume policy mismatch')
        def tuples(x):return tuple(tuples(v) for v in x) if isinstance(x,list) else x
        rng.setstate(tuples(s['rng']));old=s['old'];new=s['new'];prior=s['seconds']
        if len(old)!=len(new):raise ValueError('sample checkpoint mismatch')
    for i in range(len(new),n):
        if prior+time.monotonic()-start>120:
            atomic(out,dict(status='INCOMPLETE_TIME_LIMIT',n=i,policy_digest=p.policy_digest));return
        deck=rng.sample(range(52),9);tape=rng.getrandbits(128)
        old.append(native_value(p.base,p.native,game,deck,tape));new.append(native_value(p,p.native,game,deck,tape))
        if (i+1)%64==0:atomic(str(out)+'.progress.json',dict(worlds=i+1,target=n,seconds=prior+time.monotonic()-start,rng=rng.getstate(),old=old,new=new,policy_digest=p.policy_digest))
    delta=.001/3
    atomic(out,dict(status='COMPLETE_UNVERIFIED',n=n,seed=17118204,native_paths=2*n,seconds=prior+time.monotonic()-start,policy_digest=p.policy_digest,
        old_EV_bb=interval(old,-50,50,delta),new_EV_bb=interval(new,-50,50,delta),EV_change_bb=interval([a-b for a,b in zip(new,old)],-100,100,delta),
        confidence_family=.999,events=3,full_BR_upper_bb=None,nashconv_bb=None,nashconv_upper_bb=None,ordinary_registry_admission=False,verified_strategy_count=0))

if __name__=='__main__':
    q=argparse.ArgumentParser();q.add_argument('--build',required=True);q.add_argument('--library',required=True);q.add_argument('--output',required=True);q.add_argument('--ev',action='store_true');q.add_argument('--resume');a=q.parse_args()
    if a.ev:ev(a.build,a.library,a.output,a.resume)
    else:probes(a.build,a.library,a.output)
