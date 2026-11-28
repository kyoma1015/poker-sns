"""Same-game control: existing CSR private-vector CFR, exact vs public-chance sampling.
Fixed884-tree/2board law; NOT a full native quality certificate.
"""
import argparse,gc,json,random,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import public_chance_solver as pcs,integrated_br as br
from gto.qualification.integrated_audit import make,layout,ROOT
from gto.qualification.evaluate import atomic
from gto.qualification.policy import sha

def run(seed,mode):
    folder=ROOT/'same-game'/str(seed)/mode
    if folder.exists() and any(folder.iterdir()):raise FileExistsError('preserve prior control')
    folder.mkdir(parents=True,exist_ok=True);native,m,rules=make(seed,True);nodes,obs=layout(rules);rng=random.Random(17138101);boards=[rng.sample(range(52),5) for _ in range(2)];rows,projection=br.snapshot(native,nodes,obs,boards)
    lib=pcs.build('/tmp/same-game-'+str(seed)+'-'+mode);blocks=[pcs.block(lib,b,.5) for b in boards];q=pcs.Game(lib,nodes,[dict(blocks[0],weight=1.)]);q.use_blocks(blocks);pi=q.policy()
    for b,block in enumerate(blocks):
        for k,n in enumerate(nodes):
            if n['actor']<0:continue
            r=n['round'];codes=np.array(block['codes'])>>(3-r);group=block['public']>>(3-r);at=q.base[k]+(group*(169<<r)+codes)*len(n['children'])
            for j in range(len(n['children'])):pi[at+j]=rows[b][k]['pi'][:,j]
    del native,rows;gc.collect();q.R[:]=pi*1e-6;q.A[:]=pi*1e-3;q.save(folder/'initial.npz');rng=random.Random(seed+17138901);curve=[];pure=0.;reason='CPU_BUDGET'
    for target in (0,4,16,64,256,1024):
        if target>256 and (len(curve)<3 or curve[-1]['restricted_NC_bb']>=curve[0]['restricted_NC_bb']*.8):reason='NO_EXTENSION_TREND';break
        while q.t<target and pure<90:
            if mode=='sample':q.use_blocks([dict(blocks[rng.randrange(2)],weight=1.)])
            else:q.use_blocks(blocks)
            st=time.process_time();q.step();pure+=time.process_time()-st
        q.use_blocks(blocks);metric=q.measure();curve.append(dict(t=q.t,pure_CPU_seconds=pure,**metric));print(json.dumps(dict(seed=seed,mode=mode,**curve[-1])),flush=True)
        q.save(folder/'checkpoint.npz');atomic(folder/'rng.json',dict(t=q.t,state=rng.getstate()))
        if pure>=90:break
    q.use_blocks(blocks);pi=q.policy();rows=[]
    for block in blocks:
        row=[]
        for k,n in enumerate(nodes):
            if n['actor']<0:row.append(None);continue
            r=n['round'];codes=np.array(block['codes'])>>(3-r);group=block['public']>>(3-r);at=q.base[k]+(group*(169<<r)+codes)*len(n['children'])
            row.append(dict(pi=np.array([pi[at+j] for j in range(len(n['children']))]).T,keys=[(k,group,int(c)) for c in codes]))
        rows.append(row)
    independent=br.measure(lib,nodes,boards,rows);physical=br.measure(lib,nodes,boards,rows,physical=True);assert abs(independent['NashConv_bb']-q.measure()['restricted_NC_bb'])<1e-8
    atomic(folder/'result.json',dict(seed=seed,mode=mode,boards=boards,curve=curve,pure_CPU_seconds=pure,independent_same_info=independent,physical_info_same_game=physical,projection=projection,source_sha256=sha(Path(__file__)),peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,stop=reason,full_native_BR_upper=None,formal_acceptance=0))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True);a.add_argument('--mode',choices=['exact','sample'],required=True);x=a.parse_args();run(x.seed,x.mode)
