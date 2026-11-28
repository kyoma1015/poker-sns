"""Compute/IO-separated coverage study and fresh native holdout. No admission."""
import argparse,gzip,json,math,random,time
from pathlib import Path
from collections import Counter
from gto.qualification.action_baseline import ActionBaselineSolver
from gto.qualification.action_native import native_value,interval,load_solver
from gto.qualification.first_external import FirstExternalSolver
from gto.qualification.coverage_solver import CoverageSolver
from gto.qualification.root_cause import SOURCE,root_coverage
from gto.qualification.build import load
from gto.qualification.evaluate import atomic
from gto.qualification.fast_checkpoint import save as compressed
from gto.native.training import NativeGame


def load_model(rules,native,path):
    d=json.loads(gzip.decompress(Path(path).read_bytes()));i=d['identity']
    if 'coverage_source_sha256' in i:
        s=CoverageSolver(rules,native,external=i['first_external'],family=i['untrained_prior']=='equal-legal-action-family',adaptive=i['chance'].startswith('adaptive'))
    else:s=ActionBaselineSolver(rules,native,baseline=True,targeted=True)
    s.id={**s.id,'warm_source_digest':i['warm_source_digest']};s.restore(d);return s


def train(build,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rules,native=load(build);base=load_solver(rules,native,SOURCE);source_digest=base.policy_digest
    arms=[]
    for name,external,family,adaptive in [('rawOS',None,False,False),('batchOS',False,False,False),('adaptiveExt',True,False,True),('adaptiveExtFamily',True,True,True)]:
        s=ActionBaselineSolver(rules,native,baseline=True,targeted=True) if external is None else CoverageSolver(rules,native,external=external,family=family,adaptive=adaptive)
        FirstExternalSolver.adopt(s,base,17118101);path=out/(name+'-checkpoint.json.gz');learn=io=0.;worlds=since=0;start=time.monotonic()
        def save():
            t=time.monotonic();compressed(path,s.snapshot());return time.monotonic()-t
        io+=save()
        while learn<12 and time.monotonic()-start<120:
            t=time.monotonic()
            try:
                if name=='batchOS':n=s.batch()
                else:s.step();n=1
            except TimeoutError:
                atomic(out/(name+'-incomplete.json'),dict(status='INCOMPLETE_STOP',last_complete_checkpoint=str(path)));raise
            learn+=time.monotonic()-t;worlds+=n;since+=n
            if since>=169:io+=save();since=0
        io+=save();rc=sum(s.counts.values());sc=sum(s.average_counts.values())
        arms.append(dict(name=name,learning_compute_seconds=learn,checkpoint_seconds=io,wall_seconds=time.monotonic()-start,world_pairs=worlds,
            root_classes=sum(h['has_S'] for h in root_coverage(s)),root_combo_mass=sum(h['mass'] for h in root_coverage(s) if h['has_S']),
            R_updates=rc,R_distinct=len(s.counts),R_revisit_rate=1-len(s.counts)/rc if rc else None,
            S_updates=sc,S_distinct=len(s.average_counts),S_revisit_rate=1-len(s.average_counts)/sc if sc else None,
            chance_weight_max=getattr(s,'chance_weight_max',None),policy_digest=s.policy_digest,infosets=len(s.rows)))
        atomic(out/'training.json',dict(status='COMPLETE' if len(arms)==4 else 'RUNNING',source_policy_digest=source_digest,seed=17118101,arms=arms))
        if sum(p.stat().st_size for p in out.glob('*'))>100*1024*1024:raise RuntimeError('disk cap')
    prior=CoverageSolver(rules,native,family=True);prior.adopt(base,17118101);compressed(out/'priorFamily-checkpoint.json.gz',prior.snapshot())

class Tracked:
    def __init__(self,s):self.s=s;self.path=[]
    def row(self,o,average=False):
        if hasattr(self.s,'observation'):
            ob=self.s.observation(o);r=self.s.rows.get(ob.key);self.path.append(bool(r and math.fsum(r['S'])>0))
        return self.s.row(o,True)


def evaluate(build,out,b_artifact=None):
    out=Path(out);rules,native=load(build);base=load_solver(rules,native,SOURCE)
    names=['source','priorFamily','rawOS','batchOS','adaptiveExt','adaptiveExtFamily']
    solvers=[base]+[load_model(rules,native,out/(n+'-checkpoint.json.gz')) for n in names[1:]]
    if b_artifact:
        from gto.qualification.preflop_release_solver import load_policy
        names.append('preflopAbstract');solvers.append(load_policy(build,b_artifact))
    events=len(solvers)+(len(solvers)-1);delta=.001/events
    tracked=[Tracked(s) for s in solvers];values=[[] for s in solvers];missing=Counter();rng=random.Random(17118102)
    n=16384;start=time.monotonic();game=NativeGame([100,100]);ids=[s.policy_digest for s in solvers]
    for k in range(n):
        if time.monotonic()-start>90:raise RuntimeError('native holdout90sec cap')
        deck=rng.sample(range(52),9);tape=rng.getrandbits(128)
        for j,s in enumerate(tracked):
            s.path=[];values[j].append(native_value(s,native,game,deck,tape))
            if s.path:missing[names[j]]+=not all(s.path)
        if (k+1)%2048==0:atomic(out/'native-progress.json',dict(worlds=k+1,target=n))
    profiles=[]
    for name,s,v in zip(names,solvers,values):
        ev=interval(v,-50,50,delta);fold=[-.5-ev['interval'][1],-.5-ev['interval'][0]]
        profiles.append(dict(name=name,policy_digest=s.policy_digest,ev_bb=ev,fold_gain_interval_bb=fold,
            untrained_path_rate=missing[name]/n if hasattr(s,'observation') else None,
            coverage_scope='native positive-S paths' if hasattr(s,'observation') else 'ABSTRACT_DOMAIN_NOT_NATIVE_ACCUMULATOR',
            full_br_gain_lower_bb=max(0,fold[0]),nashconv_lower_bb=max(0,fold[0]),full_br_upper_bb=None,nashconv_bb=None,nashconv_upper_bb=None))
    comparisons=[]
    for j in range(1,len(solvers)):
        change=interval([x-y for x,y in zip(values[j],values[0])],-100,100,delta)
        gate=change['interval'][0]>.1 and profiles[j]['fold_gain_interval_bb'][1]<profiles[0]['fold_gain_interval_bb'][1]-.1
        comparisons.append(dict(candidate=names[j],control='source',paired_ev_change_bb=change,stage_gate=gate))
    assert ids==[s.policy_digest for s in solvers]
    atomic(out/'native.json',dict(status='COMPLETE_UNVERIFIED',seed=17118102,n=n,native_paths=n*len(solvers),seconds=time.monotonic()-start,
        confidence_family=.999,events=events,profiles=profiles,comparisons=comparisons,
        ordinary_registry_admission=False,formal_acceptance_complete=0,verified_strategy_count=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--out',required=True);p.add_argument('--evaluate',action='store_true');p.add_argument('--b-artifact');a=p.parse_args()
    if a.evaluate:evaluate(a.build,a.out,a.b_artifact)
    else:train(a.build,a.out)
