"""Same chance-board CF method, explicit finite R/S warmstart and heldout stopping."""
import argparse,gc,gzip,json,random,time
from pathlib import Path
import numpy as np
from gto.qualification import fullstreet_solver as f
from gto.qualification.fullstreet_generalize import OLD,boards,load_one,stop
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic

def run(lib,out,pool):
    out=Path(out);pool=Path(pool);out.mkdir(parents=True,exist_ok=True);results=[]
    for seed in (17120101,17120102):
        root=OLD/str(seed);folder=out/str(seed);folder.mkdir(exist_ok=True);trainroot=pool/str(seed);split=json.loads((trainroot/'split.json').read_text());meta=json.loads((root/'policy-selected.json').read_text())
        excluded=sum(split['train']+split['selection']+split['final'],[])+meta['train_boards']+meta['fresh_heldout_boards']+meta['paired_comparison_boards'];sel=boards(seed+600000,1,excluded);final=boards(seed+700000,1,excluded+sum(sel,[]))
        selected=[f.moment(lib,g[0],w) for g,w in zip(sel,f.WEIGHTS)];f.save_blocks(folder/'selection.npz',selected)
        prior=np.load(root/'policy-initial.npz')['pi'].astype(np.float32);q=f.Game(lib,meta['nodes'],selected,prior=prior);del prior;q.restore(root/'selected-checkpoint.npz');start_t=q.t
        identity=dict(meta,generalization_driver_sha256=sha(Path(__file__)),source_py_sha256=sha(Path(f.__file__)),source_cpp_sha256=sha(Path(f.__file__).with_name('fullstreet_core.cc')),binary_sha256=sha(Path(lib._name)),parent_checkpoint_sha256=sha(root/'selected-checkpoint.npz'),parent_state128_sha256=sha(root/'checkpoint.npz'),warmstart='actual16 R/A/visits/t retained as finite initial state; oldprefix NOT drawn from expandedlaw',inherited_regret_epochs=16,sampling_seed=seed+400000,train_boards=sum(split['train'],[]),selection_boards=sum(sel,[]),final_boards=sum(final,[]),chance_scope='finite32board law expanded; old16 finite initialization retained,not unbiased fullhistory')
        rng=random.Random(seed+400000);best=q.measure();bestnc=best['restricted_NC_bb'];curve=[dict(additional_steps=0,selection_NC_bb=bestnc,coverage=f.inspect_coverage(q))];q.save(folder/'best-checkpoint.npz');f.dump_policy(q,folder,identity,'policy-best');start=time.monotonic();reason='MAX128';draws=[]
        for amount in (16,32,64,128):
            while q.t<start_t+amount and time.monotonic()-start<90:
                g=rng.choices(range(4),weights=f.WEIGHTS,k=1)[0];i=rng.randrange(8);draws.append((g,i));q.use_blocks([load_one(trainroot/f'train-{g}-{i}.npz')]);q.step()
            q.use_blocks(selected);m=q.measure();row=dict(additional_steps=q.t-start_t,selection_NC_bb=m['restricted_NC_bb'],seconds=time.monotonic()-start,peak_RSS_bytes=m['peak_RSS_bytes'],coverage=f.inspect_coverage(q));curve.append(row);q.save(folder/'last-checkpoint.npz');atomic(folder/'last-state.json',dict(iterations=q.t,rng_state=rng.getstate(),draws=draws));atomic(folder/'curve.json',dict(curve=curve));print(json.dumps(dict(seed=seed,**{k:v for k,v in row.items() if k!='coverage'})),flush=True)
            if q.t<start_t+amount:reason='TIME_LIMIT';break
            if stop(bestnc,m['restricted_NC_bb']):reason='FIRST_SELECTION_NONIMPROVEMENT';break
            bestnc=m['restricted_NC_bb'];best=m;q.save(folder/'best-checkpoint.npz');f.dump_policy(q,folder,identity,'policy-best')
        q.restore(folder/'best-checkpoint.npz');frozen=json.loads((folder/'policy-best.json').read_text());array_sha=sha(folder/'policy-best.npz');atomic(folder/'freeze.json',dict(iterations=q.t,array_sha256=array_sha,selection_finished=True,reason=reason,final_evaluations=0));cov=f.inspect_coverage(q)
        finalblocks=[f.moment(lib,g[0],w) for g,w in zip(final,f.WEIGHTS)];f.save_blocks(folder/'final.npz',finalblocks);q.use_blocks(finalblocks);new=q.measure();q.restore(root/'selected-checkpoint.npz');old16=q.measure();q.restore(root/'checkpoint.npz');old128=q.measure()
        parentseed=17119201 if seed==17120101 else 17119202;parent=json.loads(gzip.decompress((Path('docs/qa/joint-release-20261119')/str(parentseed)/'policy-final.json.gz').read_bytes()));pi=f.projected_prior(q,parent,False).astype(float);br=[q.evaluate_owner(pi,p) for p in (0,1)]
        rec=dict(seed=seed,selected_iterations=frozen['iterations'],additional_iterations=frozen['iterations']-16,stopped_additional=curve[-1]['additional_steps'],reason=reason,curve=curve,oldjoint_final_NC_bb=sum(x[1] for x in br),old16_final=old16,old128_final=old128,new_final=new,selected_coverage=cov,selection_improvement=bestnc<curve[0]['selection_NC_bb'],seconds=time.monotonic()-start,array_sha256=array_sha,full_native_BR_upper=None,ordinary_registry_admission=False)
        assert array_sha==sha(folder/'policy-best.npz');atomic(folder/'result.json',rec);results.append(rec);atomic(out/'results.json',dict(records=results,formal_acceptance=0,verified_RFI=0,verified_3bet=0));del q,pi,parent,selected,finalblocks;gc.collect()
    return results
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--pool',required=True);p.add_argument('--library',default='/tmp/fullstreet-build/fullstreet.so');a=p.parse_args();run(f.load(a.library),a.out,a.pool)
