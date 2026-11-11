"""Finite registered continuation; only reconstructable cutoff on /tmp."""
import hashlib,json,shutil,sqlite3,time
from pathlib import Path
from gto.abstract import joint_training as t,joint_training_window as w,joint_stream as s,joint_stream_cache as cache

ROOT=Path('/workspace/joint-window-run');QA=Path('docs/qa/joint-training-20261111');ACTIVE=Path('/workspace/joint-training-run/vector.sqlite');BACKUP=Path('/workspace/joint-window-parent/vector4.sqlite');CUT=Path('/tmp/joint-window-cutoff/cutoff.sqlite')
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def run():
 ROOT.mkdir(exist_ok=True)
 if (ROOT/'registration.json').exists():raise ValueError('already registered; inspect consumedbudget,never blindly rerun')
 gate=json.loads((QA/'window-space-gate.json').read_text());space=shutil.disk_usage(ACTIVE.parent).free;temporary=shutil.disk_usage('/tmp').free;reserve=2*1024**3
 placement={'workspace_free':space,'workspace_required':ACTIVE.stat().st_size+reserve,'temporary_free':temporary,'temporary_required':gate['cutoff_estimated_upper_bytes']+reserve,'pass':space>=ACTIVE.stat().st_size+reserve and temporary>=gate['cutoff_estimated_upper_bytes']+reserve,'old_same_filesystem_gate_preserved':True}
 save(ROOT/'placement.json',placement)
 if not placement['pass']:return {'status':'PLACEMENT_BLOCKED'}
 save(ROOT/'registration.json',{'utc':time.time(),'epochs':[5,6,7],'seconds':3600,'max_blocks':10530,'evaluation_seconds_each':900,'protocol_hash':w.file_hash(QA/'WINDOW_PROTOCOL.md'),'storage_addendum_hash':w.file_hash(QA/'WINDOW_STORAGE_ADDENDUM.md'),'source_hashes':{str(p):w.file_hash(p) for p in (Path(t.__file__),Path(w.__file__),Path(__file__))},'normal_GTO_added':0,'formal_acceptance':[0,12]})
 if BACKUP.exists() or CUT.exists():raise ValueError('never overwrite preserved snapshot/cutoff')
 BACKUP.parent.mkdir(exist_ok=True);shutil.copy2(ACTIVE,BACKUP)
 original=w.file_hash(ACTIVE);assert w.file_hash(BACKUP)==original
 db=sqlite3.connect(BACKUP.resolve().as_uri()+'?mode=ro',uri=True);assert db.execute('pragma quick_check').fetchone()[0]=='ok';db.close()
 rows=cache.population();source=t.Store(ACTIVE,rows,'/workspace/joint-updates-run/cfr_plus.sqlite','vector')
 assert source.meta()['epoch']==4 and source.meta()['cursor']==0 and source.meta()['owner']==0
 CUT.parent.mkdir(exist_ok=True);w.capture(source,CUT);save(ROOT/'preservation.json',{'vector4_file_sha256':original,'snapshot':str(BACKUP),'snapshot_exact':True,'cutoff':str(CUT),'cutoff_sha256':w.file_hash(CUT),'cutoff_recoverable_from_actual_workspace_snapshot':True})
 lib=t.build(ROOT/'native','vector');start=time.monotonic();points=[]
 for stop in (5,6,7):
  if min(shutil.disk_usage('/tmp').free,shutil.disk_usage('/workspace').free)<reserve:return {'status':'SPACE_STOP','meta':source.meta()}
  try:r=source.train(lib,'/workspace/joint-stream-cache',epochs=stop-source.meta()['epoch'],max_blocks=3510,seconds=max(0,3600-(time.monotonic()-start)))
  except ValueError as error:return {'status':'TRAIN_GUARD','error':str(error),'meta':source.meta()}
  r['logical_digest']=source.logical_digest();points.append(r);save(ROOT/'training-points.json',points);print(json.dumps({'phase':'window_train','target':stop,'meta':source.meta(),'seconds':time.monotonic()-start}),flush=True)
  if source.meta()['epoch']!=stop or source.meta()['owner'] or source.meta()['cursor']:return {'status':'TRAIN_BUDGET','meta':source.meta()}
 br=s.build(ROOT/'independent-br');full=t.evaluate(source,br,'/workspace/joint-stream-cache',seconds=900);save(ROOT/'full7.json',full)
 view=w.Window(source,CUT,ROOT/'window-evaluation.sqlite');delayed=t.evaluate(view,br,'/workspace/joint-stream-cache',seconds=900);save(ROOT/'delayed7.json',delayed);view.close();source.close()
 assert w.file_hash(BACKUP)==original
 candidates={'immutable_frozen':.9321071527220774}
 for name,r in (('full7',full),('delayed7',delayed)):
  if r['coverage']==1:candidates[name]=r['restricted_nashconv_interval_bb'][1]
 best=min(candidates,key=candidates.get)
 return {'status':'COMPLETE' if full['coverage']==delayed['coverage']==1 else 'EVALUATION_BUDGET','candidates_nashconv_bb':candidates,'selected_same_game_profile':best,'strictly_improves_frozen':candidates[best]<candidates['immutable_frozen']-1e-8,'target_0_1_pass':candidates[best]<=.1,'normal_GTO_added':0,'formal_acceptance':[0,12],'external_GTO':'NOT PERFORMED','real_game_error':'UNKNOWN'}
if __name__=='__main__':
 result=run();save(ROOT/'result.json',result);print(json.dumps(result),flush=True)
