"""Switchable exact kernels and lossless inherited-state overlay. Research only.

Original stores/kernels are unchanged. A backend is part of checkpoint identity;
resumption never silently changes floating-point execution order.
"""
import hashlib,json,sqlite3,zlib,shutil,time,math
from pathlib import Path
from gto.abstract import joint_stream as s,joint_updates as u,joint_alternating as a,joint_vector as v,fullsupport as fs

def build(directory,backend):
    if backend not in ('legacy','vector'):raise ValueError('explicit backend required')
    lib=(u.build if backend=='legacy' else v.build)(directory)
    lib.training_backend=backend
    return lib

class Store(a.Store):
    """Compressed copy-on-write overlay; never modifies the genuine epoch3 parent.

    Parent arrays remain exact bytes, including tiny initialization regrets that
    existed in that actual history. This does not invent frozen-policy history.
    """
    method='alternating_cfr_plus_inherited_switchable'
    def __init__(self,path,rows,parent_path,backend):
        if backend not in ('legacy','vector'):raise ValueError('explicit backend required')
        self.backend=backend;self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.rows=rows;self.pre=s.layout(1)[3]
        self.parent_path=Path(parent_path).resolve()
        if self.path.resolve()==self.parent_path:raise ValueError('overlay must differ from parent')
        if Path(str(self.parent_path)+'-wal').exists() and Path(str(self.parent_path)+'-wal').stat().st_size:raise ValueError('parent must be quiescent')
        self.parent=sqlite3.connect(self.parent_path.as_uri()+'?mode=ro',uri=True)
        meta=json.loads(self.parent.execute("select value from state where key='meta'").fetchone()[0])
        if meta.get('identity')!=u.identity('cfr_plus',rows) or meta['epoch']!=3 or meta['cursor']!=0:raise ValueError('completed genuine same-game epoch3 required')
        parent_hash=a.numeric_digest(self.parent)
        sources=[Path(__file__),Path(a.__file__),Path(u.__file__),Path(s.__file__),Path(v.__file__),Path(v.__file__).with_suffix('.cc'),Path(u.__file__).with_suffix('.cc')]
        self.identity=fs.digest({'backend':backend,'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'parent_identity':meta['identity'],'parent_numeric_digest':parent_hash,'population':rows,'version':1})
        self.db=sqlite3.connect(self.path);self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value BLOB NOT NULL)')
        if self.db.execute("select 1 from state where key='meta'").fetchone() is None:
            with self.db:self.put('meta',json.dumps({'identity':self.identity,'epoch':3,'cursor':0,'owner':0,'backend':backend,'parent_numeric_digest':parent_hash,'inherited_actual_epochs':3}).encode())
        if self.meta()['identity']!=self.identity:raise ValueError('backend/source/parent checkpoint mismatch')
        self.pre_masks=a.masks(1)[:self.pre]
    def get(self,key):
        row=self.db.execute('SELECT value FROM state WHERE key=?',(key,)).fetchone()
        if row is not None:return zlib.decompress(row[0])
        if key=='meta' or key.startswith('eval:'):return None
        row=self.parent.execute('SELECT value FROM state WHERE key=?',(key,)).fetchone()
        return None if row is None else row[0]
    def put(self,key,value):super().put(key,zlib.compress(value,1))
    def logical_digest(self):
        keys={k for k, in self.parent.execute('select key from state')}|{k for k, in self.db.execute('select key from state')}
        return fs.digest([(k,hashlib.sha256(self.get(k)).hexdigest()) for k in sorted(keys) if k!='meta' and not k.startswith('eval:')])
    def train(self,lib,cache_dir,**budget):
        if getattr(lib,'training_backend',None)!=self.backend:raise ValueError('kernel/backend mismatch')
        epochs=budget.pop('epochs',1);max_blocks=budget.pop('max_blocks',3510);seconds=budget.pop('seconds',1800);crash=budget.pop('crash',False)
        if budget or type(epochs) is not int or epochs<1 or type(max_blocks) is not int or max_blocks<0 or not math.isfinite(seconds) or seconds<0:raise ValueError('finite explicit budget required')
        start=time.monotonic();cpu=time.process_time();stop=self.meta()['epoch']+epochs;done=0;P=self.pre;mass=sum(r['multiplicity'] for r in self.rows)
        while self.meta()['epoch']<stop and done<max_blocks and time.monotonic()-start<seconds:
            if shutil.disk_usage(self.path.parent).free<2*1024**3:raise ValueError('overlay free guard2GiB')
            if sum(p.stat().st_size for p in self.path.parent.glob('*.sqlite*'))>3*1024**3:raise ValueError('overlay directory cap3GiB')
            meta=self.meta();i=meta['cursor'];owner=meta['owner'];t=meta['epoch']+1;row=self.rows[i]
            obj,values=s.cache.read(cache_dir,row);reg,avg=self.state(i,len(obj['codes']));out=s.block(lib,obj,values,reg,avg);weight=row['multiplicity']/mass;owners=a.masks(len(obj['codes']));postR=reg[P:];postS=avg[P:]
            for j in range(P,len(reg)):
                if owners[j]==owner:postR[j-P]=max(0.,reg[j]+weight*out['grad'][j]);postS[j-P]+=t*weight*out['avg'][j]
            pre=s.unpack(self.get('pre'))
            for j in range(P):
                if self.pre_masks[j]==owner:pre[2*P+j]+=weight*out['grad'][j];pre[3*P+j]+=weight*out['avg'][j]
            meta['cursor']+=1
            if meta['cursor']==len(self.rows):
                for j in range(P):
                    if self.pre_masks[j]==owner:pre[j]=max(0.,pre[j]+pre[2*P+j]);pre[P+j]+=t*pre[3*P+j]
                    pre[2*P+j]=pre[3*P+j]=0.
                meta['cursor']=0;meta['owner']=1-owner
                if owner==1:meta['epoch']+=1
            with self.db:
                self.put('b:'+str(i),s.pack(postR+postS))
                if crash:raise RuntimeError('simulated alternating transaction interruption')
                self.put('pre',s.pack(pre));self.put('meta',json.dumps(meta).encode());self.db.execute("delete from state where key like 'eval:%'")
            done+=1
            if done%128==0:print(json.dumps({'backend':self.backend,'blocks':done,'epoch':meta['epoch'],'owner':meta['owner'],'cursor':meta['cursor'],'wall':time.monotonic()-start}),flush=True)
        return {'meta':self.meta(),'blocks':done,'seconds':time.monotonic()-start,'cpu_seconds':time.process_time()-cpu}
    def close(self):self.db.close();self.parent.close()

def evaluate(store,lib,cache_dir,**budget):
    # Keep the original independently implemented world-BR evaluator by default.
    return a.evaluate(store,lib,cache_dir,**budget)
