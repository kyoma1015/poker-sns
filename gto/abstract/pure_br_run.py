"""Finite pure-policy qualification with independent original-world evaluation."""
import argparse,fcntl,hashlib,heapq,json,math,shutil,sqlite3,time,zlib
from pathlib import Path
from gto.abstract import pure_br as p,joint_stream as s,joint_stream_cache as cache,joint_updates as u,joint_realization as mix,fullsupport as fs,model

def hash_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while b:=f.read(4*1024**2):h.update(b)
    return h.hexdigest()

class Run:
    def __init__(self,root,temp,baseline,rows=None):
        self.root=Path(root);self.temp=Path(temp);self.root.mkdir(parents=True,exist_ok=True);self.temp.mkdir(parents=True,exist_ok=True)
        self.rows=cache.population() if rows is None else rows;self.source=p.Frozen(baseline,self.rows);self.P=self.source.pre;self.L=2*len(model.tree())*169
        self.identity=fs.digest({'source_numeric':self.source.numeric_digest(),'source_meta':self.source.meta(),'population':self.rows,'game':s.tree()[0],'producer':cache.identity(),'code':{x.name:hash_file(x) for x in (Path(__file__),Path(p.__file__),Path(p.__file__).with_suffix('.cc'))},'tie':'first_legal','version':1})
        self.db=sqlite3.connect(self.root/'policy.sqlite');self.db.execute('pragma journal_mode=WAL');self.db.execute('pragma synchronous=FULL');self.db.execute('create table if not exists state(key text primary key,value blob not null)')
        if self.get('meta') is None:
            with self.db:self.put('meta',json.dumps({'identity':self.identity,'phase':'extract','cursor':0,'extract_started':time.time(),'verify_started':None}).encode());self.put('sum',s.pack([0.]*(2*self.L+2*self.P+2)))
        if self.meta()['identity']!=self.identity:raise ValueError('policy/source/game/chance mismatch')
    def get(self,key):
        r=self.db.execute('select value from state where key=?',(key,)).fetchone();return None if r is None else zlib.decompress(r[0])
    def put(self,key,value):self.db.execute('insert into state values (?,?) on conflict(key) do update set value=excluded.value',(key,zlib.compress(value,1)))
    def meta(self):return json.loads(self.get('meta'))
    def guard(self):
        if min(shutil.disk_usage(self.root).free,shutil.disk_usage(self.temp).free)<2*1024**3:raise ValueError('2GiB free reserve')
        if sum(x.stat().st_size for x in self.root.glob('*.sqlite*'))>64*1024**2:raise ValueError('64MiB compact policy budget')
        if sum(x.stat().st_size for x in self.temp.glob('*.bin'))>768*1024**2:raise ValueError('768MiB temporary diagnostic budget')
    def extract(self,lib,old,cache_dir,max_blocks=1755):
        meta=self.meta();total=s.unpack(self.get('sum'));mass=sum(x['multiplicity'] for x in self.rows);done=0;maximum=0.
        while meta['cursor']<len(self.rows) and done<max_blocks and time.time()-meta['extract_started']<1800:
            self.guard();i=meta['cursor'];row=self.rows[i];obj,values=cache.read(cache_dir,row);T=len(obj['codes']);reg,avg=self.source.state(i,T)
            out=s.block(lib,obj,values,reg,avg,True);choices=lib.choices.copy();den=lib.cf_mass.copy();post=p.post_bytes(choices,T)
            reference=s.block(old,obj,values,reg,avg,True);error=max(abs(a-b) for field in ('leaf','metrics') for a,b in zip(out[field],reference[field]));maximum=max(maximum,error)
            if error>1e-8:raise ValueError('independent originalBR output mismatch')
            weight=row['multiplicity']/mass;diag=[]
            for start,types,n,k in out['rows']:
                if start>=self.P:
                    for typ in range(types):
                        at=start+typ*n+choices[start+typ*n];diag.extend((out['grad'][at],den[at]))
            raw=zlib.compress(s.pack(diag),1);file=self.temp/(str(i)+'.bin');tmp=file.with_suffix('.pending');tmp.write_bytes(raw);tmp.replace(file)
            add=out['leaf']+reference['leaf']+out['grad'][:self.P]+out['action_den']+out['metrics'][:1]+reference['metrics'][:1]
            for j,x in enumerate(add):total[j]+=weight*x
            meta['cursor']+=1;meta['max_native_error']=max(meta.get('max_native_error',0),maximum)
            with self.db:self.put('b:'+str(i),post);self.put('d:'+str(i),hashlib.sha256(raw).digest());self.put('sum',s.pack(total));self.put('meta',json.dumps(meta).encode())
            done+=1
            if done%64==0:print(json.dumps({'phase':'extract','blocks':meta['cursor'],'seconds':time.time()-meta['extract_started']}),flush=True)
        if meta['cursor']==len(self.rows):
            prefix,values=p.prefix_bytes(total[:self.L]);independent=s.collapse(total[self.L:2*self.L]);meta.update(phase='verify',cursor=0,verify_started=time.time());stats={'ev':[0.,0.],'bins':{},'positive':[0.,0.],'negative':[0.,0.],'top_positive':[],'top_negative':[]}
            obj,_=cache.read(cache_dir,self.rows[0]);pure=p.pure_policy(prefix,self.get('b:0'),len(obj['codes']));reach=mix.info_reach(pure,obj['codes']);ns,_,rows,P,_,_=s.layout(len(obj['codes']));pos=0
            for start,types,n,k in rows:
                if start<P:
                    for typ in range(types):
                        a=prefix[pos];pos+=1;at=start+typ*n+a;own=reach[at];self.record(stats,ns,k,typ,a,own*total[2*self.L+at],own*total[2*self.L+self.P+at],None)
            with self.db:self.put('prefix',prefix);self.put('oracle',s.pack(values+independent+total[-2:]));self.put('verify',json.dumps(stats,separators=(',',':')).encode());self.put('meta',json.dumps(meta).encode())
        return self.meta()
    def record(self,stats,ns,k,hand,a,gain,reach,flop):
        owner=ns[k]['actor'];key=f'{owner}/{k}/{hand}/{a}';v=stats['bins'].setdefault(key,[0.,0.]);v[0]+=gain;v[1]+=reach
        stats['positive' if gain>=0 else 'negative'][owner]+=gain
        entry={'owner':owner,'node':k,'hand':model.CLASSES[hand],'action_index':a,'gain_bb':gain,'reach':reach,'flop':flop}
        key2='top_positive' if gain>=0 else 'top_negative';stats[key2].append(entry);stats[key2]=sorted(stats[key2],key=lambda r:abs(r['gain_bb']),reverse=True)[:50]
    def verify(self,utility,cache_dir,max_blocks=1755):
        meta=self.meta()
        if meta['phase']!='verify':raise ValueError('complete population/globalprepolicy required')
        stats=json.loads(self.get('verify'));prefix=self.get('prefix');mass=sum(r['multiplicity'] for r in self.rows);done=0
        while meta['cursor']<len(self.rows) and done<max_blocks and time.time()-meta['verify_started']<2400:
            self.guard();i=meta['cursor'];row=self.rows[i];obj,values=cache.read(cache_dir,row);T=len(obj['codes']);reg,avg=self.source.state(i,T);pure=p.pure_policy(prefix,self.get('b:'+str(i)),T);baseline=s.strategy(reg,avg,s.layout(T)[2],True);weight=row['multiplicity']/mass
            for owner in (0,1):
                policy=p.hybrid(baseline,pure,T,owner);r=s.block(utility,obj,values,[0.]*len(policy),policy,True);stats['ev'][owner]+=weight*r['metrics'][0]
            raw=(self.temp/(str(i)+'.bin')).read_bytes()
            if hashlib.sha256(raw).digest()!=self.get('d:'+str(i)):raise ValueError('temporary diagnostics/source mismatch')
            diag=s.unpack(zlib.decompress(raw));reach=mix.info_reach(pure,obj['codes']);ns,_,rows,P,_,_=s.layout(T);pos=which=0;post=self.get('b:'+str(i))
            for start,types,n,k in rows:
                if start>=P:
                    for typ in range(types):
                        a=post[which];which+=1;own=reach[start+typ*n+a];g,d=diag[pos:pos+2];pos+=2;self.record(stats,ns,k,obj['codes'][typ]//8,a,weight*own*g,weight*own*d,row['representative'])
            if pos!=len(diag):raise ValueError('diagnostic shape')
            meta['cursor']+=1;done+=1
            if done%16==0 or meta['cursor']==len(self.rows):
                with self.db:self.put('verify',json.dumps(stats,separators=(',',':')).encode());self.put('meta',json.dumps(meta).encode())
            if done%64==0:print(json.dumps({'phase':'verify','blocks':meta['cursor'],'seconds':time.time()-meta['verify_started']}),flush=True)
        with self.db:self.put('verify',json.dumps(stats,separators=(',',':')).encode());self.put('meta',json.dumps(meta).encode())
        return self.result()
    def result(self):
        meta=self.meta();complete=meta['phase']=='verify' and meta['cursor']==len(self.rows)
        out={'complete':complete,'meta':meta,'population_orbits':len(self.rows),'normal_GTO_added':0,'formal_acceptance':[0,12],'external_GTO':'NOT PERFORMED','real_game_error':'UNKNOWN'}
        if not complete:return out
        values=s.unpack(self.get('oracle'));stats=json.loads(self.get('verify'));base=values[-2];reference_base=values[-1];realized=[stats['ev'][0]-reference_base,reference_base-stats['ev'][1]];expected=[values[2]-reference_base,values[3]+reference_base];attributed=[stats['positive'][o]+stats['negative'][o] for o in (0,1)]
        errors=[abs(a-b) for a,b in zip(realized,expected)]+[abs(a-b) for a,b in zip(realized,attributed)]+[abs(values[0]-values[2]),abs(values[1]-values[3]),abs(base-reference_base)]
        ns=s.tree()[0];drivers=[]
        for key,(gain,reach) in stats['bins'].items():
            owner,k,h,a=map(int,key.split('/'));node=ns[k];drivers.append({'owner':owner,'node':k,'street':node['street'],'hand':model.CLASSES[h],'history':node.get('history',[]),'preflop_leaf':node.get('preflop_leaf'),'action':node['actions'][a],'root_gain_bb':gain,'root_reach':reach})
        out.update(oracle_br_values_bb=values[:2],independent_br_values_bb=values[2:4],baseline_sb_ev_bb=reference_base,realized_br_gains_bb=realized,independent_br_gains_bb=expected,attributed_gains_bb=attributed,max_agreement_error_bb=max(errors),pass_tolerance=max(errors)<=1e-8,nashconv_bb=sum(expected),top_drivers=sorted(drivers,key=lambda x:x['root_gain_bb'],reverse=True)[:40],top_negative_drivers=sorted(drivers,key=lambda x:x['root_gain_bb'])[:20],top_information_sets=stats['top_positive'],negative_information_sets=stats['top_negative'],representation='PURE_POLICY_ONLY_NOT_CFR_HISTORY')
        return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--temporary',type=Path,required=True);args=parser.parse_args();args.root.mkdir(exist_ok=True)
    with (args.root/'operator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);run=Run(args.root,args.temporary,'/workspace/joint-stream-run/frozen.sqlite');lib=p.build(args.root/'extractor');old=s.build(args.root/'independent');utility=u.build(args.root/'utility')
        if run.meta()['phase']=='extract':run.extract(lib,old,'/workspace/joint-stream-cache')
        result=run.verify(utility,'/workspace/joint-stream-cache') if run.meta()['phase']=='verify' else run.result();(args.root/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if not k.startswith('top') and k not in ('negative_information_sets',)}),flush=True)
if __name__=='__main__':main()
