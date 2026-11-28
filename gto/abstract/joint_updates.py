"""Registered update schedules around the immutable exact population kernel.

No old checkpoint is migrated or edited. Original BR remains the evaluator.
"""
import argparse,fcntl,ctypes as C,hashlib,json,math,shutil,sqlite3,subprocess,time
from pathlib import Path
from gto.abstract import joint_stream as s,joint_stream_cache as cache,fullsupport as fs,model
METHODS=('vanilla_linear','cfr_plus','dcfr')

def update(reg,avg,grad,own,t,method):
    if method not in METHODS or t<1:raise ValueError('registered update schedule required')
    r=[a+b for a,b in zip(reg,grad)]
    if method=='cfr_plus':r=[max(0.,x) for x in r]
    elif method=='dcfr':r=[x*(t**(1.5 if x>0 else 0)/(t**(1.5 if x>0 else 0)+1)) for x in r]
    if method=='dcfr':a=[(x+y)*(t/(t+1))**2 for x,y in zip(avg,own)]
    else:a=[x+t*y for x,y in zip(avg,own)]
    return r,a

def build(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);out=directory/'joint-updates.so'
    subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(Path(__file__).with_suffix('.cc')),'-o',str(out)],check=True)
    lib=C.CDLL(str(out.resolve()));fn=lib.stream_train_block;fn.argtypes=[C.c_int]*4+[model.IP]*10+[model.DP]*11;fn.restype=C.c_int;lib.stream_block=fn;return lib

