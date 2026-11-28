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
    def __init__(self,module,warm_data,origin,seed,*,extra_support=(),rows=200000,epsilon=.2,stacks=(100,100),root_integration=True,coarse=False,signed_regret=False,linear_average=True):
        self.module=module;self.ranklib=pcs.build('/tmp/integrated-ranks');self.iteration=0;self.checkpoint_hash=None
        data=dict(warm_data,extra_support=list(extra_support),coarse=coarse,signed_regret=signed_regret,linear_average=linear_average);ptr=lambda name:C.cast(getattr(self.ranklib,name),C.c_void_p).value
        self.core=module.Integrated(NativeGame(list(stacks)),data,seed,rows,ptr('pcs_terminal'),ptr('pcs_world'),epsilon,root_integration)
        self.stats={r:dict(queries=0,untrained=0,warm=0) for r in range(4)}
        self.identity=dict(schema='sparse-private-integrated-v2',root_integration=root_integration,coarse=coarse,signed_regret=signed_regret,linear_average=linear_average,origin=origin,seed=seed,rows=rows,epsilon=epsilon,
          game=dict(stacks=list(stacks),bb=2,bba=0,rake=0),extra_support=list(extra_support),
          sources={str(p):sha(p) for p in (Path(__file__),Path(__file__).with_name('integrated_native.cc'),Path(s.__file__).with_name('sparse_native.cc'),Path(pcs.__file__).with_name('public_chance_core.cc'))},
          binary_sha256=sha(Path(module.__file__)),rank_binary_sha256=sha(Path(self.ranklib._name)),
          prior_tables_digest=digest(dict(classes=data['classes'],equity=data['equity'])),
          abstraction='own169 and all causal strategic-prefix signals; exact native public history',
          estimator='uniform public board/exact private pairs/root public support integration; future action importance sampling; integrate BEFOREclip',
          formal_profile=False,ordinary_registry_admission=False)
    def step(self,seconds=10.):
        r=self.core.step(seconds);self.iteration=r['iterations'];self.checkpoint_hash=None;return r

    def rebase_warm(self):
        """New-game behavioral warm start, not resumed old regret/average history."""
        self.core.rebase_warm();self.checkpoint_hash=None
        self.identity['warm_initialization']='same average behavior, uniform per-row pseudomass R1e-6/A1e-3; old checkpoints intact'

    def add_support(self,round,history,actions):
        history=[list(h[:3])+[0,0] for h in history]
        self.core.expand_support(round,history,actions)
        self.identity.setdefault('adaptive_support',[]).append(dict(round=round,history=history,actions=list(actions)))
        self.checkpoint_hash=None

    def import_preflop_checkpoint(self,folder,rules):
        """Exact old preflop R/A and ALL stored public support, not intersection."""
        import gzip,json,struct,tempfile
        from gto.abstract import model
        from gto.qualification.native_mccfr import betting
        from gto.qualification.public_response import observe
        from gto.qualification.policy import act
        folder=Path(folder);meta=json.loads((folder/'checkpoint.json').read_text())
        if (folder/'checkpoint.bin.zst').exists():
            raw=subprocess.check_output(['zstd','-d','-q','-c',str(folder/'checkpoint.bin.zst')])
        else:raw=gzip.decompress((folder/'checkpoint.bin.gz').read_bytes())
        import hashlib
        if hashlib.sha256(raw).hexdigest()!=meta['sha256']:raise ValueError('inherited checkpoint digest')
        for path,pin in meta['identity']['sources'].items():
            if sha(Path(path))!=pin:raise ValueError('old sparse source identity')
        if self.identity['prior_tables_digest']!=meta['identity']['prior_tables_digest']:raise ValueError('old sparse prior identity')
        at=0
        def number():
            nonlocal at
            v=struct.unpack_from('=Q',raw,at)[0];at+=8;return v
        def blob():
            nonlocal at
            n=number();v=raw[at:at+n];at+=n;return v
        if blob()!=b'sparse-native-v1' or blob().decode()!=digest(meta['identity']):raise ValueError('inherited checkpoint identity')
        oldt=number();blob();count=number();pre=[];support={}
        for _ in range(count):
            key=blob();n=number();actions=list(struct.unpack_from('='+str(n)+'q',raw,at));at+=8*n
            arrays=[]
            for __ in range(3):arrays.append(list(struct.unpack_from('='+str(n)+'d',raw,at)));at+=8*n
            number();number();number()
            if key[0]!=0:continue
            history=[list(struct.unpack_from('=bbh',key,1+4*j))+[0,0] for j in range((len(key)-4)//4)]
            tag=tuple(tuple(h[:3]) for h in history);support.setdefault(tag,set()).update(a for a in actions if a>1)
            pre.append((key,history,actions,arrays))
        if at!=len(raw):raise ValueError('inherited trailing bytes')
        inherited=[]
        for history,actions in sorted(support.items()):
            h=[list(x)+[0,0] for x in history];a=sorted(actions);self.core.expand_support(0,h,a);inherited.append(dict(round=0,history=h,actions=a))
        groups=model.classes();payload=[];observations=[]
        for key,history,actions,arrays in pre:
            b=betting(rules)
            for h in history:act(b,h[2] if h[2] in (0,1) else 3 if h[2]==-3 else h[2]+2)
            own=list(groups[struct.unpack_from('=h',key,len(key)-2)[0]][0]);o=observe(b,own,[])
            row=self.core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,True)
            if row['key']!=key or not set(actions)<=set(row['actions']):raise ValueError('inherited support/key lost')
            new=row['actions'];R=[0.]*len(new);A=R.copy();prior=[0.]*len(new)
            for i,a in enumerate(actions):
                j=new.index(a);R[j]=arrays[0][i];A[j]=arrays[1][i];prior[j]=arrays[2][i]
            z=sum(prior);prior=[x/z for x in prior];payload.append(dict(key=key,actions=new,R=R,A=A,prior=prior));observations.append(o)
        self.core.seed_preflop(payload)
        # Verify EVERY imported row's average distribution, including old sizes
        # which the regenerated geometry omitted. Additional actions stay zero.
        for (key,history,actions,arrays),row,o in zip(pre,payload,observations):
            z=sum(arrays[1]);expected=np.array(arrays[1])/z if z else np.array(arrays[2])
            actual=self.core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,True)['probabilities']
            np.testing.assert_allclose([actual[o.actions.index(a)] for a in actions],expected,atol=1e-14)
        self.identity['inherited_support']=inherited
        self.identity['bootstrap']=dict(checkpoint_sha256=meta['sha256'],old_identity=meta['identity'],old_iterations=oldt,preflop_rows=len(pre),scope='exact finite preflop R/A import; no inherited new-game RNG/t; post behavior from existing warm prior')
        self.checkpoint_hash=None
        return dict(rows=len(pre),public_nodes=len(inherited),all_old_actions_preserved=True,average_frequency_max_error=0.)


