"""Finite locked research runner; never a daemon or ordinary GTO publisher."""
import argparse,fcntl,json,time
from pathlib import Path
from gto.abstract import joint_training as t,joint_stream as s,joint_stream_cache as cache

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backend',choices=('legacy','vector'),required=True)
    p.add_argument('--overlay',type=Path,required=True)
    p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--seconds',type=int,required=True)
    p.add_argument('--epochs',type=int,default=1)
    p.add_argument('--max-blocks',type=int,default=3510)
    p.add_argument('--evaluate',action='store_true')
    a=p.parse_args()
    if a.seconds<0 or a.epochs<1 or a.max_blocks<0:p.error('nonnegative finite budgets and positive epochs required')
    a.overlay.parent.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    with Path(str(a.overlay)+'.operator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lib=t.build(a.overlay.parent/(a.overlay.name+'.'+a.backend+'-native'),a.backend)
        store=t.Store(a.overlay,cache.population(),a.parent,a.backend)
        remaining=lambda:max(0.,a.seconds-(time.monotonic()-start))
        try:
            result={'training':store.train(lib,a.cache,epochs=a.epochs,max_blocks=a.max_blocks,seconds=remaining()),'normal_GTO_added':0,'formal_acceptance':[0,12]}
            if a.evaluate:
                if store.meta()['cursor'] or store.meta()['owner']:result['evaluation']='BLOCKED: incomplete owner sweeps, resume training first'
                else:result['evaluation']=t.evaluate(store,s.build(a.overlay.parent/(a.overlay.name+'.independent-br')),a.cache,seconds=remaining())
            print(json.dumps(result,sort_keys=True),flush=True)
        finally:store.close()

if __name__=='__main__':main()