def identity(method,rows):
    return fs.digest({'method':method,'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_suffix('.cc')]},'base':s.source_identity(),'producer':cache.identity(),'population':rows,'tree':s.tree()[0],'initial_regret_epsilon':1e-15,'initial_average':0,'version':1})

class Store(s.Store):
    def __init__(self,path,rows,method):
        if method not in METHODS:raise ValueError('method')
        self.method=method;self.rows=rows;self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.pre=s.layout(1)[3];self.identity=identity(method,rows)
        self.db=sqlite3.connect(path);self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL');self.db.execute('CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value BLOB NOT NULL)')
        if self.get('meta') is None:
            with self.db:self.put('meta',json.dumps({'identity':self.identity,'method':method,'epoch':0,'cursor':0,'initialized':False,'init_cursor':0}).encode());self.put('pre',s.pack([0.]*(4*self.pre)))
        if self.meta()['identity']!=self.identity:raise ValueError('method/source/game/chance mismatch')
    def initialize(self,baseline,cache_dir,seconds=3600):
        start=time.monotonic();meta=self.meta()
        if meta['initialized']:return True
        if meta['epoch'] or meta['cursor']:raise ValueError('fresh initialization required')
        if baseline.meta()['epoch'] or not baseline.get('baseline:ready'):raise ValueError('completed immutable baseline required')
        P=self.pre;prefix=s.unpack(baseline.get('pre'));rows=[r for r in s.layout(1)[2] if r[0]<P];pi=s.strategy(prefix[:P],prefix[P:2*P],rows,True)
        if meta['init_cursor']==0:
            with self.db:self.put('pre',s.pack([1e-15*x for x in pi]+[0.]*(3*P)))
        while meta['init_cursor']<len(self.rows) and time.monotonic()-start<seconds:
            i=meta['init_cursor'];obj,_=cache.read(cache_dir,self.rows[i]);reg,avg=baseline.state(i,len(obj['codes']));pi=s.strategy(reg,avg,s.layout(len(obj['codes']))[2],True);post=pi[P:]
            meta['init_cursor']+=1
            with self.db:self.put('b:'+str(i),s.pack([1e-15*x for x in post]+[0.]*len(post)));self.put('meta',json.dumps(meta).encode())
        if meta['init_cursor']==len(self.rows):
            meta['initialized']=True
            with self.db:self.put('meta',json.dumps(meta).encode())
        return meta['initialized']
    def train(self,lib,cache_dir,*,epochs=1,max_blocks=1755,seconds=3600,crash=False):
        if not self.meta()['initialized']:raise ValueError('incomplete frozen initialization')
        if type(epochs) is not int or epochs<1 or max_blocks<0 or seconds<0:raise ValueError('explicit nonnegative resource budget')
        start=time.monotonic();done=0;stop=self.meta()['epoch']+epochs;P=self.pre;mass=sum(x['multiplicity'] for x in self.rows)
        while self.meta()['epoch']<stop and done<max_blocks and time.monotonic()-start<seconds:
            meta=self.meta();i=meta['cursor'];t=meta['epoch']+1;row=self.rows[i]
            if shutil.disk_usage(self.path.parent).free<4*1024**3:raise ValueError('filesystem free guard4GiB')
            if sum(p.stat().st_size for p in self.path.parent.rglob('*.sqlite*'))>8*1024**3:raise ValueError('trial disk cap8GiB')
            obj,values=cache.read(cache_dir,row);reg,avg=self.state(i,len(obj['codes']));out=s.block(lib,obj,values,reg,avg);weight=row['multiplicity']/mass
            postR,postS=update(reg[P:],avg[P:],[weight*x for x in out['grad'][P:]],[weight*x for x in out['avg'][P:]],t,self.method)
            pre=s.unpack(self.get('pre'))
            for j in range(P):pre[2*P+j]+=weight*out['grad'][j];pre[3*P+j]+=weight*out['avg'][j]
            meta['cursor']+=1
            if meta['cursor']==len(self.rows):
                r,a=update(pre[:P],pre[P:2*P],pre[2*P:3*P],pre[3*P:],t,self.method);pre=r+a+[0.]*(2*P);meta['epoch']+=1;meta['cursor']=0
            with self.db:
                self.put('b:'+str(i),s.pack(postR+postS))
                if crash:raise RuntimeError('simulated atomic interruption')
                self.put('pre',s.pack(pre));self.put('meta',json.dumps(meta).encode());self.db.execute("DELETE FROM state WHERE key LIKE 'eval:%'")
            done+=1
            if done%64==0:print(json.dumps({'method':self.method,'phase':'train','blocks':done,'meta':meta,'seconds':time.monotonic()-start}),flush=True)
        return {'meta':self.meta(),'blocks':done,'seconds':time.monotonic()-start,'digest':self.digest()}

def evaluate(store,lib,cache_dir,**budget):
    class Proxy:
        def __getattr__(self,key):return getattr(store,key)
        def meta(self):return {**store.meta(),'epoch':0}
    # Discounted/linear average needs a differently weighted regret certificate;
    # do NOT reuse the old unweighted bound. Exact independent BR still applies.
    result=s.evaluate(Proxy(),lib,cache_dir,**budget);result['epoch']=store.meta()['epoch'];result['method']=store.method;result['positive_regret_bound_bb']=None;result['regret_bound_status']='UNWEIGHTED_CERTIFICATE_NOT_APPLICABLE';return result

def run(root,method,cache_dir,baseline_path,seconds=7200):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);start=time.monotonic();lib=build(root/(method+'-native'));br=s.build(root/(method+'-br'));rows=cache.population();store=Store(root/(method+'.sqlite'),rows,method);baseline=s.Store(baseline_path,rows)
    remain=lambda:max(0,seconds-(time.monotonic()-start))
    if not store.initialize(baseline,cache_dir,remain()):return {'status':'INIT_BUDGET','meta':store.meta()}
    for stop in (1,2):
        path=root/(method+'-epoch'+str(stop)+'.json')
        if path.exists() and json.loads(path.read_text())['coverage']==1:continue
        if store.meta()['epoch']<stop:store.train(lib,cache_dir,epochs=stop-store.meta()['epoch'],max_blocks=1755*stop,seconds=remain())
        if store.meta()['epoch']<stop:return {'status':'TRAIN_BUDGET','meta':store.meta()}
        result=evaluate(store,br,cache_dir,seconds=remain());path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'method':method,'epoch':stop,'coverage':result['coverage'],'nc':result['restricted_nashconv_interval_bb'],'sb':result['sb_br_gain_bb'],'bb':result['bb_br_gain_bb']}),flush=True)
        if result['coverage']<1:return {'status':'EVAL_BUDGET','meta':store.meta()}
    return {'status':'COMPLETE_FIXED_BUDGET','method':method,'seconds':time.monotonic()-start,'meta':store.meta()}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--method',choices=METHODS,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--seconds',type=int,default=7200);a=p.parse_args();a.root.mkdir(parents=True,exist_ok=True)
    with (a.root/(a.method+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        print(json.dumps(run(a.root,a.method,a.cache,a.baseline,a.seconds)),flush=True)
