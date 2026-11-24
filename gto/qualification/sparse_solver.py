"""Sparse native joint external sampling with generic exact-history size handling."""
import argparse,gzip,hashlib,importlib.util,json,os,resource,subprocess,sys,sysconfig,time
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification import fullstreet_solver as old
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame
ROOT=Path(__file__).resolve().parents[2]
PARENT=ROOT/'docs/qa/fullstreet-generalization-20261121/corrected'

def build(directory,native_build):
    d=Path(directory);d.mkdir(parents=True,exist_ok=True);n=Path(native_build);out=d/('_sparse_qualification'+sysconfig.get_config_var('EXT_SUFFIX'))
    cmd=['c++','-O3','-std=c++20','-fno-fast-math','-ffp-contract=off','-shared','-fPIC',str(Path(__file__).with_name('sparse_native.cc')),'-I'+str(n),'-I'+str(n/'headers/pybind11/include'),'-I'+sysconfig.get_path('include'),'-o',str(out)]
    subprocess.run(cmd,check=True);return load(out)

def load(path):
    spec=importlib.util.spec_from_file_location('_sparse_qualification',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def warm(module,seed):
    folder=PARENT/str(seed);meta=json.loads((folder/'policy-best.json').read_text());array=folder/'policy-best.npz'
    if sha(array)!=meta['array_sha256']:raise ValueError('parent array hash')
    data=np.load(array);pi=data['pi'];support=(data['average_mass']>0).astype(np.uint8);nodes=[]
    cp=np.load(folder/'best-checkpoint.npz');R=cp['R'];A=cp['A']
    for k,n in enumerate(meta['nodes']):
        if n['actor']<0:continue
        at=meta['bases'][k];count=169*len(n['children']) if n['round']==0 else 0
        nodes.append(dict(base=at,round=n['round'],actions=n['native_actions'],history=[list(h[:3])+[0,0] for h in n['native_prefix']],R=R[at:at+count].tolist(),A=A[at:at+count].tolist()))
    del R,A,cp,data
    classes=np.full(2704,-1,dtype=np.int32);hands=[]
    for c,group in enumerate(model.classes()):
        hands.append(list(group[0]))
        for a,b in group:classes[a*52+b]=classes[b*52+a]=c
    eq=module.pre_equities(hands,128,17124001)
    return dict(pi=pi,support=support,classes=classes.tolist(),equity=eq,nodes=nodes),dict(parent_seed=seed,parent_checkpoint_sha256=sha(folder/'best-checkpoint.npz'),parent_policy_array_sha256=sha(array),parent_iterations=meta['iterations'],warm='matching preflop finite R/A; postflop average behavior; not new-game prefix history')

class Solver:
    def __init__(self,module,warm_data,origin,seed,*,full=False,refined=True,rows=400000,node_cap=1000000):
        self.module=module;self.rules=None;self.iteration=0;self.core=module.Sparse(NativeGame([100,100]),warm_data,seed,full,refined,rows,node_cap);self.stats={r:dict(queries=0,untrained=0,warm=0) for r in range(4)}
        self.identity=dict(schema='sparse-native-external-v1',origin=origin,seed=seed,all_native_actions=full,refined=refined,rows=rows,node_cap=node_cap,game=dict(stacks=[100,100],bb=2,bba=0,rake=0),sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),Path(__file__).with_name('sparse_native.cc'),Path(__file__).with_name('fullstreet_core.cc'),ROOT/'handoff/gto/g12_next/g11_native_state.h')},binary_sha256=sha(Path(module.__file__)),formal_profile=False,ordinary_registry_admission=False)
        self.identity['prior_tables_digest']=digest(dict(classes=warm_data['classes'],equity=warm_data['equity']))
        self.checkpoint_hash=None
    def step(self,seconds=2.):
        r=self.core.step(seconds);self.iteration=r['iterations'];self.checkpoint_hash=None;return r
    def row(self,o,average=False):
        if len(o.live)!=2 or any(o.live[p]+o.remaining[p]!=100 for p in (0,1)) or any(o.dead):raise ValueError('HU50 zeroante research only')
        if o.actor not in (0,1) or o.round not in (0,1,2,3) or len(o.own)!=2 or any(type(c) is not int or not 0<=c<52 for c in o.own+o.board) or len(set(o.own+o.board))!=len(o.own+o.board) or len(o.board)!=(0,3,4,5)[o.round]:raise ValueError('own/public cards')
        r=self.core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,True)
        self.stats[o.round]['queries']+=1;self.stats[o.round]['untrained']+=not r['trained'];self.stats[o.round]['warm']+=r['warm']
        p=r['probabilities']
        if abs(sum(p)-1)>1e-10 or any(x<0 for x in p):raise ValueError('normalized legal sparse row')
        return p
    def save(self,folder):
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);raw=folder/'checkpoint.bin';tmp=folder/'checkpoint.tmp.bin';self.core.save(str(tmp),digest(self.identity));tmp.replace(raw);self.checkpoint_hash=sha(raw)
        atomic(folder/'checkpoint.json',dict(identity=self.identity,sha256=self.checkpoint_hash,iterations=self.iteration,stats=self.core.stats(),policy_digest=self.policy_digest,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    def restore(self,folder):
        folder=Path(folder);d=json.loads((folder/'checkpoint.json').read_text());p=folder/'checkpoint.bin'
        if d['identity']!=self.identity or sha(p)!=d['sha256']:raise ValueError('sparse source/game/checkpoint identity')
        self.core.restore(str(p),digest(self.identity));self.iteration=d['iterations'];self.checkpoint_hash=d['sha256']
    @property
    def policy_digest(self):
        if self.checkpoint_hash is None:raise ValueError('freeze sparse checkpoint before independent evaluation')
        return digest(dict(identity=self.identity,checkpoint_sha256=self.checkpoint_hash))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--native-build',required=True);a=p.parse_args();build(a.build,a.native_build)
