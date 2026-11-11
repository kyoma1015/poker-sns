"""Research delayed output averaging, never reset genuine training R/S history."""
import hashlib,json,sqlite3,zlib
from pathlib import Path
from gto.abstract import joint_stream as s,fullsupport as fs

def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(4*1024**2):h.update(block)
    return h.hexdigest()

def capture(store,path):
    if store.meta()['cursor'] or store.meta()['owner']:raise ValueError('coherent epoch cutoff required')
    path=Path(path)
    if path.exists():raise ValueError('cutoff already exists; do not overwrite')
    db=sqlite3.connect(path);db.execute('create table state(key text primary key,value blob not null)')
    P=store.pre;prefix=s.unpack(store.get('pre'))
    with db:
        db.execute('insert into state values (?,?)',('pre',zlib.compress(s.pack(prefix[P:2*P]),1)))
        for i in range(len(store.rows)):
            raw=store.get('b:'+str(i));half=len(raw)//2
            if len(raw)%16:raise ValueError('paired double arrays required')
            db.execute('insert into state values (?,?)',('b:'+str(i),zlib.compress(raw[half:],1)))
        db.execute('insert into state values (?,?)',('meta',json.dumps({'source_identity':store.identity,'cutoff_epoch':store.meta()['epoch'],'source_logical_digest':store.logical_digest(),'rows_digest':fs.digest(store.rows)}).encode()))
    db.close()

class Window:
    method='delayed_output_average_actual_full_history_retained'
    def __init__(self,store,cutoff,evaluation):
        if store.meta()['cursor'] or store.meta()['owner']:raise ValueError('coherent source epoch required')
        self.source=store;self.rows=store.rows;self.pre=store.pre
        self.source_meta=store.meta()
        self.cut=sqlite3.connect(Path(cutoff).resolve().as_uri()+'?mode=ro',uri=True)
        meta=json.loads(self.cut.execute("select value from state where key='meta'").fetchone()[0])
        if meta['source_identity']!=store.identity or meta['rows_digest']!=fs.digest(self.rows) or meta['cutoff_epoch']>=store.meta()['epoch']:raise ValueError('matching earlier actual cutoff required')
        self.identity=fs.digest({'source_logical':store.logical_digest(),'cutoff_meta':meta,'cutoff_file_sha256':file_hash(cutoff),'source_module_sha256':file_hash(__file__),'version':1})
        self.db=sqlite3.connect(evaluation);self.db.execute('create table if not exists state(key text primary key,value blob not null)')
        prior=self.db.execute("select value from state where key='identity'").fetchone()
        if prior and prior[0]!=self.identity:raise ValueError('window evaluation source changed')
        with self.db:self.db.execute('insert or ignore into state values (?,?)',('identity',self.identity))
    def subtract(self,key,values):
        old=s.unpack(zlib.decompress(self.cut.execute('select value from state where key=?',(key,)).fetchone()[0]))
        if len(old)!=len(values):raise ValueError('cutoff shape')
        result=[x-y for x,y in zip(values,old)]
        if any(x<0 for x in result):raise ValueError('historical average mass cannot decrease')
        return result
    def state(self,index,T):
        self.check_source()
        reg,avg=self.source.state(index,T);P=self.pre
        return reg,self.subtract('pre',avg[:P])+self.subtract('b:'+str(index),avg[P:])
    def get(self,key):
        if key=='pre':
            self.check_source()
            raw=s.unpack(self.source.get(key));P=self.pre;return s.pack(raw[:P]+self.subtract('pre',raw[P:2*P])+raw[2*P:])
        row=self.db.execute('select value from state where key=?',(key,)).fetchone();return None if row is None else row[0]
    def put(self,key,value):self.db.execute('insert into state values (?,?) on conflict(key) do update set value=excluded.value',(key,value))
    def check_source(self):
        if self.source.meta()!=self.source_meta:raise ValueError('window source advanced during evaluation')
    def meta(self):self.check_source();return self.source_meta
    def digest(self):return self.identity
    def close(self):self.cut.close();self.db.close()
