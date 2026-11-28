import gc,json,tempfile,time
from pathlib import Path
from gto.qualification.integrated_final_study import make,ROOT
from gto.qualification.integrated_study import Track,rb_value,samples
from gto.qualification.sparse_study import archive_restore
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame
records=[]
for seed in (17120101,17120102):
 q,m,r,_=make(seed,True);clone,_,_,_=make(seed,True)
 a=q.step(10);b=clone.step(10)
 with tempfile.TemporaryDirectory() as d:
  x=Path(d)/'a';y=Path(d)/'b';q.core.save(str(x),'replay');clone.core.save(str(y),'replay');assert x.read_bytes()==y.read_bytes()
 del clone;gc.collect();q,_,_,_=make(seed,True);archive_restore(q,ROOT/str(seed)/'last');track=Track(q);st=time.monotonic()
 for deck,tape in samples(17137601,2048):rb_value(track,q.native,NativeGame([100,100]),deck,tape,m)
 records.append(dict(seed=seed,selected_nextstep_exact=a['complete'] and b['complete'],diagnostic='last checkpoint, independent coverage only; not candidate selection',last_iterations=q.iteration,coverage=track.count,worlds=2048,evaluation_seed=17137601,seconds=time.monotonic()-st))
 del q,track;gc.collect()
atomic(ROOT/'replay-and-last-coverage.json',dict(records=records))
print(json.dumps(records))
