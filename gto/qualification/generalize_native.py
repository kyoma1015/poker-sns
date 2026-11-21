"""One-shot disjoint native gate after the chance-board policy has been frozen."""
import argparse,copy,gzip,json,random,time,resource
from pathlib import Path
from gto.abstract import model
from gto.qualification import fullstreet_solver as f,fullstreet_evaluate as oldeval
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.native_mccfr import betting
from gto.qualification.public_response import observe
from gto.qualification.policy import sha,act
from gto.qualification.action_native import native_value,interval
from gto.qualification.coupled_evaluate import Extra
from gto.qualification.range_study import GeneralNuts
from gto.qualification.variance_study import compressed
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame
OLD=Path('docs/qa/fullstreet-joint-20261120')

def run(build,folder,seed=17122201):
    folder=Path(folder);lib=f.load('/tmp/fullstreet-build/fullstreet.so');base=load_policy(build,f.old.ARTIFACT);rank=model.load('/tmp/range-continuation-build/range.so')
    parents=[oldeval.load_parent(build,rank,s) for s in (17119201,17119202)];controls=[f.read_policy(OLD/str(s),lib,base,'policy-selected') for s in (17120101,17120102)]
    for q in controls:q.average_mass=q.average_mass>0 # exact positive-support diagnostic; policy unchanged
    qs=[f.read_policy(folder/str(s),lib,base,'policy-best') for s in (17120101,17120102)]
    profiles=[base]+parents+controls+qs;names=['oldB','oldjoint1','oldjoint2','old16_1','old16_2','new1','new2'];kinds=['open3p5','threebet10p5','river_jam','fold','open2p5','threebet9','river_nuts'];probes=[]
    for q in qs:probes += [Extra(q,k) if k!='river_nuts' else GeneralNuts(q) for k in kinds]
    for seed,q in zip((17120101,17120102),qs):
        m=json.loads((folder/str(seed)/'result.json').read_text())['new_final'];rows={}
        for name,prefix in [('rfi',[]),('vs_open',[8]),('vs_3bet',[8,22])]:
            b=betting(base.rules)
            for a in prefix:act(b,a)
            k=q.known[(0,tuple(tuple(h[:3]) for h in b.history))];na=len(q.nodes[k]['children']);rows[name]={}
            for c,(label,group) in enumerate(zip(model.CLASSES,model.classes())):
                o=observe(b,group[0],[]);at=q.bases[k]+c*na;rows[name][label]=dict(native_actions=o.actions,frequencies=q._row(o,False),average_mass=float(q.average_mass[at:at+na].sum()),final_conditional_MODEL_action_EV_bb=m['action_EV_bb'][str(k)][c*na:(c+1)*na],fullnative_EV_interval=None)
        compressed(folder/str(seed)/'169-frequencies-EV.json.gz',dict(policy_digest=q.policy_digest,rows=rows,ordinary_registry_admission=False))
    for q in qs:q.average_mass=q.average_mass>0
    rng=random.Random(seed);ws=[(rng.sample(range(52),9),rng.getrandbits(128)) for _ in range(8192)];values=[[] for _ in profiles+probes];bits={i:{r:[] for r in ('any',0,1,2,3)} for i in (3,4,5,6)};counts={i:{r:dict(queries=0,unlearned=0,offtree=0) for r in range(4)} for i in bits};start=time.monotonic();game=NativeGame([100,100]);identity=dict(seed=seed,n=8192,worlds=ws,source_sha256=sha(Path(__file__)),native_binary_sha256=sha(Path(base.native.__file__)),policy_digests=[q.policy_digest for q in profiles],confidence_family=.999,events=40)
    for i,(deck,tape) in enumerate(ws):
        if time.monotonic()-start>90:atomic(folder/'native.json',dict(status='INCOMPLETE',completed=i));return
        for j,(q,v) in enumerate(zip(profiles+probes,values)):
            before=copy.deepcopy(q.stats) if j in bits else None;v.append(native_value(q,base.native,game,deck,tape))
            if before is not None:
                delta={r:{k:q.stats[r][k]-before[r][k] for k in before[r]} for r in range(4)}
                for r in range(4):
                    bits[j][r].append(int(delta[r]['unlearned']>0))
                    for k in delta[r]:counts[j][r][k]+=delta[r][k]
                bits[j]['any'].append(int(any(delta[r]['unlearned'] for r in range(4))))
        if (i+1)%512==0:compressed(folder/'native-checkpoint.json.gz',dict(identity=identity,completed=i+1,values=values,bits={str(k):{str(r):v for r,v in b.items()} for k,b in bits.items()},counts=counts));print(json.dumps(dict(worlds=i+1,seconds=time.monotonic()-start)),flush=True)
    delta=.001/40;ev=[dict(name=n,digest=q.policy_digest,SB_EV_bb=interval(v,-50,50,delta)) for n,q,v in zip(names,profiles,values)];comp=[];dev=[];coverage=[]
    for s in (0,1):
        newi=5+s;oldi=3+s
        for ci in (0,1+s,oldi):comp.append(dict(candidate=names[newi],control=names[ci],paired_EV_difference_bb=interval([a-b for a,b in zip(values[newi],values[ci])],-100,100,delta)))
        for k,v in zip(kinds,values[7+s*7:14+s*7]):
            sign=1 if k in ('open3p5','open2p5','fold') else -1;dev.append(dict(candidate=names[newi],kind=k,gain_bb=interval([sign*(a-b) for a,b in zip(v,values[newi])],-100,100,delta)))
        coverage.append(dict(seed=(17120101,17120102)[s],old=counts[oldi],new=counts[newi],old_unlearned_world_rate=sum(bits[oldi]['any'])/8192,new_unlearned_world_rate=sum(bits[newi]['any'])/8192,paired_unlearned_world_difference={str(r):interval([a-b for a,b in zip(bits[newi][r],bits[oldi][r])],-1,1,delta) for r in ('any',2,3)}))
    atomic(folder/'native.json',dict(status='COMPLETE_UNVERIFIED',identity=identity,profiles=ev,comparisons=comp,deviations=dev,coverage=coverage,seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,positive_support_only_diagnostic=True,full_native_BR_upper=None,full_native_NashConv=None,full169_action_precision=None,abstraction_error=None,omitted_size_error=None,ordinary_registry_admission=False,formal_acceptance=0,verified_RFI=0,verified_3bet=0))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--folder',required=True);p.add_argument('--seed',type=int,default=17122201);a=p.parse_args();run(a.build,a.folder,a.seed)
