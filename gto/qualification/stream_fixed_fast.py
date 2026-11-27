"""Fast exact-layout counterpart of the fixed13-board control, no model switch."""
import argparse,gc,hashlib,json,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import stream_study as st,stream_sampling as ss,stream_chance as sc,stream_br,active_resume,active_chance as ac
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
from gto.qualification.build import load

def run(seed):
    folder=st.ROOT/str(seed)/'fixed-fast'
    if folder.exists():raise FileExistsError('preserve fixed control')
    folder.mkdir(parents=True);rules,_=load('/tmp/native-qualification');p=st.PARENT/str(seed)/'bounded';parent,oldid=active_resume.restore(p,'/tmp/fixed-parent-'+str(seed));parent.step();proof=np.load(p/'nextstep-proof.npz')
    for name in ('R','A','visits'):np.testing.assert_array_equal(getattr(parent,name),proof[name])
    parent.restore(p/'checkpoint.npz');nodes=sc.expanded_tree(rules,[0,1,6,7,8,9,10,12,16,18,19,102],[23]);mapping=sc.node_map(parent.nodes,nodes);splits=set()
    for oldnode,code in parent.splits:
        k=mapping[oldnode];r=nodes[k]['round'];h=(code%(169<<r))>>r
        for public in (0,1,3,7):
            for flags in range(1<<r):splits.add((k,(public>>(3-r))*(169<<r)+(h<<r)+flags))
    bs=sc.catalog(parent.lib,17150101+seed);q=ss.Game(parent.lib,nodes,bs,splits);warm=q.initialize(parent,mapping);q.prior=q.prior.astype(np.float32);del parent;gc.collect();q.save(folder/'initial.npz')
    files=[Path(__file__),Path(st.__file__),Path(ss.__file__),Path(ss.__file__).with_name('stream_index.py'),Path(ss.__file__).with_name('stream_features.py'),Path(ss.__file__).with_name('stream_feature_core.cc'),Path(sc.__file__),Path(stream_br.__file__),Path(ac.__file__),Path(ac.__file__).with_name('active_chance_core.cc')]
    identity=dict(schema='fixed13-fast-equivalent-control',seed=seed,nodes=nodes,splits=sorted(splits),blocks=[{k:b[k] for k in ('board','weight','stratum')} for b in bs],sources={str(p):sha(p) for p in files},binary_sha256=sha(Path(q.lib._name)),initial_checkpoint=str(folder/'initial.npz'),initial_sha256=sha(folder/'initial.npz'),parent_sha256=oldid['checkpoint_sha256'])
    pure=0.;curve=[]
    for budget in (0.,90.,180.,360.,720.):
        while pure<budget:
            tick=time.process_time();q.step();pure+=time.process_time()-tick
        nc=stream_br.finite_measure(q);target=folder/('t'+str(int(budget)));st.checkpoint(q,target,identity);record=dict(CPU_seconds=pure,t=q.t,NC=nc,checkpoint=str(target));curve.append(record);atomic(folder/'curve.json',dict(curve=curve));print(json.dumps(dict(seed=seed,budget=budget,t=q.t,CPU=pure,NC=nc['NashConv_bb'],RSS=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)),flush=True)
    fine=stream_br.finite_measure(q,physical=True);atomic(folder/'result.json',dict(seed=seed,curve=curve,fine_last=fine,CPU=pure,warm=warm,formal_pass=0))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);run(a.parse_args().seed)
