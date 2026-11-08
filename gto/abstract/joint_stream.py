"""Disk-backed exact population CFR: shared preflop snapshot, atomic board commits."""
import argparse,ctypes as C,hashlib,json,math,sqlite3,subprocess,time
from array import array
from pathlib import Path
from gto.abstract import model,fullsupport as fs,joint_stream_cache as cache
from gto.abstract.joint_reach_study import tree

def build(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);out=directory/'joint-stream.so'
    subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(Path(__file__).with_suffix('.cc')),'-o',str(out)],check=True)
    lib=C.CDLL(str(out.resolve()));lib.stream_block.argtypes=[C.c_int]*4+[model.IP]*10+[model.DP]*11;lib.stream_block.restype=C.c_int;return lib

def layout(types):
    ns,mapping,_=tree();base=[-1]*len(ns);rows=[];s=0
    for street in ('preflop','flop'):
        for k,n in enumerate(ns):
            if n['actor']>=0 and n['street']==street:
                count=len(n['children']);t=169 if street=='preflop' else types;base[k]=s;rows.append((s,t,count,k));s+=t*count
        if street=='preflop':pre=s
    boundary=[-1]*len(ns)
    for old,new in mapping.items():
        if model.tree()[old]['actor']<0:boundary[new]=old
    return ns,base,rows,pre,s,boundary

def strategy(reg,sums,rows,average):
    pi=[0.]*len(reg)
    for start,types,n,k in rows:
        for t in range(types):
            i=start+t*n;v=[sums[i+a] if average else max(0.,reg[i+a]) for a in range(n)];z=math.fsum(v)
            pi[i:i+n]=[x/z for x in v] if z else [1/n]*n
    return pi

def block(lib,obj,values,reg,sums,average=False):
    codes=obj['codes'];T=len(codes);ns,base,rows,pre,S,boundary=layout(T)
    if len(reg)!=S or len(sums)!=S:raise ValueError('board state shape')
    hc=[];vc=[];ht=[];vt=[];mass=[];equity=[]
    for i,a in enumerate(codes):
        for j,b in enumerate(codes):
            z,e=values[2*(i*T+j):2*(i*T+j)+2]
            if z>0:hc.append(a//8);vc.append(b//8);ht.append(i);vt.append(j);mass.append(z);equity.append(e/z)
    W=len(mass)
    if len(ns)*W*24+S*256+W*256>2*1024**3:raise ValueError('2GiB board working-set budget')
    pi=strategy(reg,sums,rows,average);grad=(C.c_double*S)();avg=(C.c_double*S)();B=len(model.tree());leaf=(C.c_double*(2*B*169))();metrics=(C.c_double*3)();anum=(C.c_double*S)();aden=(C.c_double*S)()
    rc=lib.stream_block(len(ns),W,S,B,model.ints([n['actor'] for n in ns]),model.ints([len(n['children']) for n in ns]),model.ints([c for n in ns for c in (n['children']+[-1]*4)[:4]]),model.ints(base),model.ints([int(n['street']=='flop') for n in ns]),model.ints(boundary),model.ints(hc),model.ints(vc),model.ints(ht),model.ints(vt),model.doubles(mass),model.doubles(equity),model.doubles([n.get('c0',0.) for n in ns]),model.doubles([n.get('c1',0.) for n in ns]),model.doubles(pi),grad,avg,leaf,metrics,anum,aden)
    if rc:raise ValueError('stream block rejected '+str(rc))
    return {'grad':list(grad),'avg':list(avg),'leaf':list(leaf),'metrics':list(metrics),'action_num':list(anum[:pre]),'action_den':list(aden[:pre]),'pre':pre,'rows':rows,'policy':pi,'worlds':W,'working_set_estimate_bytes':len(ns)*W*24+S*256+W*256}

def pack(values):return array('d',values).tobytes()
def unpack(blob):
    a=array('d');a.frombytes(blob);return list(a)

def source_identity():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path(__file__).with_suffix('.cc'))}

