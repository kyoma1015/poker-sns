import ast,hashlib,json,os,pathlib,sqlite3,sys,time,resource
sys.path.insert(0,str(pathlib.Path(__file__).parent/'build_g12_disk'))
import pokerid_g12
from g12_p1_live_backend import LiveBackend
from pokerid_rules import Rules
from fractions import Fraction
root=pathlib.Path(__file__).parent
source=(root/'g12_full52_native_smoke.py').read_text()
node=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='Full52Native')
exec(compile(ast.Module(body=[node],type_ignores=[]),'<full52>','exec'))
dbpath=root/'long9500.sqlite'; db=sqlite3.connect(dbpath);before=dict(db.execute('select k,v from meta'));old=int(before['iteration']);integrity=db.execute('pragma integrity_check').fetchone()[0];db.close()
assert integrity=='ok'
end=old+30
b=LiveBackend(dbpath,cache_kib=512);s=pokerid_g12.Solver(Full52Native(),.6,17,True,True,.1);s.enable_disk_backend(b,'bench-9p52');assert s.iteration==old
start=time.perf_counter()
for _ in range(30):s.run_iteration()
resume_elapsed=time.perf_counter()-start
assert s.iteration==end
out=root/'resume_disk_checkpoint.bin';b.export_native_checkpoint(out,'bench-9p52');b.close()
mem=pokerid_g12.Solver(Full52Native(),.6,17,True,True,.1)
t=time.perf_counter()
for _ in range(end):mem.run_iteration()
mem_elapsed=time.perf_counter()-t
mempath=root/'memory_checkpoint.bin';mem.save_binary(str(mempath),'bench-9p52')
memraw=mempath.read_bytes();diskraw=out.read_bytes();assert memraw+hashlib.sha256(memraw).digest()==diskraw
report={'status':'PASS','abrupt_termination_recovered':True,'sqlite_integrity':integrity,'iteration_at_interruption':old,'resume_additional_iterations':30,'final_iterations':end,'rows':len(mem.keys()),'checkpoint_byte_equal':True,'checkpoint_sha256':hashlib.sha256(memraw).hexdigest(),'resume_wall_s':round(resume_elapsed,3),'memory_wall_s':round(mem_elapsed,3),'disk_checkpoint_bytes':len(diskraw),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limitations':'Interrupted 9500 run after timeout; only '+str(end)+' completed; not 9500 endurance certification.'}
(root/'resume_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print(json.dumps(report,indent=2))
