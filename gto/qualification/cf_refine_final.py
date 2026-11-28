"""Fresh frozen-policy final comparison. Never selects/retrains on final data."""
import argparse,gc,json,time,random,itertools,math,resource
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from gto.abstract import model
from gto.qualification import cf_refine_study as study,cf_refine as cf,refine_checkpoint as codec,stream_chance as sc,stream_measure as measure,integrated_study as old,integrated_precision as precision,range_ev,native_tree_bound,active_native,symmetry_br
from gto.qualification.sparse_study import samples,rb_value,Force
from gto.qualification.action_native import interval
from gto.qualification.evaluate import atomic
from gto.qualification.policy import sha
from gto.qualification.variance_study import compressed
from gto.native.training import NativeGame
ROOT=study.ROOT

def run(seed,n):
 out=ROOT/str(seed)/'independent-final'
 if out.exists():raise FileExistsError('preserve final evidence')
 out.mkdir();atomic(out/'freeze.json',dict(native_seed=17160401,n=n,catalog_seed=17160301+seed,candidate='predeclared refined last; control and parent comparison, no final-data selection'))
 original,parent,meta,rules,native,m=study.make(seed);base=SimpleNamespace(**{k:getattr(original,k) for k in ('lib','nodes','base','keys','S','R','A','prior','visits')});del meta
 legacy=cf.next_bank(original,sc.catalog(original.lib,17153301+seed),parent);legacy_sym=symmetry_br.measure(legacy);legacy_raw=json.load(open(Path(f'docs/qa/public-stream-final-20261127/{seed}/independent-final/finite-final.json')));assert abs(legacy_sym['EV_bb']-legacy_raw['coarse']['EV_bb'])<1e-10;assert legacy_raw['fine']['NashConv_bb']+1e-8>=legacy_sym['NashConv_bb']>=legacy_raw['coarse']['NashConv_bb']-1e-8
 atomic(out/'legacy-law-diagnosis.json',dict(parent_policy_digest=parent.p.policy_digest,old_raw=legacy_raw,symmetrized=legacy_sym,finite_suit_law_premium=legacy_raw['fine']['NashConv_bb']-legacy_sym['NashConv_bb'],symmetric_information_gap=legacy_sym['NashConv_bb']-legacy_raw['coarse']['NashConv_bb'],full_target_chance_error_upper=None,scope='diagnosis of OLD policy/final law only, not candidate selection'));del legacy;gc.collect()
 snapshot=cf.next_bank(original,sc.catalog(original.lib,17160301+seed),parent);finite={'parent':measure.refinement_envelope(snapshot)};finite['parent']['symmetrized']=symmetry_br.measure(snapshot);del snapshot;parent.slim();del original;gc.collect();names=['parent','matched-control','refined','oldlast'];ids=[];values=[];coverage=[];st=time.monotonic();kinds=old.KINDS+['open7','open4p5','open9p5'];signs=old.SIGNS+[1,1,1]
 for mode in names:
  q=None
  if mode=='parent':p=parent.p
  elif mode=='oldlast':
   p,_,_=active_native.previous.restore(seed)
   expected=json.load(open(Path(f'docs/qa/public-stream-final-20261127/{seed}/independent-final/result.json')))['reports'][1]['digest'];assert p.policy_digest==expected
  else:
   folder=ROOT/str(seed)/mode/'last';q,identity,_=codec.restore(folder,base)
   if sha(Path(identity['parent_checkpoint'])/'receipt.json')!=identity['parent_receipt_sha256']:raise ValueError('immutable parent receipt SHA')
   p=cf.Policy(q,parent,identity);snapshot=cf.next_bank(q,sc.catalog(q.lib,17160301+seed),parent);finite[mode]=measure.refinement_envelope(snapshot);finite[mode]['symmetrized']=symmetry_br.measure(snapshot);del snapshot;gc.collect()
  pid=p.policy_digest;rows=[[] for _ in range(10)];cov={r:{} for r in range(4)};game=NativeGame([100,100])
  for k,(deck,tape) in enumerate(samples(17160401,n)):
   if time.monotonic()-st>1800:raise RuntimeError('1800s final native budget; incomplete not evidence')
   if hasattr(p,'base') and len(p.base.cache)>16384:p.base.cache.clear()
   for a,(arm,row) in enumerate(zip([p,*old.probes(p),Force(p,16),Force(p,11),Force(p,21)],rows)):
    before={r:dict(v) for r,v in getattr(p,'stats',{}).items()} if a==0 else {};row.append(rb_value(arm,native,game,deck,tape,m))
    if a==0:
     for r,c in getattr(p,'stats',{}).items():
      for key,v in c.items():cov[r][key]=cov[r].get(key,0)+v-before.get(r,{}).get(key,0)
   if (k+1)%8192==0:print(json.dumps(dict(seed=seed,mode=mode,n=k+1,seconds=time.monotonic()-st)),flush=True);compressed(out/'progress.json.gz',dict(complete=False,mode=mode,values=values+[rows]))
  assert p.policy_digest==pid;ids.append(pid);values.append(rows);coverage.append(cov)
  if mode=='refined':
   atomic(out/'native-tree-proof.json',native_tree_bound.verify(q.nodes,rules));precision.certificate(p,rules,m,out,seed,context_seconds=30)
   classes=model.classes();cid={tuple(sorted(h)):i for i,g in enumerate(classes) for h in g};b,hero,L,C=precision.tables(p,rules,[8,23]);extra={};delta=.0005/(2*169*3)
   for label in ('AA','KK','QQ'):
    i=model.CLASSES.index(label);own=list(classes[i][0]);pairs=list(itertools.combinations([c for c in range(52) if c not in own],2));hids=np.array([cid[x] for x in pairs]);Z=float(L[hids].sum())
    if Z<=0:extra[label]=dict(status='UNKNOWN_ZERO_RANGE');continue
    t=time.process_time();extra[label]=range_ev.cell(own,pairs,L[hids]/Z,C[hids],b.live[1-hero]/2,delta=delta,seed=17160501+seed+i);extra[label]['CPU_seconds']=time.process_time()-t;print(json.dumps(dict(seed=seed,EV_hand=label,**{k:extra[label][k] for k in ['n','halfwidth','proposal_precision_pass']})),flush=True)
   atomic(out/'conditional-range-EV.json',dict(policy_digest=pid,context='vs3bet10p5',prefix=[8,23],rows=extra,delta_per_cell=delta,confidence_family=.9995,combined_with_prior_method_family_at_least=.999,source_sha256=sha(Path(range_ev.__file__)),kernel_sha256=sha(Path(range_ev.__file__).with_name('range_ev_core.cc')),formal_precision_cells=0,full_native_BR_upper=None))
  del arm,p,q;gc.collect()
 delta=.001/200;reports=[]
 for name,pid,vs,cov in zip(names,ids,values,coverage):reports.append(dict(mode=name,digest=pid,EV=interval(vs[0],-50,50,delta),deviations={kind:interval([sgn*(a-b) for a,b in zip(v,vs[0])],-100,100,delta) for kind,sgn,v in zip(kinds,signs,vs[1:])},baseline_coverage=cov))
 paired=[]
 for j in (0,1,3):paired.append(dict(control=names[j],EV=interval([a-b for a,b in zip(values[2][0],values[j][0])],-100,100,delta),gain_differences={kind:interval([sgn*((a-b)-(c-d)) for a,b,c,d in zip(v,values[2][0],w,values[j][0])],-200,200,delta) for kind,sgn,v,w in zip(kinds,signs,values[2][1:],values[j][1:])}))
 compressed(out/'values.json.gz',dict(seed=17160401,digests=ids,values=values));atomic(out/'result.json',dict(seed=seed,n=n,native_seed=17160401,catalog_seed=17160301+seed,finite=finite,reports=reports,paired=paired,family_confidence=.999,events=200,seconds=time.monotonic()-st,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,source_sha256=sha(Path(__file__)),symmetry_oracle_sha256=sha(Path(symmetry_br.__file__)),formal_pass=0,full_native_BR_upper=None,selection=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--n',type=int,default=32768);a=p.parse_args();run(a.seed,a.n)
