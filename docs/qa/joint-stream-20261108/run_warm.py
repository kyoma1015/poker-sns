"""Explicit bounded warm optimization experiment; source is part of QA protocol."""
import json,time,fcntl
from pathlib import Path
from gto.abstract import joint_stream as s,joint_stream_cache as c

def run(root=Path('/workspace/joint-stream-warm'),seconds=3600):
    root.mkdir(exist_ok=True,parents=True);start=time.monotonic();rows=c.population();warm=s.Store(root/'learned.sqlite',rows);frozen=s.Store(Path('/workspace/joint-stream-run/frozen.sqlite'),rows);epsilon=1e-15
    with (root/'operator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not warm.get('warm:ready'):
            cursor=int(warm.get('warm:cursor') or b'0');budget=float(warm.get('warm:prior-budget') or b'0')
            if cursor==0:
                original=s.unpack(frozen.get('pre'));prefix=[0.]*(4*warm.pre)
                for i,p in enumerate(original[warm.pre:2*warm.pre]):prefix[i]=epsilon*p
                budget=sum(prefix)
                with warm.db:warm.put('pre',s.pack(prefix))
            for i in range(cursor,len(rows)):
                if time.monotonic()-start>=seconds:return {'status':'BUDGET_INIT','cursor':i}
                previous=s.unpack(frozen.get('b:'+str(i)));n=len(previous)//2;reg=[epsilon*p for p in previous[n:]];budget+=sum(reg)
                with warm.db:
                    warm.put('b:'+str(i),s.pack(reg+[0.]*n));warm.put('warm:cursor',str(i+1).encode());warm.put('warm:prior-budget',repr(budget).encode())
            with warm.db:warm.put('warm:ready',b'1');warm.put('warm:epsilon',repr(epsilon).encode())
        lib=s.build(root/'native')
        if warm.meta()['epoch']<2:
            out=warm.train(lib,'/workspace/joint-stream-cache',epochs=2-warm.meta()['epoch'],max_blocks=3510,seconds=max(0,seconds-(time.monotonic()-start)))
            print(json.dumps(out),flush=True)
            if warm.meta()['epoch']<2:return {'status':'BUDGET_TRAIN','meta':warm.meta()}
        out=s.evaluate(warm,lib,'/workspace/joint-stream-cache',seconds=max(0,seconds-(time.monotonic()-start)))
        out['initialization']='frozen small positive-regret prior1e-15;zero average sums';out['positive_prior_budget_bb']=float(warm.get('warm:prior-budget'))
        (root/'epoch2.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
        return {k:v for k,v in out.items() if k not in ('preflop_frequency','preflop_action_ev_bb','preflop_layout')}

if __name__=='__main__':print(json.dumps(run()),flush=True)