from gto.qualification.multiplayer_joint import SparseJoint
import random
import numpy as np

class Multiplayer(SparseJoint):
    """Existing N external sampler, mean raw chance batch BEFORE CFR+ clip.
    This reduces chance variance, not full private/action enumeration or a
    multiplayer Nash guarantee. Existing lazy average is retained unchanged.
    """
    def __init__(self,*args,chance_batch=2,chance_mode="iid",**kwargs):
        if type(chance_batch) is not int or not 1<=chance_batch<=8:raise ValueError('bounded chance batch')
        super().__init__(*args,**kwargs);self.chance_batch=chance_batch;self.batch=[];self.chance_mode=chance_mode
        if chance_mode not in ('iid','seat_rotation'):raise ValueError('chance mode')
        if chance_mode=='seat_rotation' and self.decks is not None:raise ValueError('rotation requires uniform full-deck law, not arbitrary finite support')
        self.identity.update(chance_batch=chance_batch,chance_mode=chance_mode,integration_source_sha256=sha(Path(__file__)))
    def _draw(self):
        if self.chance_mode=='iid':self.batch=[super(Multiplayer,self)._draw() for _ in range(self.chance_batch)]
        else:
            first=super()._draw();self.batch=[first]
            for j in range(1,self.chance_batch):
                # Uniform deck law is invariant under a fixed permutation of
                # private deal slots. Seats/stack/strategy stay unchanged.
                rotated=first.copy()
                for p in range(self.N):rotated[2*p:2*p+2]=first[2*((p+j)%self.N):2*((p+j)%self.N)+2]
                self.batch.append(rotated)
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
