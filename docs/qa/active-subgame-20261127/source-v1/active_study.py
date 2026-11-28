"""Bounded active/private-vector integration gate; no ordinary GTO admission."""
import argparse,gc,json,random,resource,time
from pathlib import Path
import numpy as np
from gto.qualification import active_chance as ac,public_chance_solver as pcs,integrated_br as br
from gto.qualification import integrated_audit as audit
from gto.qualification.evaluate import atomic
from gto.qualification.policy import sha
ROOT=Path('docs/qa/active-subgame-20261127')

def compact_metric(q):
    m=q.measure();m.pop('action_EV_bb',None);return m

def initialize(q,rows):
    # Every row must have one behavior, independently of sampled private pair.
    seen={}
    for b in range(len(q.blocks)):
        for k,n in enumerate(q.nodes):
            if n['actor']<0:continue
            for h,at in enumerate(q.active[b,k]):
                value=rows[b][k]['pi'][h]
                if int(at) in seen:np.testing.assert_allclose(value,seen[int(at)],atol=1e-12)
                else:seen[int(at)]=value
    for at,value in seen.items():q.R[at:at+len(value)]=value*1e-6;q.A[at:at+len(value)]=value*.001

def run(seed,mode):
    out=ROOT/str(seed)/mode
    if out.exists():raise FileExistsError('preserve previous experiments')
    out.mkdir(parents=True);lib=ac.build('/tmp/active-'+str(seed)+'-'+mode)
    parent=Path('docs/qa/integrated-audit-20261126/same-game')/str(seed)/'exact'
    result=json.loads((parent/'result.json').read_text());boards=result['boards'];blocks=[pcs.block(lib,b,.5) for b in boards]
    native,m,rules=audit.make(seed,True)
    if mode=='refine':
        nodes,obs=audit.layout(rules)
        legacy=pcs.Game(lib,nodes,[dict(blocks[0],weight=1.)]);legacy.use_blocks(blocks);legacy.restore(parent/'checkpoint.npz');pi=legacy.policy();rows=[]
        for block in blocks:
            rr=[]
            for k,n in enumerate(nodes):
                if n['actor']<0:rr.append(None);continue
                r=n['round'];ids=legacy.base[k]+((block['public']>>(3-r))*(169<<r)+(np.asarray(block['codes'])>>(3-r)))*len(n['children'])
                rr.append(dict(pi=np.array([pi[at:at+len(n['children'])] for at in ids])))
            rows.append(rr)
        del legacy;gc.collect()
    else:
        nodes=ac.native_tree(rules,[0,1,6,7,8,9,10,12,16,18,19,102]);obs=br.observations(nodes,rules);rows,projection=br.snapshot(native,nodes,obs,boards)
        atomic(out/'projection.json',projection)
    q=ac.Game(lib,nodes,blocks);initialize(q,rows);del native,rows;gc.collect()
    start=compact_metric(q);priorities=q.priorities();atomic(out/'priorities.json',[dict(priority=g,node=k,coarse=c,fine_cells=t) for g,k,c,t in priorities])
    chosen=[(k,c) for _,k,c,_ in priorities[:64]];refined=ac.Game(lib,nodes,blocks,chosen,parent=q)
    before=br.measure(lib,nodes,boards,q.export());after=br.measure(lib,nodes,boards,refined.export());assert abs(before['EV_bb']-after['EV_bb'])<1e-10
    q=refined;q.t=0;initial=compact_metric(q);q.save(out/'initial.npz');curve=[];pure=0.
    for budget in (30.,90.):
        while pure<budget:
            st=time.process_time();q.step();pure+=time.process_time()-st
        metric=compact_metric(q);curve.append(dict(CPU_seconds=pure,**metric));print(json.dumps(dict(seed=seed,mode=mode,**curve[-1])),flush=True);q.save(out/'checkpoint.npz')
    independent=br.measure(lib,nodes,boards,q.export());fine=ac.Game(lib,nodes,blocks,q.splits,fine=True,parent=q);fine_metric=compact_metric(fine);physical=br.measure(lib,nodes,boards,q.export(),physical=True)
    sources=[Path(__file__),Path(ac.__file__),Path(ac.__file__).with_name('active_chance_core.cc'),Path(pcs.__file__),Path(pcs.__file__).with_name('public_chance_core.cc')]
    identity=dict(seed=seed,mode=mode,boards=boards,nodes=nodes,splits=chosen,parent_sha256=sha(parent/'checkpoint.npz'),sources={str(p):sha(p) for p in sources},binary_sha256=sha(Path(lib._name)),checkpoint_sha256=sha(out/'checkpoint.npz'),initial_sha256=sha(out/'initial.npz'))
    atomic(out/'identity.json',identity)
    expected=q.R.copy();oldA=q.A.copy();q.step();expected=q.R.copy();nextA=q.A.copy();q.restore(out/'checkpoint.npz');q.step();np.testing.assert_array_equal(q.R,expected);np.testing.assert_array_equal(q.A,nextA)
    atomic(out/'result.json',dict(seed=seed,mode=mode,initial_coarse=start,initial_refined=initial,curve=curve,independent=independent,fine_suit_orbit_BR=fine_metric,exact_private_same_board_BR=physical,node_count=len(nodes),active_cells=q.S,refined_parent_cells=len(chosen),CPU_seconds=pure,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,nextstep_exact=True,full_native_BR_upper=None,abstraction_error_full_native=None,formal_acceptance=0,verified_RFI=0,verified_3bet=0))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--mode',choices=['refine','bounded'],required=True);a=p.parse_args();run(a.seed,a.mode)
