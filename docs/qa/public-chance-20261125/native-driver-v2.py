"""Independent fresh native data; same frozen PCS digest, never selection data."""
import argparse,json,random,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import fullstreet_solver as f,public_chance_solver as p
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.action_native import interval,native_value
from gto.qualification.coupled_evaluate import Extra
from gto.qualification.range_study import GeneralNuts
from gto.qualification.evaluate import atomic
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha
from gto.native.training import NativeGame


def run(seed,root,n=4096,conditional=False):
    root=Path(root);folder=root/'warm'/str(seed);meta=json.loads((folder/'policy.json').read_text())
    assert meta['array_sha256']==sha(folder/'policy.npz')
    assert meta['policy_digest']==digest({k:v for k,v in meta.items() if k!='policy_digest'})
    lib=p.build('/tmp/pcs');assert sha(Path(lib._name))==meta['binary_sha256']
    base=load_policy('/tmp/native-qualification',f.old.ARTIFACT)
    data=np.load(folder/'policy.npz');pi=data['pi'];mass=data['average_mass'];visits=data['visits'];data.close()
    new=f.Policy(meta,pi,mass,lib,base);new._digest=meta['policy_digest']
    parent=Path('docs/qa/fullstreet-generalization-20261121/corrected')/str(seed)
    d=np.load(parent/'best-checkpoint.npz');average_increment=mass-d['A'];d.close()
    oldmeta=json.loads((parent/'policy-best.json').read_text());d=np.load(parent/'policy-best.npz')
    old=f.Policy(dict(oldmeta,source_py_sha256=sha(Path(f.__file__)),source_cpp_sha256=sha(Path(f.__file__).with_name('fullstreet_core.cc')),binary_sha256=sha(Path(lib._name)),evaluation_build_migration=True),d['pi'],d['average_mass'],lib,base);d.close()
    kinds=['open3p5','threebet10p5','river_jam','fold','open8']
    # Existing Extra does not implement open8, use generic root-force wrapper.
    class Force:
        def __init__(self,q):self.q=q
        def row(self,o,average=False):
            if o.round==0 and not o.history and 18 in o.actions:return [float(a==18) for a in o.actions]
            return self.q.row(o,average)
    probes=[Extra(new,k) for k in kinds[:-1]]+[Force(new),GeneralNuts(new)]
    values=[[] for _ in range(8)];coverage={r:dict(queries=0,known=0,new_regret=0,new_average=0,both=0) for r in range(4)}
    class Track:
        def row(self,o,average=False):
            c=coverage[o.round];c['queries']+=1;k=new.known.get((o.round,tuple(tuple(h[:3]) for h in o.history)))
            if k is not None:
                na=len(new.nodes[k]['children']);r=o.round;code=f.signal(lib,o.own,o.board)>>(3-r);group=f.public_code(o.board)>>(3-r);at=new.bases[k]+(group*(169<<r)+code)*na;c['known']+=1
                a=bool(np.any(visits[at:at+na]>0));b=bool(average_increment[at:at+na].sum()>1e-14)
                c['new_regret']+=a;c['new_average']+=b;c['both']+=a and b
            return new.row(o,average)
    rng=random.Random(17135101);game=NativeGame([100,100]);st=time.monotonic();track=Track()
    value=native_value
    if conditional:
        from gto.qualification.sparse_study import rb_value
        from gto.qualification.sparse_solver import load
        module=load(next(Path('/tmp/sparse').glob('*.so')))
        value=lambda q,native,game,deck,tape:rb_value(q,native,game,deck,tape,module)
    for i in range(n):
        if time.monotonic()-st>90:raise RuntimeError('native evaluation budget; no completed receipt')
        deck=rng.sample(range(52),9);tape=rng.getrandbits(128)
        for q,v in zip([old,track]+probes,values):v.append(value(q,base.native,game,deck,tape))
    delta=.001/24
    record=dict(seed=seed,n=n,estimator='conditional all-in integration' if conditional else 'raw native rollout',evaluation_source_sha256=sha(Path(__file__)),evaluation_seed=17135101,policy_digest=meta['policy_digest'],native_binary_sha256=sha(Path(base.native.__file__)),
      new_EV=interval(values[1],-50,50,delta),old_EV=interval(values[0],-50,50,delta),paired_EV_change=interval([a-b for a,b in zip(values[1],values[0])],-100,100,delta),
      deviations={k:interval([(1 if k in ('open3p5','open8','fold') else -1)*(a-b) for a,b in zip(v,values[1])],-100,100,delta) for k,v in zip(kinds+['river_nuts'],values[2:])},
      coverage=coverage,seconds=time.monotonic()-st,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
      full_native_BR_upper=None,full_native_NashConv=None,all169_native_action_precision=None,abstraction_error_upper=None,omitted_size_error_upper=None,
      formal_precision_cells=0,formal_acceptance=0,ordinary_registry_admission=False)
    atomic(folder/('native-conditional.json' if conditional else 'native-final.json'),record);print(json.dumps(record),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);a.add_argument('--root',required=True);a.add_argument('--n',type=int,default=4096);a.add_argument('--conditional',action='store_true');x=a.parse_args();run(x.seed,x.root,x.n,x.conditional)
