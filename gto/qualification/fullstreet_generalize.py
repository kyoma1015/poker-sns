"""Bounded chance-board generalization of the frozen causal fullstreet CFR+."""
import argparse,gc,json,random,time
from pathlib import Path
import numpy as np
from gto.qualification import fullstreet_solver as f
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
OLD=Path('docs/qa/fullstreet-joint-20261120')

def stop(previous,current):return current>=previous-1e-10

def boards(seed,count,excluded=()):
    rng=random.Random(seed);used={tuple(sorted(b[:3])) for b in excluded};out=[]
    for public in f.PUBLIC:
        group=[]
        while len(group)<count:
            b=rng.sample(range(52),5);b[:3]=sorted(b[:3]);key=tuple(b[:3])
            if f.public_code(b)==public and key not in used:used.add(key);group.append(b)
        out.append(group)
    return out

def save_one(path,b):
    np.savez_compressed(path,**{k:np.asarray(v) for k,v in b.items()})
def load_one(path):
    with np.load(path) as d:return {k:d[k].tolist() if k in ('board','codes') else int(d[k]) if k=='public' else float(d[k]) if k=='weight' else d[k].copy() for k in d.files}

def run(lib,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);records=[]
    for seed in (17120101,17120102):
        root=OLD/str(seed);folder=out/str(seed);folder.mkdir(exist_ok=True)
        meta=json.loads((root/'policy-selected.json').read_text());oldtrain=f.load_blocks(root/'train.npz');oldval=f.load_blocks(root/'fresh_heldout.npz');excluded=[b['board'] for b in oldtrain+oldval]+meta['train_boards']+meta['paired_comparison_boards']
        train=boards(seed+100000,8,excluded);sel=boards(seed+200000,1,excluded+sum(train,[]));final=boards(seed+300000,1,excluded+sum(train+sel,[]))
        atomic(folder/'split.json',dict(seed=seed,train=train,selection=sel,final=final,final_policy_selection_allowed=False))
        for g in range(4):
            for i,b in enumerate(train[g]):save_one(folder/f'train-{g}-{i}.npz',f.moment(lib,b,1.))
        selected=[f.moment(lib,g[0],w) for g,w in zip(sel,f.WEIGHTS)];f.save_blocks(folder/'selection.npz',selected)
        # Final boards frozen above, values not computed/read until policy frozen.
        data=np.load(root/'policy-selected.npz');prior=data['pi'].astype(np.float32);del data
        q=f.Game(lib,meta['nodes'],selected,prior=prior);q.restore(root/'selected-checkpoint.npz');old16=q.measure();q.restore(root/'checkpoint.npz');old128=q.measure()
        q.R[:]=np.asarray(prior,dtype=float)*1e-15;q.A[:]=0;q.visits[:]=0;q.t=0;del prior
        identity=dict(meta,source_py_sha256=sha(Path(f.__file__)),source_cpp_sha256=sha(Path(f.__file__).with_name('fullstreet_core.cc')),binary_sha256=sha(Path(lib._name)),generalization_driver_sha256=sha(Path(__file__)),parent_checkpoint_sha256=sha(root/'selected-checkpoint.npz'),parent_state128_sha256=sha(root/'checkpoint.npz'),warmstart='actual16 average; fresh regret/average because chance law expanded',inherited_regret_epochs=0,sampling_seed=seed+400000,train_boards=sum(train,[]),selection_boards=sum(sel,[]),final_boards=sum(final,[]),chance_scope='finite32completeboards,exact disjoint privatepairs,not fullnative')
        rng=random.Random(seed+400000);curve=[];best=q.measure();bestnc=best['restricted_NC_bb'];q.save(folder/'best-checkpoint.npz');f.dump_policy(q,folder,identity,'policy-best');curve.append(dict(step=0,selection_NC_bb=bestnc,coverage=f.inspect_coverage(q)))
        start=time.monotonic();reason='MAX128';draws=[]
        for target in (16,32,64,128):
            while q.t<target and time.monotonic()-start<90:
                g=rng.choices(range(4),weights=f.WEIGHTS,k=1)[0];i=rng.randrange(8);draws.append((g,i));q.use_blocks([load_one(folder/f'train-{g}-{i}.npz')]);q.step()
            q.use_blocks(selected);m=q.measure();cv=f.inspect_coverage(q);atomic(folder/'last-state.json',dict(iterations=q.t,rng_state=rng.getstate(),draws=draws));q.save(folder/'last-checkpoint.npz')
            row=dict(step=q.t,selection_NC_bb=m['restricted_NC_bb'],seconds=time.monotonic()-start,estimated_working_bytes=q.estimate_bytes,peak_RSS_bytes=m['peak_RSS_bytes'],coverage=cv);curve.append(row);print(json.dumps(dict(seed=seed,**{k:v for k,v in row.items() if k!='coverage'})),flush=True)
            atomic(folder/'curve.json',dict(curve=curve,old16=old16,old128=old128))
            if q.t<target:reason='TIME_LIMIT';break
            if stop(bestnc,m['restricted_NC_bb']):reason='FIRST_SELECTION_NONIMPROVEMENT';break
            bestnc=m['restricted_NC_bb'];best=m;q.save(folder/'best-checkpoint.npz');f.dump_policy(q,folder,identity,'policy-best')
        q.restore(folder/'best-checkpoint.npz');frozen=json.loads((folder/'policy-best.json').read_text());frozen_sha=sha(folder/'policy-best.npz');atomic(folder/'freeze.json',dict(iterations=q.t,array_sha256=frozen_sha,selection_finished=True,stop_reason=reason,final_evaluations=0))
        # Independent final finite-game evaluation only AFTER frozen artifact.
        finalblocks=[f.moment(lib,g[0],w) for g,w in zip(final,f.WEIGHTS)];f.save_blocks(folder/'final.npz',finalblocks);q.use_blocks(finalblocks);new=q.measure();cov=f.inspect_coverage(q)
        q.restore(root/'selected-checkpoint.npz');old=q.measure()
        # Oldjoint projection: same FULLSTREET game/public/private map, passive T/R.
        import gzip
        parentseed=17119201 if seed==17120101 else 17119202
        parent=json.loads(gzip.decompress((Path('docs/qa/joint-release-20261119')/str(parentseed)/'policy-final.json.gz').read_bytes()));pi=f.projected_prior(q,parent,False).astype(float);br=[q.evaluate_owner(pi,p) for p in (0,1)]
        rec=dict(seed=seed,selected_iterations=frozen['iterations'],stopped_at=curve[-1]['step'],reason=reason,curve=curve,old16_selection_NC_bb=old16['restricted_NC_bb'],old128_selection_NC_bb=old128['restricted_NC_bb'],oldjoint_final_NC_bb=sum(x[1] for x in br),old16_final=old,new_final=new,selected_coverage=cov,selection_improvement=bestnc<curve[0]['selection_NC_bb'],seconds=time.monotonic()-start,policy_array_sha256=frozen_sha,full_native_BR_upper=None,ordinary_registry_admission=False)
        assert frozen_sha==sha(folder/'policy-best.npz');atomic(folder/'result.json',rec);records.append(rec);atomic(out/'results.json',dict(records=records,formal_acceptance=0,verified_RFI=0,verified_3bet=0));del q,pi,parent,finalblocks,oldtrain,oldval,selected;gc.collect()
    return records
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--library',default='/tmp/fullstreet-build/fullstreet.so');p.add_argument('--out',required=True);a=p.parse_args();run(f.load(a.library),a.out)
