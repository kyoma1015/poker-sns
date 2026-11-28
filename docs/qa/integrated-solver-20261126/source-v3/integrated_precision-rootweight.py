"""Same-policy preflop Bayes ranges and optimally stratified jam action EV.
Numerical proposal precision only: NOT formal GTO/BR/registry admission.
Reuses sparse_study.jam_certificate's conditional fold/call decomposition.
"""
import argparse,itertools,json,math,random,time
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification.native_mccfr import betting
from gto.qualification.public_response import observe
from gto.qualification.policy import act,hand,sha
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed


def allocation(weights,halfwidth=.05,delta=1e-7):
    a=np.asarray(weights,dtype=float)
    if np.any(a<0) or not np.all(np.isfinite(a)) or not 0<delta<1 or halfwidth<=0:raise ValueError('EV allocation')
    scale=10000*math.log(2/delta)*float(a.sum())/(2*halfwidth**2)
    n=np.where(a>0,np.maximum(1,np.ceil(scale*a)),0).astype(np.int64)
    radius=100*math.sqrt(math.log(2/delta)*float(np.sum(np.divide(a*a,n,out=np.zeros_like(a),where=n>0)))/2)
    return n,radius


def tables(q,rules,prefix):
    b=betting(rules)
    for action in prefix:act(b,action)
    hero=b.actor
    if b.round!=0 or hero not in (0,1) or 102 not in observe(b,(48,49),[]).actions:raise ValueError('preflop jam context')
    likelihood=[];calls=[]
    for group in model.classes():
        def one(own):
            state=betting(rules);weight=1.
            for action in prefix:
                if state.actor!=hero:
                    o=observe(state,own,[]);weight*=q.row(o,True)[o.actions.index(action)]
                act(state,action)
            act(state,102);o=observe(state,own,[])
            if set(o.actions)!={0,1}:raise ValueError('only fold/call after HU jam')
            return weight,q.row(o,True)[o.actions.index(1)]
        x=one(group[0]);y=one(group[-1]);np.testing.assert_allclose(x,y,atol=1e-14)
        likelihood.append(x[0]);calls.append(x[1])
    return b,hero,np.array(likelihood),np.array(calls)


def certificate(q,rules,module,folder,seed,context_seconds=30):
    folder=Path(folder);frozen=q.policy_digest;output=folder/'169-context-EV.json'
    if output.exists():raise FileExistsError('preserve EV certificate')
    contexts=[('rfi',[]),('vs_open3p5',[9]),('vs_3bet10p5',[8,23])]
    rng=random.Random(17137101+seed);classes={tuple(sorted(h)):i for i,g in enumerate(model.classes()) for h in g};allrows={};frequencies={};total=0
    # Fixed family allocation over both seeds / all169 / all3 contexts /2actions.
    delta=.0005/(2*169*3*2)
    for name,prefix in contexts:
        b,hero,L,C=tables(q,rules,prefix);fold=-b.live[hero]/2;profit=b.live[1-hero]/2;rows={};freq={};start=time.monotonic();doneboards=0
        for label,group in zip(model.CLASSES,model.classes()):
            own=list(group[0]);o=observe(b,own,[]);freq[label]=dict(actions=o.actions,frequency=q.row(o,True))
            pairs=list(itertools.combinations([c for c in range(52) if c not in own],2));ids=np.array([classes[x] for x in pairs]);z=float(L[ids].sum())
            if z<=0:rows[label]=dict(status='UNKNOWN_ZERO_RANGE',fold=None,jam=None);continue
            weights=L[ids]/z;mass=weights*C[ids];counts,radius=allocation(mass,.05,delta)
            state=betting(rules);ownreach=1.
            for action in prefix:
                if state.actor==hero:
                    past=observe(state,own,[]);ownreach*=q.row(past,True)[past.actions.index(action)]
                act(state,action)
            baseweight=len(group)/1326*ownreach*z/1225
            fp=q.row(o,True);fw=baseweight*fp[o.actions.index(0)]
            rows[label]=dict(fold=dict(action=0,EV=fold,interval=[fold,fold],exact=True,root_weight=fw,root_contribution=fw*fold),jam=None,opponent_history_mass=z/1225,hero_history_reach=ownreach,counterfactual_decision_EV=True)
            # This coverage decision uses weights/time only, never sampled outcomes.
            boards=int(counts.sum());elapsed=time.monotonic()-start
            speed=doneboards/elapsed if elapsed>0 and doneboards else 1500000.
            if boards>12000000 or elapsed+boards/max(speed,1)*1.2>context_seconds:continue
            value=profit
            for other,a,n in zip(pairs,mass,counts):
                n=int(n)
                if not n:continue
                remain=n;eq=0.
                while remain:
                    k=min(100000,remain);eq+=k*module.equity_prefix(own+list(other),[],k,rng.getrandbits(64));remain-=k
                value+=float(a)*(50*(2*eq/n-1)-profit)
            doneboards+=boards;total+=1
            jw=baseweight*fp[o.actions.index(102)]
            rows[label]['jam']=dict(action=102,EV=value,root_weight=jw,root_contribution_interval=[jw*max(-50,value-radius),jw*min(50,value+radius)],interval=[max(-50,value-radius),min(50,value+radius)],halfwidth=radius,boards=boards,opponent_pairs=1225,proposal_precision_pass=radius<=.05+1e-12)
        allrows[name]=dict(prefix=prefix,rows=rows,seconds=time.monotonic()-start,boards=doneboards)
        frequencies[name]=freq
        atomic(output,dict(policy_digest=frozen,contexts=allrows,computed_jam_cells=total,proposal_precision_pass_cells=sum(r['jam'] is not None and r['jam']['proposal_precision_pass'] for c in allrows.values() for r in c['rows'].values()),formal_precision_cells=0,formal_acceptance=0,confidence_family=.9995,allocated_delta=.0005,source_sha256=sha(Path(__file__)),method='exact card removal and same-policy opponent prehistory likelihood; integrate fold/call; independent conditionalboard strata, n_i proportional posterior_i*call_i chosen before outcomes; weighted Hoeffding',full_native_BR_upper=None,ordinary_registry_admission=False))
        print(json.dumps(dict(seed=seed,context=name,complete_jams=sum(r['jam'] is not None for r in rows.values()),boards=doneboards,seconds=time.monotonic()-start)),flush=True)
    compressed(folder/'169-frequencies-final.json.gz',dict(policy_digest=frozen,contexts=frequencies,formal_pass=False))
    assert frozen==q.policy_digest

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);x=a.parse_args()
    from gto.qualification import integrated_study as study
    if x.seed==17120102:
        from gto.qualification.integrated_extension import make,ROOT
        q,m=make(x.seed,True);folder=ROOT/str(x.seed)
    else:
        folder=study.ROOT/'root-integrated'/str(x.seed);q,m,_,_=study.current(x.seed,study.ROOT/'root-integrated',True)
    rules=study.load('/tmp/native-qualification')[0];certificate(q,rules,m,folder,x.seed)