class Store:
    def __init__(self,path,rows):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.db=sqlite3.connect(path);self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL');self.db.execute('CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value BLOB NOT NULL)')
        self.rows=rows;self.pre=layout(1)[3];self.identity=fs.digest({'source':source_identity(),'producer':cache.identity(),'population':rows,'nodes':tree()[0],'version':1})
        if self.get('meta') is None:
            with self.db:
                self.put('meta',json.dumps({'identity':self.identity,'epoch':0,'cursor':0}).encode());self.put('pre',pack([0.]*(4*self.pre)))
        if self.meta()['identity']!=self.identity:raise ValueError('checkpoint source/game/chance identity mismatch')
    def get(self,key):
        row=self.db.execute('SELECT value FROM state WHERE key=?',(key,)).fetchone();return None if row is None else row[0]
    def put(self,key,value):self.db.execute('INSERT INTO state VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,value))
    def meta(self):return json.loads(self.get('meta'))
    def board(self,index,T):
        S=layout(T)[4];post=S-self.pre;b=self.get('b:'+str(index));return [0.]*(2*post) if b is None else unpack(b)
    def state(self,index,T):
        pre=unpack(self.get('pre'));post=self.board(index,T);P=self.pre;H=len(post)//2
        return pre[:P]+post[:H],pre[P:2*P]+post[H:]
    def digest(self):return fs.digest([(k,hashlib.sha256(v).hexdigest()) for k,v in self.db.execute('SELECT key,value FROM state ORDER BY key')])
    def train(self,lib,cache_dir,*,epochs=1,max_blocks=1755,seconds=3600,crash=False):
        if type(epochs) is not int or epochs<1 or max_blocks<0 or seconds<0:raise ValueError('explicit nonnegative resource budget')
        start=time.monotonic();done=0;stop=self.meta()['epoch']+epochs;reason='BUDGET_OR_COMPLETE'
        while self.meta()['epoch']<stop and done<max_blocks and time.monotonic()-start<seconds:
            meta=self.meta();i=meta['cursor'];row=self.rows[i]
            try:obj,values=cache.read(cache_dir,row)
            except FileNotFoundError:reason='WAITING_CACHE';break
            reg,sums=self.state(i,len(obj['codes']));out=block(lib,obj,values,reg,sums);P=self.pre;weight=row['multiplicity']/sum(r['multiplicity'] for r in self.rows)
            disk=sum(p.stat().st_size for p in Path(cache_dir).glob('*.json'))+sum(p.stat().st_size for p in self.path.parent.glob(self.path.name+'*'))
            if disk>12*1024**3:raise ValueError('12GiB checkpoint/cache budget')
            pre=unpack(self.get('pre'));postR=[r+weight*d for r,d in zip(reg[P:],out['grad'][P:])];postS=[s+weight*d for s,d in zip(sums[P:],out['avg'][P:])]
            for j in range(P):pre[2*P+j]+=weight*out['grad'][j];pre[3*P+j]+=weight*out['avg'][j]
            meta['cursor']+=1
            if meta['cursor']==len(self.rows):
                for j in range(P):pre[j]+=pre[2*P+j];pre[P+j]+=pre[3*P+j];pre[2*P+j]=pre[3*P+j]=0.
                meta['epoch']+=1;meta['cursor']=0
            with self.db:
                self.put('b:'+str(i),pack(postR+postS))
                if crash:raise RuntimeError('simulated interruption before atomic cursor commit')
                self.put('pre',pack(pre));self.put('meta',json.dumps(meta).encode());self.db.execute("DELETE FROM state WHERE key LIKE 'eval:%'")
            done+=1
            if done%32==0:print(json.dumps({'phase':'train','blocks':done,'meta':meta,'seconds':time.monotonic()-start}),flush=True)
        return {'meta':self.meta(),'blocks':done,'seconds':time.monotonic()-start,'state_digest':self.digest(),'stop_reason':reason}

def collapse(leaf):
    """Integrate all board chance first, then maximize own preflop classes."""
    ns=model.tree();B=len(ns);out=[]
    for owner in (0,1):
        v=[None]*B
        for k in range(B-1,-1,-1):
            n=ns[k]
            if n['actor']<0:v[k]=leaf[(owner*B+k)*169:(owner*B+k+1)*169]
            else:v[k]=[(max if n['actor']==owner else math.fsum)(v[c][t] for c in n['children']) for t in range(169)]
        out.append(math.fsum(v[0]))
    return out

def evaluate(store,lib,cache_dir,*,max_blocks=1755,seconds=3600):
    if store.meta()['cursor']:raise ValueError('evaluate only completed coherent epochs')
    P=store.pre;B=len(model.tree());length=2*B*169+3+2*P+1
    prior=store.get('eval:sum');total=[0.]*(length+1) if prior is None else unpack(prior);cursor=int(total[-1]);start=time.monotonic();done=0
    while cursor<len(store.rows) and done<max_blocks and time.monotonic()-start<seconds:
        row=store.rows[cursor]
        try:obj,values=cache.read(cache_dir,row)
        except FileNotFoundError:break
        reg,sums=store.state(cursor,len(obj['codes']));out=block(lib,obj,values,reg,sums,True);weight=row['multiplicity']/sum(r['multiplicity'] for r in store.rows);add=out['leaf']+out['metrics']+out['action_num']+out['action_den']
        for j,x in enumerate(add):total[j]+=weight*x
        for base,types,n,k in out['rows']:
            if base>=P:
                for t in range(types):total[-2]+=max(0.,*reg[base+t*n:base+(t+1)*n])
        cursor+=1;total[-1]=cursor
        with store.db:store.put('eval:sum',pack(total))
        done+=1
        if done%64==0:print(json.dumps({'phase':'evaluate','blocks':cursor,'seconds':time.monotonic()-start}),flush=True)
    coverage=sum(r['multiplicity'] for r in store.rows[:cursor])/sum(r['multiplicity'] for r in store.rows);missing=1-coverage;h,v=collapse(total[:2*B*169]);ev,known,unknown=total[2*B*169:2*B*169+3];nc=h+v
    prefix=unpack(store.get('pre'));ns,base,rows,_,_,_=layout(1);bound=total[-2]
    for start,types,n,k in rows:
        if start<P:
            for t in range(types):bound+=max(0.,*prefix[start+t*n:start+(t+1)*n])
    epoch=store.meta()['epoch'];bound=bound/epoch if epoch else None
    if not missing and epoch and nc>bound+1e-8:raise ValueError('population regret certificate mismatch')
    prepi=strategy(prefix[:P],prefix[P:2*P],[r for r in rows if r[0]<P],True)
    at=2*B*169+3;num=total[at:at+P];den=total[at+P:at+2*P]
    return {'epoch':epoch,'evaluated_orbits':cursor,'population_orbits':len(store.rows),'coverage':coverage,'partial_sb_ev_bb':ev,'sb_ev_interval_bb':[ev-50*missing,ev+50*missing],'restricted_nashconv_interval_bb':[max(0.,nc-100*missing),max(0.,min(100.,nc+100*missing))],'sb_br_gain_bb':h-ev if not missing else None,'bb_br_gain_bb':v+ev if not missing else None,'positive_regret_bound_bb':bound if not missing else None,'preflop_frequency':fs.pack(prepi),'preflop_action_ev_bb':[a/b if b>0 else None for a,b in zip(num,den)],'preflop_layout':[{'base':start,'classes':types,'actions':ns[k]['actions'],'history':ns[k]['history'],'node':k} for start,types,n,k in rows if start<P],'future_ev_envelope_bb':[known-50*(unknown+missing),known+50*(unknown+missing)],'nonallin_showdown_mass':unknown,'target_0_1_bb_pass':not missing and nc<=.1,'sampling_error_bb':0,'numerical_guard_bb':1e-8,'full_real_game_gto_verified':False,'external_GTO':'NOT PERFORMED','formal_acceptance':0,'state_digest':store.digest(),'wall_seconds':time.monotonic()-start}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('train','evaluate'),required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--epochs',type=int,default=1);p.add_argument('--seconds',type=int,default=3600);p.add_argument('--max-blocks',type=int,default=1755);a=p.parse_args();s=Store(a.checkpoint,cache.population());lib=build(a.build)
    result=s.train(lib,a.cache,epochs=a.epochs,seconds=a.seconds,max_blocks=a.max_blocks) if a.phase=='train' else evaluate(s,lib,a.cache,seconds=a.seconds,max_blocks=a.max_blocks);a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('preflop_frequency','preflop_action_ev_bb','preflop_layout')}),flush=True)
