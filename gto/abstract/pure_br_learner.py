"""Same BR qualifier for the immutable completed full7 learner checkpoint."""
import argparse,fcntl,json,sqlite3,time,zlib
from pathlib import Path
from gto.abstract import pure_br as p,pure_br_run as run,joint_stream as s,joint_stream_cache as cache,joint_updates as u,fullsupport as fs,model

class LearnedSnapshot(p.Frozen):
    def __init__(self,path,rows):
        self.path=Path(path);self.rows=rows;self.pre=s.layout(1)[3]
        self.db=sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro',uri=True);self.db.execute('BEGIN')
        meta=self.meta();self.identity=meta['identity']
        if meta['epoch']!=7 or meta['cursor'] or meta['owner']:raise ValueError('coherent completed actual full7 required')
        expected=json.loads(Path('docs/qa/joint-training-20261111/window-full7.json').read_text())
        if self.digest()!=expected['state_digest']:raise ValueError('actual full7 policy differs from recorded independent result')
        keys={k for k, in self.db.execute("select key from state where key like 'b:%'")}
        if keys!={'b:'+str(i) for i in range(len(rows))}:raise ValueError('complete materialized private states required')
    def get(self,key):
        r=self.db.execute('select value from state where key=?',(key,)).fetchone();return None if r is None else zlib.decompress(r[0])

class LearnedRun(run.Run):
    def __init__(self,root,temp):
        self.root=Path(root);self.temp=Path(temp);self.root.mkdir(parents=True,exist_ok=True);self.temp.mkdir(parents=True,exist_ok=True);self.rows=cache.population()
        self.source=LearnedSnapshot('/workspace/joint-training-run/vector.sqlite',self.rows);self.P=self.source.pre;self.L=2*len(model.tree())*169
        self.identity=fs.digest({'target':'actual_full7','source_numeric':self.source.numeric_digest(),'source_meta':self.source.meta(),'population':self.rows,'producer':cache.identity(),'game':s.tree()[0],'code':{x.name:run.hash_file(x) for x in (Path(__file__),Path(run.__file__),Path(p.__file__),Path(p.__file__).with_suffix('.cc'))},'version':1})
        self.db=sqlite3.connect(self.root/'policy.sqlite');self.db.execute('pragma journal_mode=WAL');self.db.execute('pragma synchronous=FULL');self.db.execute('create table if not exists state(key text primary key,value blob not null)')
        if self.get('meta') is None:
            with self.db:self.put('meta',json.dumps({'identity':self.identity,'phase':'extract','cursor':0,'extract_started':time.time(),'verify_started':None}).encode());self.put('sum',s.pack([0.]*(2*self.L+2*self.P+2)))
        if self.meta()['identity']!=self.identity:raise ValueError('full7 source/qualifier mismatch')
    def guard(self):
        super().guard()
        if sum(x.stat().st_size for x in self.root.glob('*.sqlite*'))>48*1024**2:raise ValueError('48MiB full7 compact policy budget')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--temporary',type=Path,required=True);a=parser.parse_args();a.root.mkdir(parents=True,exist_ok=True)
    # This second run starts only after the first run's measured durable footprint.
    first=Path('/workspace/pure-br-run/result.json')
    if not first.exists() or not json.loads(first.read_text()).get('complete') or not json.loads(first.read_text()).get('pass_tolerance'):raise ValueError('finish and pass frozen qualification first')
    import shutil
    if not (a.root/'policy.sqlite').exists() and shutil.disk_usage(a.root).free<2*1024**3+48*1024**2+4*1024**2:raise ValueError('prove full7 capacity before starting')
    with (a.root/'operator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=LearnedRun(a.root,a.temporary);lib=p.build(a.root/'extractor');old=s.build(a.root/'independent');utility=u.build(a.root/'utility')
        if r.meta()['phase']=='extract':r.extract(lib,old,'/workspace/joint-stream-cache')
        result=r.verify(utility,'/workspace/joint-stream-cache') if r.meta()['phase']=='verify' else r.result();result['target_profile']='actual_full7';(a.root/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if not k.startswith('top') and k!='negative_information_sets'}),flush=True)
if __name__=='__main__':main()
