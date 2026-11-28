"""Existing sparse policy/CP interface, private-integrated native learning backend."""
import ctypes as C
import importlib.util
import subprocess
import sysconfig
from pathlib import Path
from gto.qualification import sparse_solver as s,public_chance_solver as pcs
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha
from gto.native.training import NativeGame


def build(directory,native_build):
    d=Path(directory);d.mkdir(parents=True,exist_ok=True);n=Path(native_build)
    out=d/('_integrated_qualification'+sysconfig.get_config_var('EXT_SUFFIX'))
    subprocess.run(['c++','-O3','-std=c++20','-fno-fast-math','-ffp-contract=off','-shared','-fPIC',
      str(Path(__file__).with_name('integrated_native.cc')),'-I'+str(n),'-I'+str(n/'headers/pybind11/include'),
      '-I'+sysconfig.get_path('include'),'-o',str(out)],check=True)
    spec=importlib.util.spec_from_file_location('_integrated_qualification',out);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class Solver(s.Solver):
    def __init__(self,module,warm_data,origin,seed,*,extra_support=(),rows=200000,epsilon=.2,stacks=(100,100)):
        self.module=module;self.ranklib=pcs.build('/tmp/integrated-ranks');self.iteration=0;self.checkpoint_hash=None
        data=dict(warm_data,extra_support=list(extra_support));ptr=lambda name:C.cast(getattr(self.ranklib,name),C.c_void_p).value
        self.core=module.Integrated(NativeGame(list(stacks)),data,seed,rows,ptr('pcs_terminal'),ptr('pcs_world'),epsilon)
        self.stats={r:dict(queries=0,untrained=0,warm=0) for r in range(4)}
        self.identity=dict(schema='sparse-private-integrated-v1',origin=origin,seed=seed,rows=rows,epsilon=epsilon,
          game=dict(stacks=list(stacks),bb=2,bba=0,rake=0),extra_support=list(extra_support),
          sources={str(p):sha(p) for p in (Path(__file__),Path(__file__).with_name('integrated_native.cc'),Path(s.__file__).with_name('sparse_native.cc'),Path(pcs.__file__).with_name('public_chance_core.cc'))},
          binary_sha256=sha(Path(module.__file__)),rank_binary_sha256=sha(Path(self.ranklib._name)),
          prior_tables_digest=digest(dict(classes=data['classes'],equity=data['equity'])),
          abstraction='own169 and all causal strategic-prefix signals; exact native public history',
          estimator='uniform public board/exact private pairs/public action outcome sampling with full-support proposal; integrate BEFOREclip',
          formal_profile=False,ordinary_registry_admission=False)
    def step(self,seconds=10.):
        r=self.core.step(seconds);self.iteration=r['iterations'];self.checkpoint_hash=None;return r

    def add_support(self,round,history,actions):
        history=[list(h[:3])+[0,0] for h in history]
        self.core.expand_support(round,history,actions)
        self.identity.setdefault('adaptive_support',[]).append(dict(round=round,history=history,actions=list(actions)))
        self.checkpoint_hash=None


from gto.qualification.multiplayer_joint import SparseJoint
import random
import numpy as np

class Multiplayer(SparseJoint):
    """Existing N external sampler, mean raw chance batch BEFORE CFR+ clip.
    This reduces chance variance, not full private/action enumeration or a
    multiplayer Nash guarantee. Existing lazy average is retained unchanged.
    """
    def __init__(self,*args,chance_batch=2,**kwargs):
        if type(chance_batch) is not int or not 1<=chance_batch<=8:raise ValueError('bounded chance batch')
        super().__init__(*args,**kwargs);self.chance_batch=chance_batch;self.batch=[]
        self.identity.update(chance_batch=chance_batch,integration_source_sha256=sha(Path(__file__)))
    def _draw(self):
        self.batch=[super(Multiplayer,self)._draw() for _ in range(self.chance_batch)]
        return self.batch[0]
    def collect(self,owner,deck,stream,pi,*,audit=False,budget=None):
        if self.chance_batch==1:return super().collect(owner,deck,stream,pi,audit=audit,budget=budget)
        worlds=self.batch if self.batch else [deck];out=dict(grad={},avg={},actions={},owners={},info={},max_average_weight=0.,max_CF_scale=0.)
        for world in worlds:
            part=super().collect(owner,world,random.Random(stream.getrandbits(128)),pi,audit=audit,budget=budget)
            for key in ('grad','avg'):
                for k,v in part[key].items():out[key][k]=out[key].get(k,np.zeros(len(v)))+v/len(worlds)
            for key in ('actions','owners','info'):
                for k,v in part[key].items():
                    if k in out[key] and out[key][k]!=v:raise ValueError('N information/own-parent mismatch')
                    out[key][k]=v
            for key in ('max_average_weight','max_CF_scale'):out[key]=max(out[key],part[key])
        return out
    def step(self):
        if self.chance_batch!=self.identity['chance_batch']:raise ValueError('chance batch changed')
        return super().step()
