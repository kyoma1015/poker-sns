"""Matched bounded HU50 first-external gate. Never admits strategies."""
import argparse,gzip,json,random,time
from pathlib import Path
from gto.qualification.action_baseline import ActionBaselineSolver
from gto.qualification.action_native import interval,native_value,load_solver
from gto.qualification.first_external import FirstExternalSolver
from gto.qualification.build import load
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed
from gto.qualification.root_cause import SOURCE
from gto.native.training import NativeGame

def load_experiment(rules,native,path):
    d=json.loads(gzip.decompress(Path(path).read_bytes()));i=d['identity']
    s=FirstExternalSolver(rules,native) if 'first_external_source_sha256' in i else ActionBaselineSolver(rules,native,baseline=True,targeted=True)
    s.id={**s.id,'warm_source_digest':i['warm_source_digest']};s.restore(d);return s

def run(build,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rules,native=load(build);base=load_solver(rules,native,SOURCE)
    before=base.snapshot();solvers=[];arms=[]
    for seed in (17118041,17118042,17118043):
        for method in ('outcome','first-external'):
            s=FirstExternalSolver(rules,native) if method=='first-external' else ActionBaselineSolver(rules,native,baseline=True,targeted=True)
            FirstExternalSolver.adopt(s,base,seed);name=f'{method}-{seed}';path=out/(name+'-checkpoint.json.gz')
            start=time.monotonic();i=0
            while i<1024 and time.monotonic()-start<3.:
                s.step();i+=1;compressed(path,s.snapshot())
                if sum(p.stat().st_size for p in out.glob('*'))>20*1024*1024:raise RuntimeError('storage cap')
            elapsed=time.monotonic()-start
            solvers.append(s);arms.append(dict(name=name,method=method,seed=seed,pairs=i,seconds=elapsed,
                policy_digest=s.policy_digest,infosets=len(s.rows)))
            atomic(out/'first-external-training.json',dict(arms=arms,status='COMPLETE' if len(arms)==6 else 'RUNNING'))
    assert before==base.snapshot()
    solvers.append(base);names=[a['name'] for a in arms]+['frozen-source'];samples=[[] for s in solvers]
    master=random.Random(17118038);start=time.monotonic();game=NativeGame([100,100]);n=8192
    for k in range(n):
        if time.monotonic()-start>60:raise RuntimeError('native holdout cap; incomplete not accepted')
        deck=master.sample(range(52),9);tape=master.getrandbits(128)
        for s,v in zip(solvers,samples):v.append(native_value(s,native,game,deck,tape))
        if (k+1)%2048==0:atomic(out/'first-external-progress.json',dict(worlds=k+1,target=n))
    delta=.001/13;profiles=[]
    for name,s,v in zip(names,solvers,samples):
        ev=interval(v,-50,50,delta);fold=[-.5-ev['interval'][1],-.5-ev['interval'][0]]
        profiles.append(dict(name=name,policy_digest=s.policy_digest,ev_bb=ev,fold_gain_interval_bb=fold,
            full_br_gain_lower_bb=max(0,fold[0]),nashconv_lower_bb=max(0,fold[0]),
            full_br_upper_bb=None,nashconv_bb=None,nashconv_upper_bb=None))
    comparisons=[]
    for a,b in ((1,0),(3,2),(5,4),(1,6),(3,6),(5,6)):
        change=interval([x-y for x,y in zip(samples[a],samples[b])],-100,100,delta)
        comparisons.append(dict(candidate=names[a],control=names[b],paired_ev_change_bb=change,
            gate=(change['interval'][0]>.1 and profiles[a]['fold_gain_interval_bb'][1]<profiles[b]['fold_gain_interval_bb'][1]-.1)))
    passed=all(c['gate'] for c in comparisons)
    atomic(out/'first-external-native.json',dict(status='NATIVE_STAGE_GATE_PASS_NOT_QUALIFIED' if passed else 'STOP_NO_SIGNIFICANT_NATIVE_IMPROVEMENT',
        n=n,seed=17118038,native_paths=n*len(solvers),seconds=time.monotonic()-start,
        confidence_family=.999,events=13,profiles=profiles,comparisons=comparisons,
        stage_gate=passed,expanded_training=False,ordinary_registry_admission=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.build,a.out)
