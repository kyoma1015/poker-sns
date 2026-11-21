"""Full-population alternating RM+ with genuine inherited state; research only."""
import argparse,fcntl,hashlib,json,shutil,sqlite3,time
from pathlib import Path
from gto.abstract import joint_stream as s,joint_updates as u,joint_stream_cache as cache,fullsupport as fs

def numeric_digest(db):
    return fs.digest([(k,hashlib.sha256(v).hexdigest()) for k,v in db.execute("select key,value from state where key!='meta' and key not like 'eval:%' order by key")])

def masks(types):
    ns,base,rows,P,S,b=s.layout(types);owners=[-1]*S
    for start,T,n,k in rows:owners[start:start+T*n]=[ns[k]['actor']]*(T*n)
    return owners

class Store(s.Store):
    method='alternating_cfr_plus_inherited'
    def __init__(self,path,rows,parent_path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.rows=rows;self.pre=s.layout(1)[3]
        source=sqlite3.connect('file:'+str(Path(parent_path).resolve())+'?mode=ro',uri=True)
        parent_meta=json.loads(source.execute("select value from state where key='meta'").fetchone()[0]);parent_hash=numeric_digest(source)
        if parent_meta.get('identity')!=u.identity('cfr_plus',rows) or parent_meta['epoch']!=3 or parent_meta['cursor']!=0:raise ValueError('actual completed same-game CFR+ epoch3 required')
        source_id={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path(s.__file__),Path(u.__file__))}
        self.identity=fs.digest({'algorithm':'alternating_RMplus_linear_average','source':source_id,'base':s.source_identity(),'producer':cache.identity(),'population':rows,'parent_meta':parent_meta,'parent_numeric_digest':parent_hash,'tree':s.tree()[0],'version':1})
        fresh=not self.path.exists();self.db=sqlite3.connect(self.path)
        if fresh:
            source.backup(self.db)
            if numeric_digest(self.db)!=parent_hash:raise ValueError('fork must preserve every inherited numeric byte')
            meta={'identity':self.identity,'epoch':3,'cursor':0,'owner':0,'parent_numeric_digest':parent_hash,'inherited_actual_epochs':3}
            with self.db:self.put('meta',json.dumps(meta).encode());self.db.execute("delete from state where key like 'eval:%'")
        source.close();self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        if self.meta()['identity']!=self.identity:raise ValueError('alternating source/game/parent mismatch')
        self.pre_masks=masks(1)[:self.pre]
    def train(self,lib,cache_dir,*,epochs=1,max_blocks=3510,seconds=3600,crash=False):
        if type(epochs) is not int or epochs<1 or max_blocks<0 or seconds<0:raise ValueError('nonnegative finite budget')
        start=time.monotonic();stop=self.meta()['epoch']+epochs;done=0;P=self.pre;mass=sum(r['multiplicity'] for r in self.rows)
        while self.meta()['epoch']<stop and done<max_blocks and time.monotonic()-start<seconds:
            meta=self.meta();i=meta['cursor'];owner=meta['owner'];t=meta['epoch']+1
            if shutil.disk_usage(self.path.parent).free<4*1024**3:raise ValueError('4GiB free guard')
            if sum(p.stat().st_size for p in self.path.parent.glob('*.sqlite*'))>3*1024**3:raise ValueError('new checkpoint budget3GiB')
            row=self.rows[i];obj,values=cache.read(cache_dir,row);reg,avg=self.state(i,len(obj['codes']));out=s.block(lib,obj,values,reg,avg);weight=row['multiplicity']/mass;owners=masks(len(obj['codes']));postR=reg[P:];postS=avg[P:]
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
            if done%64==0:print(json.dumps({'phase':'alternating_train','blocks':done,'meta':meta,'seconds':time.monotonic()-start}),flush=True)
        return {'meta':self.meta(),'blocks':done,'seconds':time.monotonic()-start}

def evaluate(store,lib,cache_dir,**budget):
    if store.meta()['cursor'] or store.meta()['owner']:raise ValueError('both full owner sweeps required before evaluation')
    result=u.evaluate(store,lib,cache_dir,**budget);result['actual_inherited_epochs']=3;result['update_order']='full_population_SB_then_full_population_BB';return result

def run(root,parent,cache_dir,seconds):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);start=time.monotonic();store=Store(root/'alternating.sqlite',cache.population(),parent);lib=u.build(root/'train');br=s.build(root/'br');remain=lambda:max(0,seconds-(time.monotonic()-start))
    for stop in (4,5):
        path=root/('epoch'+str(stop)+'.json')
        if path.exists() and json.loads(path.read_text())['coverage']==1:continue
        if store.meta()['epoch']<stop:store.train(lib,cache_dir,epochs=stop-store.meta()['epoch'],max_blocks=3510,seconds=remain())
        if store.meta()['epoch']<stop:return {'status':'TRAIN_BUDGET','meta':store.meta()}
        result=evaluate(store,br,cache_dir,seconds=remain());path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'epoch':stop,'coverage':result['coverage'],'nc':result['restricted_nashconv_interval_bb'],'sb':result['sb_br_gain_bb'],'bb':result['bb_br_gain_bb']}),flush=True)
        if result['coverage']<1:return {'status':'EVAL_BUDGET','meta':store.meta()}
    return {'status':'COMPLETE_REGISTERED_BUDGET','meta':store.meta(),'seconds':time.monotonic()-start}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--seconds',type=int,default=3600);a=p.parse_args();a.root.mkdir(parents=True,exist_ok=True)
    with (a.root/'operator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(run(a.root,a.parent,a.cache,a.seconds)),flush=True)
