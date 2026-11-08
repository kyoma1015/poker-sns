"""Finite supervised population run. No daemon, no policy selection or UI admission."""
import argparse,json,time,fcntl
from pathlib import Path
from gto.abstract import joint_stream as s,joint_stream_cache as c,model,fullsupport as fs,suit_exact as old,street_tree as st
from gto.abstract.factorial_transfer import category

def frozen(store,cache_dir):
    """Lift immutable frozen small policy onto the identical full-information game."""
    if store.meta()['epoch'] or store.meta()['cursor']:raise ValueError('fresh readonly baseline store required')
    fixed=json.loads((old.ROOT/'results.json').read_text())['complete_preflop_policies']['learned_small'];teacher=json.loads(old.old.TEACHER.read_text());ns,mapping,leaves=s.tree();inverse={new:old for old,new in mapping.items()};starts=dict(leaves);reach={r['leaf_index']:r for r in fs.leaves(fixed)};offsets={}
    for leaf,r in reach.items():
        if not r['remaining_stack_bb']:continue
        off=[0]
        for n in st.tree(r['post_call_pot_bb'],r['remaining_stack_bb'],r['hero_actor'],(1/3,.5,.75))['nodes']:off.append(off[-1]+8*len(n['children']))
        offsets[leaf]=off
    prefix=[0.]*(4*store.pre)
    for start,types,n,k in s.layout(1)[2]:
        if start>=store.pre:continue
        for t in range(169):
            for a in range(n):prefix[store.pre+start+t*n+a]=fixed[(inverse[k]*3+a)*169+t]
    with store.db:store.put('pre',s.pack(prefix))
    for i,row in enumerate(store.rows):
        obj,_=c.read(cache_dir,row);codes=obj['codes'];ns,base,layout,P,S,b=s.layout(len(codes));sums=[0.]*(S-P)
        for start,T,n,k in layout:
            if start<P:continue
            leaf=ns[k]['preflop_leaf'];coarse=teacher['profiles']['learned_small'][str(leaf)+'|'+category(row['representative'])];off=offsets[leaf][k-starts[leaf]]
            for t,code in enumerate(codes):
                vals=coarse[off+(code%8)*n:off+(code%8+1)*n]
                if abs(sum(vals)-1)>1e-10:raise ValueError('frozen action tree mismatch')
                sums[start-P+t*n:start-P+(t+1)*n]=vals
        with store.db:store.put('b:'+str(i),s.pack([0.]*(S-P)+sums))
    with store.db:store.put('baseline:ready',b'1')

def run_locked(root,cache_dir,seconds=3600):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);start=time.monotonic();lib=s.build(root/'native');rows=c.population();store=s.Store(root/'learned.sqlite',rows);baseline=s.Store(root/'frozen.sqlite',rows)
    if not baseline.get('baseline:ready'):
        try:frozen(baseline,cache_dir)
        except FileNotFoundError:return {'status':'WAITING_CACHE','phase':'baseline_initialize'}
    if not (root/'frozen-evaluation.json').exists():
        result=s.evaluate(baseline,lib,cache_dir,seconds=max(0,seconds-(time.monotonic()-start)));(root/'frozen-evaluation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
        print(json.dumps({'phase':'frozen','orbits':result['evaluated_orbits'],'nashconv':result['restricted_nashconv_interval_bb']}),flush=True)
        if result['coverage']<1:return {'status':'BUDGET','phase':'baseline_evaluate'}
    for stop in (1,2,4):
        if (root/('epoch'+str(stop)+'.json')).exists():continue
        remaining=seconds-(time.monotonic()-start)
        if remaining<=0:return {'status':'BUDGET','meta':store.meta()}
        if store.meta()['epoch']<stop:
            result=store.train(lib,cache_dir,epochs=stop-store.meta()['epoch'],max_blocks=1755*stop,seconds=remaining)
            print(json.dumps({'phase':'train','result':result}),flush=True)
            if store.meta()['epoch']<stop:return {'status':'BUDGET_OR_CACHE','meta':store.meta()}
        result=s.evaluate(store,lib,cache_dir,seconds=max(0,seconds-(time.monotonic()-start)))
        if result['coverage']<1:return {'status':'BUDGET','phase':'evaluate','epoch':stop}
        (root/('epoch'+str(stop)+'.json')).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
        print(json.dumps({'phase':'evaluate','epoch':stop,'nashconv':result['restricted_nashconv_interval_bb'],'sb_ev':result['sb_ev_interval_bb']}),flush=True)
    return {'status':'COMPLETE_REGISTERED_BUDGET','meta':store.meta(),'elapsed_seconds':time.monotonic()-start,'ordinary_GTO':False}

def run(root,cache_dir,seconds=3600):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    # One trainer/evaluator per checkpoint family. Cache generation is separate.
    with (root/'operator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return run_locked(root,cache_dir,seconds)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--seconds',type=int,default=3600);a=p.parse_args();print(json.dumps(run(a.root,a.cache,a.seconds)),flush=True)
