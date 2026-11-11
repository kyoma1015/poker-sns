"""Finite registered whole-epoch comparison; no source DB writes."""
import hashlib,json,resource,time
from pathlib import Path
from gto.abstract import joint_training as t,joint_stream as s,joint_stream_cache as cache

ROOT=Path('/workspace/joint-training-run');QA=Path('docs/qa/joint-training-20261111')
def save(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
 ROOT.mkdir(exist_ok=True);rows=cache.population();parent='/workspace/joint-updates-run/cfr_plus.sqlite';results={}
 save(ROOT/'registration.json',{'utc':time.time(),'protocol_sha256':hashlib.sha256((QA/'PROTOCOL.md').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(Path(t.__file__).read_bytes()).hexdigest(),'backends':['legacy','vector'],'epochs':1,'max_blocks':3510,'seconds_each':1800,'evaluation_seconds_each':900,'parent':parent,'formal_acceptance':[0,12]})
 for backend in ('legacy','vector'):
  lib=t.build(ROOT/(backend+'-native'),backend);store=t.Store(ROOT/(backend+'.sqlite'),rows,parent,backend);initial=store.logical_digest()
  start=time.process_time();wall=time.monotonic();r=store.train(lib,'/workspace/joint-stream-cache',epochs=1,max_blocks=3510,seconds=1800)
  r.update({'backend':backend,'parent_logical_digest':initial,'logical_digest':store.logical_digest(),'checkpoint_digest':store.digest(),'whole_call_cpu_seconds':time.process_time()-start,'whole_call_wall_seconds':time.monotonic()-wall,'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'complete_epoch':store.meta()['epoch']==4 and store.meta()['owner']==0 and store.meta()['cursor']==0})
  save(ROOT/(backend+'-training.json'),r);results[backend]=r;store.close();print(json.dumps({'finished':backend,**r}),flush=True)
 if all(r['complete_epoch'] for r in results.values()):
  old=t.Store(ROOT/'legacy.sqlite',rows,parent,'legacy');new=t.Store(ROOT/'vector.sqlite',rows,parent,'vector');max_array=max_policy=0.;compared=0
  for i,row in enumerate(rows):
   obj,_=cache.read('/workspace/joint-stream-cache',row);T=len(obj['codes']);pairs=[x.state(i,T) for x in (old,new)]
   for xs,ys in zip(*pairs):max_array=max(max_array,max(abs(x-y) for x,y in zip(xs,ys)))
   for average in (False,True):
    ps=[s.strategy(*pair,s.layout(T)[2],average) for pair in pairs];max_policy=max(max_policy,max(abs(x-y) for x,y in zip(*ps)))
   compared+=1
  results['parity']={'orbits':compared,'max_array_difference':max_array,'max_policy_difference':max_policy,'pass':max_array<1e-8 and max_policy<1e-8,'cpu_speedup':results['legacy']['cpu_seconds']/results['vector']['cpu_seconds']}
  save(ROOT/'parity.json',results['parity']);old.close();new.close()
  for backend in ('legacy','vector'):
   store=t.Store(ROOT/(backend+'.sqlite'),rows,parent,backend);br=s.build(ROOT/(backend+'-independent-br'));r=t.evaluate(store,br,'/workspace/joint-stream-cache',seconds=900)
   save(ROOT/(backend+'-evaluation.json'),r);store.close();print(json.dumps({'evaluated':backend,'coverage':r['coverage'],'nc':r['restricted_nashconv_interval_bb']}),flush=True)
 save(ROOT/'summary.json',results)
if __name__=='__main__':main()
