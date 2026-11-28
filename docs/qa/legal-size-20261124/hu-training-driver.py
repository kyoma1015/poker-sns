"""Bounded native legal-size study of one sparse joint external-sampling engine."""
import argparse,copy,gc,json,random,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import sparse_solver as s,fullstreet_solver as old
from gto.qualification.action_native import native_value as raw_value,interval
from gto.qualification.coupled_evaluate import Extra
from gto.qualification.range_study import GeneralNuts
from gto.qualification.native_mccfr import choose,betting
from gto.qualification.policy import act,sha
from gto.qualification.public_response import Observation,observe
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame


def rb_value(policy,native,game,deck,tape,module):
    state=native.NativeState(game);rng=random.Random(tape)
    for c in deck[:4]:state.apply_action(c)
    while not state.is_terminal():
        a=state.audit()
        if state.is_chance_node():
            if a['remaining']==[0,0] and len(a['board'])<5:
                if a['live']!=[100,100]:raise ValueError('HU50 allin stake')
                eq=module.equity_prefix(a['holes'][0]+a['holes'][1],a['board'],16,tape&((1<<64)-1))
                return 50*(2*eq-1)
            state.apply_action(deck[4+len(a['board'])]);continue
        p=state.current_player();o=Observation(p,tuple(sorted(a['holes'][p])),tuple(a['board']),a['round'],a['price'],a['last_full'],tuple(a['remaining']),tuple(a['street']),tuple(a['live']),tuple(a['dead']),tuple(a['folded']),tuple(tuple(h) for h in a['history']),tuple(state.legal_actions()))
        state.apply_action(choose(o.actions,policy.row(o,True),rng))
    return state.returns()[0]/2


def samples(seed,n):
    r=random.Random(seed);return [(r.sample(range(52),9),r.getrandbits(128)) for _ in range(n)]

def selection(q,native,module,worlds):
    probe=Extra(q,'open3p5');base=[];gain=[]
    for deck,tape in worlds:
        v=rb_value(q,native,NativeGame([100,100]),deck,tape,module);base.append(v);gain.append(rb_value(probe,native,NativeGame([100,100]),deck,tape,module)-v)
    return dict(SB_EV_bb=float(np.mean(base)),open3p5_gain_bb=float(np.mean(gain)),n=len(worlds))

def train(module,native_build,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);base=load_policy(native_build,old.old.ARTIFACT);resource_records=[];results=[]
    for seed in (17120101,17120102):
        w,origin=s.warm(module,seed);folder=out/str(seed);folder.mkdir(exist_ok=True)
        if seed==17120101:
            for full,fine in ((True,True),(False,False),(False,True)):
                q=s.Solver(module,w,origin,seed+1000000,full=full,refined=fine);start=time.monotonic();last=None
                for _ in range(4):
                    last=q.step(1.)
                    if not last['complete']:break
                resource_records.append(dict(full=full,refined=fine,last=last,stats=q.core.stats(),seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024));del q;gc.collect()
            atomic(out/'resource-comparison.json',dict(records=resource_records,selection='allnative rejected if incomplete; same geometry engine with strength key continues; omission errors UNKNOWN'))
        q=s.Solver(module,w,origin,seed+1100000,full=False,refined=True);del w;gc.collect();worlds=samples(seed+1200000,256)
        q.save(folder/'initial');initial=selection(q,base.native,module,worlds);q.save(folder/'best');best=initial['open3p5_gain_bb'];curve=[dict(iterations=0,selection=initial)];start=time.monotonic();reason='STAGE_LIMIT';training_seconds=0.
        for target in (64,256,1024):
            while q.iteration<target and time.monotonic()-start<60:
                r=q.step(min(1.,max(.01,60-(time.monotonic()-start))))
                if not r['complete']:reason=r['error'];break
            if not r['complete'] or q.iteration<target:
                q.save(folder/'last');break
            q.save(folder/'last');v=selection(q,base.native,module,worlds);curve.append(dict(iterations=q.iteration,selection=v,stats=q.core.stats(),seconds=time.monotonic()-start));print(json.dumps(dict(seed=seed,**curve[-1])),flush=True);atomic(folder/'selection.json',dict(curve=curve))
            if v['open3p5_gain_bb']>best+1e-10:reason='FIRST_SELECTION_WORSENING';break
            best=v['open3p5_gain_bb'];q.save(folder/'best')
        q.restore(folder/'best');atomic(folder/'freeze.json',dict(policy_digest=q.policy_digest,iterations=q.iteration,source_sha256=sha(Path(__file__)),selection_finished=True,stop_reason=reason,final_evaluations=0))
        result=dict(seed=seed,curve=curve,reason=reason,best_iterations=q.iteration,stats=q.core.stats(),seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,ordinary_registry_admission=False)
        atomic(folder/'training.json',result);results.append(result);del q;gc.collect()
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--library',required=True);p.add_argument('--native-build',required=True);p.add_argument('--out',required=True);a=p.parse_args();train(s.load(a.library),a.native_build,a.out)
