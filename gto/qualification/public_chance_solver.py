"""Research PCS CFR+: exact private integration, CSR actions, causal prefixes.
No native BR certificate, abstraction error bound, or registry admission implied.
"""
import ctypes as C
import random
import subprocess
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification import fullstreet_solver as f
from gto.qualification.policy import hand


def build(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    target=directory/'public_chance.so'
    subprocess.run(['c++','-std=c++17','-O3','-fno-fast-math','-ffp-contract=off',
                    '-shared','-fPIC',str(Path(__file__).with_name('public_chance_core.cc')),
                    '-o',str(target)],check=True)
    lib=f.load(target)
    lib.pcs_eval.argtypes=[C.c_int]*5+[model.IP]*13+[model.DP]*9+[C.c_int,model.DP]
    lib.pcs_eval.restype=C.c_int
    lib.pcs_world.argtypes=[model.IP]*4;lib.pcs_world.restype=C.c_int
    lib.pcs_terminal.argtypes=[C.c_int]+[model.IP]*2+[model.DP]*3
    lib.pcs_terminal.restype=C.c_int
    return lib


def block(lib,board,weight=1.):
    holes=np.empty((1081,2),dtype=np.int32);codes=np.empty(1081,dtype=np.int32);ranks=codes.copy()
    rc=lib.pcs_world(model.ints(board),holes.ctypes.data_as(model.IP),codes.ctypes.data_as(model.IP),ranks.ctypes.data_as(model.IP))
    if rc!=1081:raise ValueError('invalid public board')
    codes+=np.array([8*hand(tuple(map(int,h))) for h in holes],dtype=np.int32)
    return dict(board=list(board),public=f.public_code(board),codes=codes.tolist(),
                holes=holes,ranks=ranks,weight=weight)


def draw(lib,rng):
    # Uniform ordered full board; all compatible private pairs integrated exactly.
    # Future suffix is evaluator input only; policy indexes use revealed prefixes.
    return block(lib,rng.sample(range(52),5))


class Game(f.Game):
    def use_blocks(self,blocks):
        if not blocks or abs(sum(b['weight'] for b in blocks)-1)>1e-12 or any(b['weight']<=0 for b in blocks):
            raise ValueError('normalized board law / p-to-q corrected weights required')
        self.blocks=blocks;self.types=[1081]*len(blocks);nodes=self.nodes
        offsets=np.cumsum([0]+[len(n['children']) for n in nodes])
        self.static=[model.ints([n['actor'] for n in nodes]),model.ints(offsets),
          model.ints([c for n in nodes for c in n['children']]),model.ints([n['round'] for n in nodes]),
          model.ints(self.base),model.ints(self.prebase),model.ints([b['public'] for b in blocks]),
          model.ints(self.types),model.ints(np.arange(len(blocks))*1081),model.ints([0]*len(blocks)),
          model.ints([c for b in blocks for c in b['codes']]),
          model.ints(np.concatenate([b['holes'].ravel() for b in blocks])),
          model.ints(np.concatenate([b['ranks'] for b in blocks]))]
        self.weights=model.doubles([b['weight'] for b in blocks])
        self.c0=model.doubles([n.get('c0',0.) for n in nodes]);self.c1=model.doubles([n.get('c1',0.) for n in nodes])

    def evaluate_owner(self,pi,owner):
        result=(C.c_double*2)();ptr=lambda x:x.ctypes.data_as(model.DP)
        rc=self.lib.pcs_eval(len(self.nodes),len(self.blocks),self.C,self.S,owner,*self.static,
            self.weights,self.c0,self.c1,ptr(pi),ptr(self.grad),ptr(self.avg),ptr(self.den),
            ptr(self.num),ptr(self.evden),self.P,result)
        if rc:raise ValueError('PCS kernel '+str(rc))
        return list(result)

    def step(self):
        # BOTH owners use the same pre-update pi and sampled public chance draw.
        pi=self.policy(False);self.t+=1
        for owner in (0,1):
            self.evaluate_owner(pi,owner)
            for start,t,n,k in self.rows:
                if self.nodes[k]['actor']!=owner:continue
                sl=slice(start,start+t*n)
                self.R[sl]=np.maximum(0,self.R[sl]+self.grad[sl])
                self.A[sl]+=self.t*self.avg[sl]
                self.visits[sl]=np.minimum(65535,self.visits[sl].astype(np.uint32)+(self.den[sl]>0))
