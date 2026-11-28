"""Matched pureCPU active CF-refinement control; no final-data selection."""
import argparse,gc,json,random,time,resource,hashlib
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from gto.qualification import cf_refine as cf,refine_checkpoint as cp,public_stream_study as store,public_stream_batch as proposal,stream_sampling as ss,stream_chance as sc,stream_measure as sm,sampling_policy,sparse_solver,integrated_study as old
from gto.qualification.build import load
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
from gto.qualification.sparse_study import samples,rb_value
from gto.native.training import NativeGame
ROOT=Path('docs/qa/cf-refinement-20261128')

def make(seed):
 path=Path(f'docs/qa/public-stream-final-20261127/{seed}/t64');q,meta,rng=store.restore(path);rules,native=load('/tmp/native-qualification');m=sparse_solver.load(next(Path('/tmp/sparse').glob('*.so')));w,origin=sparse_solver.warm(m,seed);fallback=old.old_policy(m,w,origin,seed);fallback.native=native;p=sampling_policy.Policy(q,fallback,meta)
 expected=json.load(open(path.parent/'independent-final/result.json'))['reports'][3]['digest'];assert p.policy_digest==expected
 return q,cf.Parent(p),meta,rules,native,m

def metric(q,parent,seed,physical=False):
 snapshot=cf.next_bank(q,sc.catalog(q.lib,seed),parent);v=sm.measure(snapshot,physical);del snapshot;gc.collect();return v

def run(seed,mode):
 folder=ROOT/str(seed)/mode
 if folder.exists():raise FileExistsError('preserve existing gate')
 folder.mkdir();start=time.monotonic();original,parent,meta,rules,native,m=make(seed);ranking=json.load(open(folder.parent/'selection-rank.json'));chosen=[(r['node'],r['coarse']) for r in ranking['chosen']] if mode=='refined' else []
 baseline=SimpleNamespace(**{k:getattr(original,k) for k in ('lib','nodes','base','keys','S','R','A','prior','visits')})
 q=cf.change(original,chosen,parent);p=cf.Policy(q,parent,dict(stage='initial'))
 # Native equality on fresh development worlds including branches not in bank.
 game=NativeGame([100,100])
 for deck,tape in samples(17160201,128):
  a=rb_value(parent.p,native,game,deck,tape,m);b=rb_value(p,native,game,deck,tape,m)
  if abs(a-b)>1e-10:raise ValueError('initial native behavior changed')
 parent.slim();del original,p;gc.collect();rng=random.Random(17160211+seed);sources=[Path(__file__),Path(cf.__file__),Path(cp.__file__)]
 identity=dict(seed=seed,mode=mode,nodes=q.nodes,splits=sorted(q.splits),parent_checkpoint=f'docs/qa/public-stream-final-20261127/{seed}/t64',parent_receipt_sha256=sha(Path(f'docs/qa/public-stream-final-20261127/{seed}/t64/receipt.json')),binary_sha256=sha(Path(q.lib._name)),sources={str(p):sha(p) for p in sources},parent_policy_digest=parent.p.policy_digest,refinement_history='unchanged old keys retain exact R/A; appended fine keys R/A0 and causal frozen-parent prior',formal_pass=False)
 cp.save(q,baseline,folder/'initial',identity,rng);curve=[];CPU=0;draws=[]
 for budget in (0,90,180):
  while CPU<budget:
   state=rng.getstate();tick=time.process_time()
   try:
    draw=rng.getrandbits(64);blocks=proposal.catalog(q.lib,draw);new=cf.next_bank(q,blocks,parent)
    if new.S>10000000:raise MemoryError('10M scalar cap')
    new.step()
   except Exception:rng.setstate(state);raise
   CPU+=time.process_time()-tick;q=new;del new;draws.append(draw);gc.collect()
  coarse=metric(q,parent,17160101+seed);fine=metric(q,parent,17160101+seed,True);curve.append(dict(CPU=CPU,t=q.t,updates=q.t-64,cells=q.S,NC=coarse,fine=fine));atomic(folder/'curve.json',dict(curve=curve,selection_only=True));print(json.dumps(dict(seed=seed,mode=mode,CPU=CPU,t=q.t,NC=coarse['NashConv_bb'],fine=fine['NashConv_bb'])),flush=True)
 cp.save(q,baseline,folder/'last',identity,rng);p=cf.Policy(q,parent,identity)
 atomic(folder/'result.json',dict(seed=seed,mode=mode,curve=curve,selected_splits=chosen,initial_native_equal=True,policy_digest=p.policy_digest,CPU=CPU,seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,draw_seeds=draws,full_native_BR_upper=None,formal_pass=0))
 # Real immutable checkpoint replay, including next fresh public draw.
 draw=rng.getrandbits(64);n=cf.next_bank(q,proposal.catalog(q.lib,draw),parent);n.step();expected=[hashlib.sha256(getattr(n,k).tobytes()).hexdigest() for k in ('R','A','visits')];del n,p,q;gc.collect();r,_,rr=cp.restore(folder/'last',baseline);assert rr.getrandbits(64)==draw;n=cf.next_bank(r,proposal.catalog(r.lib,draw),parent);n.step();assert expected==[hashlib.sha256(getattr(n,k).tobytes()).hexdigest() for k in ('R','A','visits')]
 atomic(folder/'replay.json',dict(next_fresh_RNG_and_R_A_visits_exact=True,hashes=expected,draw_seed=draw))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--mode',choices=['control','refined'],required=True);a=p.parse_args();run(a.seed,a.mode)
