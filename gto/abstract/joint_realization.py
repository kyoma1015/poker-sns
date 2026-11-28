"""Read-only own-realization mixture; NEVER a fabricated CFR regret history."""
import argparse,fcntl,hashlib,json,sqlite3,time
from pathlib import Path
from gto.abstract import joint_stream as s,joint_updates as u,joint_alternating as alt,joint_stream_cache as cache,fullsupport as fs

def info_reach(pi,codes):
    ns,base,rows,P,S,b=s.layout(len(codes));parents={c:(k,a) for k,n in enumerate(ns) for a,c in enumerate(n['children'])};r=[{},{}];out=[0.]*S;classes=[x//8 for x in codes]
    for k,n in enumerate(ns):
        post=n['street']=='flop';size=len(codes) if post else 169
        for owner in (0,1):
            if k==0:values=[1.]*size
            else:
                p,action=parents[k];parent=ns[p];old=r[owner][p]
                if parent['actor']==owner:
                    count=len(parent['children']);values=[x*pi[base[p]+t*count+action] for t,x in enumerate(old)]
                else:values=old
                if post and parent['street']=='preflop':values=[values[t] for t in classes]
                if not post and parent['street']=='flop':raise ValueError('future-to-preflop transition')
            r[owner][k]=values
        if n['actor']>=0:
            count=len(n['children']);start=base[k]
            for t,v in enumerate(r[n['actor']][k]):out[start+t*count:start+(t+1)*count]=[v]*count
    return out

def mixture(left,right,codes,weight=.25):
    if not 0<=weight<=1:raise ValueError('convex mixture weight')
    layout=s.layout(len(codes))
    if len(left)!=layout[4] or len(right)!=layout[4]:raise ValueError('policy shape')
    for pi in (left,right):
        for start,T,n,k in layout[2]:
            for t in range(T):
                row=pi[start+t*n:start+(t+1)*n]
                if any(not 0<=x<=1 for x in row) or abs(sum(row)-1)>1e-10:raise ValueError('normalized legal policy required')
    a,b=info_reach(left,codes),info_reach(right,codes);out=[0.]*len(left)
    for start,T,n,k in s.layout(len(codes))[2]:
        for t in range(T):
            i=start+t*n;x=(1-weight)*a[i];y=weight*b[i];z=x+y
            out[i:i+n]=[(x*left[i+j]+y*right[i+j])/z for j in range(n)] if z else left[i:i+n]
    return out

class Evaluation(s.Store):
    method='evaluation_only_realization_mixture'
    def __init__(self,path,rows,baseline,candidate,weight=.25):
        if candidate.meta()['epoch']!=5 or candidate.meta()['cursor'] or candidate.meta()['owner']:raise ValueError('complete epoch5 policy required')
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.rows=rows;self.pre=s.layout(1)[3];self.left=baseline;self.right=candidate;self.weight=weight
        self.snapshots=[alt.numeric_digest(x.db) for x in (baseline,candidate)]
        self.identity=fs.digest({'source':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'base':s.source_identity(),'producer':cache.identity(),'snapshots':self.snapshots,'weight':weight,'population':rows,'version':1})
        self.db=sqlite3.connect(path);self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value BLOB NOT NULL)')
        if self.get('meta') is None:
            ns,base,layout,P,S,b=s.layout(1)
            def prefix_only(source):
                pre=s.unpack(source.get('pre'));reg=[0.]*S;avg=[0.]*S;reg[:P]=pre[:P];avg[:P]=pre[P:2*P]
                return s.strategy(reg,avg,layout,True) # Postflop placeholders cannot affect earlier own reach.
            pi=mixture(prefix_only(baseline),prefix_only(candidate),[0],weight)
            with self.db:self.put('meta',json.dumps({'identity':self.identity,'epoch':0,'cursor':0,'representation':'POLICY_ONLY_NOT_CFR_HISTORY'}).encode());self.put('pre',s.pack([0.]*P+pi[:P]+[0.]*(2*P)))
        if self.meta()['identity']!=self.identity:raise ValueError('mixture snapshots/source mismatch')
    def state(self,index,T):
        leftR,leftS=self.left.state(index,T);rightR,rightS=self.right.state(index,T);layout=s.layout(T)[2];lp=s.strategy(leftR,leftS,layout,True);rp=s.strategy(rightR,rightS,layout,True)
        obj,_=cache.read(self.cache_dir,self.rows[index]);pi=mixture(lp,rp,obj['codes'],self.weight);prefix=s.unpack(self.get('pre'))[self.pre:2*self.pre]
        if any(abs(x-y)>1e-12 for x,y in zip(prefix,pi[:self.pre])):raise ValueError('future-board-specific preflop mixture')
        return [0.]*len(pi),pi
    def train(self,*args,**kwargs):raise ValueError('EVALUATION_ONLY,no regret history or training')
    def verify_snapshots(self):
        if self.snapshots!=[alt.numeric_digest(x.db) for x in (self.left,self.right)]:raise ValueError('immutable input policy changed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--seconds',type=int,default=900);a=p.parse_args();a.root.mkdir(parents=True,exist_ok=True);start=time.monotonic();rows=cache.population();left=s.Store(a.baseline,rows);right=alt.Store(a.candidate,rows,a.parent);store=Evaluation(a.root/'evaluation.sqlite',rows,left,right);store.cache_dir=a.cache;lib=s.build(a.root/'native');result=u.evaluate(store,lib,a.cache,seconds=max(0,a.seconds-(time.monotonic()-start)));store.verify_snapshots();result['lambda']=.25;result['representation']='READONLY_POLICY_MIXTURE_NOT_CFR_HISTORY';(a.root/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:result[k] for k in ['coverage','restricted_nashconv_interval_bb','sb_br_gain_bb','bb_br_gain_bb']}),flush=True)
