"""Disentangle information refinement from different work per pureCPU budget."""
import json,gc,time,hashlib
from pathlib import Path
from types import SimpleNamespace
from gto.qualification import cf_refine_study as st,cf_refine as cf,refine_checkpoint as cp,public_stream_batch as proposal
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic

def run(seed):
 folder=st.ROOT/str(seed)/'matched-control'
 if folder.exists():raise FileExistsError('preserve matched control')
 folder.mkdir();old,parent,_,rules,native,m=st.make(seed);base=SimpleNamespace(**{k:getattr(old,k) for k in ('lib','nodes','base','keys','S','R','A','prior','visits')});q,meta,rng=cp.restore(st.ROOT/str(seed)/'control/last',base);parent.slim();del old;gc.collect();ref=json.load(open(st.ROOT/str(seed)/'refined/result.json'));original_t=q.t;draws=[];tick=time.process_time()
 while q.t<ref['curve'][-1]['t']:
  draw=rng.getrandbits(64);q=cf.next_bank(q,proposal.catalog(q.lib,draw),parent);q.step();draws.append(draw)
 CPU=time.process_time()-tick;assert draws==ref['draw_seeds'][original_t-64:]
 coarse=st.metric(q,parent,17160101+seed);fine=st.metric(q,parent,17160101+seed,True);meta={k:v for k,v in meta.items() if k not in ('records','logical_array_bytes','compressed_array_bytes','S','t','blocks','layout','rng')};meta.update(mode='matched-control',matching='same update count and identical public draws as refined',sources={**meta['sources'],str(Path(__file__)):sha(Path(__file__))});cp.save(q,base,folder/'last',meta,rng)
 atomic(folder/'result.json',dict(seed=seed,from_t=original_t,t=q.t,extra_CPU_seconds=CPU,NC=coarse,fine=fine,public_draws_match_refined=True,formal_pass=0));print(seed,'matched',q.t,coarse,fine,flush=True)
 draw=rng.getrandbits(64);n=cf.next_bank(q,proposal.catalog(q.lib,draw),parent);n.step();h=[hashlib.sha256(getattr(n,k).tobytes()).hexdigest() for k in ('R','A','visits')];del n,q;gc.collect();r,_,rr=cp.restore(folder/'last',base);assert rr.getrandbits(64)==draw;n=cf.next_bank(r,proposal.catalog(r.lib,draw),parent);n.step();assert h==[hashlib.sha256(getattr(n,k).tobytes()).hexdigest() for k in ('R','A','visits')];atomic(folder/'replay.json',dict(next_draw_and_step_exact=True,hashes=h))
if __name__=='__main__':
 for seed in (17120101,17120102):run(seed)
