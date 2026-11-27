"""Active private-vector indexing and perfect-recall refinement of existing PCS.
Finite public-board/action game only. Refinement scores are priorities, not native
error certificates. No policy input contains the opponent's cards/future board.
"""
import ctypes as C
import itertools
import subprocess
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification import public_chance_solver as pcs, fullstreet_solver as fs
from gto.qualification.policy import hand

PERMS=tuple(itertools.permutations(range(4)))

def observation(own, visible):
    """Full visible observation modulo global suit relabeling (not equity bins)."""
    if not visible:return (hand(tuple(map(int,own))),)
    def image(p):
        cv=lambda c:4*(int(c)//4)+p[int(c)%4]
        return (tuple(sorted(map(cv,own))),tuple(sorted(map(cv,visible[:3]))),tuple(map(cv,visible[3:])))
    return min(map(image,PERMS))

def feature(lib,own,visible):
    rank=int(lib.active_rank(model.ints(list(own)+list(visible)),len(visible)+2))
    suits=[sum(c%4==s for c in visible) for s in range(4)]
    ranks={c//4+2 for c in list(own)+list(visible)}
    if 14 in ranks:ranks.add(1)
    potential=max(sum(r in ranks for r in range(lo,lo+5)) for lo in range(1,11))
    flush=max(sum(c%4==s for c in list(own)+list(visible)) for s in range(4))
    blocker=tuple(sorted((suits[c%4],c//4+2) for c in own if suits[c%4]>=2))
    # Made category/primary rank, draw potential and nut-suit blockers. Never
    # future runout rank or opponent cards; public history is the node identity.
    return (rank//759375,(rank//50625)%15,flush,potential,tuple(sorted(suits)),blocker)

def build(directory):
    path=Path(directory);path.mkdir(parents=True,exist_ok=True);target=path/'active_chance.so'
    subprocess.run(['c++','-std=c++17','-O3','-fno-fast-math','-ffp-contract=off','-shared','-fPIC',str(Path(__file__).with_name('active_chance_core.cc')),'-o',str(target)],check=True)
    lib=fs.load(target)
    lib.active_eval.argtypes=[C.c_int]*5+[model.IP]*15+[model.DP]*9+[C.c_int,model.DP]
    lib.active_eval.restype=C.c_int
    lib.active_rank.argtypes=[model.IP,C.c_int];lib.active_rank.restype=C.c_uint64
    lib.pcs_world.argtypes=[model.IP]*4;lib.pcs_world.restype=C.c_int
    lib.pcs_terminal.argtypes=[C.c_int]+[model.IP]*2+[model.DP]*3;lib.pcs_terminal.restype=C.c_int
    return lib

class Game(pcs.Game):
    def __init__(self,lib,nodes,blocks,splits=(),fine=False,parent=None):
        self.lib,self.nodes,self.blocks,self.C=lib,nodes,blocks,169
        self.splits=set(map(tuple,splits));self.fine=fine;self.t=0;self.P=0
        B=len(blocks);N=len(nodes);self.active=np.full((B,N,1081),-1,dtype=np.int32)
        self.keys=[None]*N;self.base=[];self.prebase=[];self.rows=[];self.spans=[];self.parent_rows=[]
        ancestors=[[] for _ in nodes]
        for k,n in enumerate(nodes):
            for c in n['children']:ancestors[c]=ancestors[k]+([k] if n['actor']>=0 else [])
        obs={}
        for b,block in enumerate(blocks):
            for r in (1,2,3):obs[b,r]=[(observation(h,block['board'][:(0,3,4,5)[r]]) if fine else feature(lib,h,block['board'][:(0,3,4,5)[r]])) for h in block['holes']]
        self.observations=obs
        S=0
        for k,n in enumerate(nodes):
            self.base.append(S);self.prebase.append(self.P if n['round']==0 and n['actor']>=0 else -1)
            if n['actor']<0:self.spans.append(0);continue
            count=len(n['children']);groups={};keys=[];parents={}
            for b,block in enumerate(blocks):
                code=np.asarray(block['codes']);pub=block['public'];r=n['round']
                coarse=(pub>>(3-r))*(169<<r)+(code>>(3-r))
                for h in range(1081):
                    memory=[]
                    for a in ancestors[k]+[k]:
                        na=nodes[a];ra=na['round']
                        if na['actor']!=n['actor'] or not ra:continue
                        ca=(pub>>(3-ra))*(169<<ra)+(int(code[h])>>(3-ra))
                        if fine or (a,ca) in self.splits:memory.append((a,obs[b,ra][h]))
                    key=(int(coarse[h]),tuple(memory))
                    gid=groups.setdefault(key,len(groups));at=S+gid*count;self.active[b,k,h]=at
                    if gid==len(keys):
                        keys.append(key)
                        if parent is not None:parents[at]=int(parent.active[b,k,h])
            self.keys[k]=keys;size=len(keys)*count
            self.rows.append((S,len(keys),count,k));self.spans.append(size)
            self.parent_rows.extend((at,pa,count) for at,pa in parents.items());S+=size
            if n['round']==0:self.P+=169*count
        self.S=S;self.prior=np.empty(S,dtype=np.float32)
        for st,t,n,k in self.rows:self.prior[st:st+t*n]=1/n
        self.R=np.zeros(S);self.A=np.zeros(S);self.visits=np.zeros(S,dtype=np.uint16)
        self.grad=np.zeros(S);self.avg=np.zeros(S);self.den=np.zeros(S);self.num=np.zeros(self.P);self.evden=np.zeros(self.P)
        self.estimate_bytes=self.active.nbytes+S*54+B*N*1081*8*5
        if self.estimate_bytes>512*1024**2:raise MemoryError('512MiB active kernel budget')
        if parent is not None:
            # Split mass by chance occurrence count; current/average behavior and
            # total accumulated mass are preserved. This is a warm transfer, not
            # a claim that split regrets equal historical split CF regrets.
            parent_pi=parent.policy();oldcount=np.bincount(parent.active[parent.active>=0]);newcount=np.bincount(self.active[self.active>=0]);self.t=parent.t
            for at,pa,n in self.parent_rows:
                f=newcount[at]/oldcount[pa]
                self.R[at:at+n]=parent.R[pa:pa+n]*f;self.A[at:at+n]=parent.A[pa:pa+n]*f
                self.prior[at:at+n]=parent_pi[pa:pa+n]
        self.use_blocks(blocks)

    def use_blocks(self,blocks):
        if hasattr(self,'static') and [b['board'] for b in blocks]!=[b['board'] for b in self.blocks]:raise ValueError('reindex a different board law explicitly')
        pcs.Game.use_blocks(self,blocks)
        self.static[4]=model.ints(self.base)
        self.static[11:11] = [model.ints(self.active.ravel()),model.ints(self.spans)]

    def evaluate_owner(self,pi,owner):
        out=(C.c_double*2)();ptr=lambda x:x.ctypes.data_as(model.DP)
        rc=self.lib.active_eval(len(self.nodes),len(self.blocks),169,self.S,owner,*self.static,self.weights,self.c0,self.c1,ptr(pi),ptr(self.grad),ptr(self.avg),ptr(self.den),ptr(self.num),ptr(self.evden),self.P,out)
        if rc:raise ValueError('active kernel '+str(rc))
        return list(out)

    def export(self,pi=None):
        if pi is None:pi=self.policy()
        return [[None if n['actor']<0 else dict(pi=np.array([pi[at:at+len(n['children'])] for at in self.active[b,k]]),keys=[self.keys[k][(int(at)-self.base[k])//len(n['children'])] for at in self.active[b,k]]) for k,n in enumerate(self.nodes)] for b in range(len(self.blocks))]

    def priorities(self):
        """One-step CF heterogeneity, evaluated at the current average policy.
        Full-observation refinement retains every earlier owner observation.
        Scores select training work; only subsequent independent BR tests quality.
        """
        fine=Game(self.lib,self.nodes,self.blocks,self.splits,fine=True,parent=self);pi=fine.policy();answer=[]
        for owner in (0,1):
            fine.evaluate_owner(pi,owner)
            for st,t,n,k in fine.rows:
                if self.nodes[k]['actor']!=owner or self.nodes[k]['round']==0:continue
                grouped={}
                for j,key in enumerate(fine.keys[k]):grouped.setdefault(key[0],[]).append(fine.grad[st+j*n:st+(j+1)*n].copy())
                for code,values in grouped.items():
                    if (k,code) in self.splits:continue
                    v=np.asarray(values);gap=float(np.max(v,axis=1).sum()-np.max(v.sum(axis=0)))
                    if gap>1e-12:answer.append((gap,k,code,len(values)))
        return sorted(answer,reverse=True)

def native_tree(rules,root_actions):
    """Bounded native subgame; all offered sizes keep their exact public ledger.
    Unoffered sizes are not certified. Root support is supplied by the existing
    adaptive size selector, not a new release-size specification.
    """
    import copy
    from gto.qualification.native_mccfr import betting
    from gto.qualification.policy import act,legal
    from gto.qualification.range_continuation import street_tree
    nodes=[]
    def terminal(b):
        folded=any(b.folded);v=b.settle([0,0],True)['net'][0] if folded else b.live[0]
        nodes.append(dict(actor=-1,children=[],round=b.round,c0=v/2 if folded else -v/2,c1=0. if folded else v));return len(nodes)-1
    def post(b):
        sub,states=street_tree(b)
        def visit(k):
            n=sub[k];x=states[k]
            if n['actor']<0:return terminal(x) if x.done else post(x)
            at=len(nodes);nodes.append(dict(actor=n['actor'],children=[],round=x.round,native_prefix=[list(h[:3]) for h in x.history],native_actions=n['native_actions']))
            nodes[at]['children']=[visit(c) for c in n['children']];return at
        return visit(0)
    def pre(b,raises):
        if b.done:return terminal(b)
        if b.round>0:return post(b)
        offered=legal(b)
        if not b.history:actions=[a for a in root_actions if a in offered]
        else:
            target=22 if raises<=1 else 102 if raises==2 else None
            actions=[a for a in (0,1,target) if a is not None and a in offered]
            if target is not None and target not in offered:
                rs=[a for a in offered if a>1]
                if rs:actions.append(max(rs))
        at=len(nodes);nodes.append(dict(actor=b.actor,children=[],round=0,native_prefix=[list(h[:3]) for h in b.history],native_actions=actions))
        for a in actions:
            child=copy.deepcopy(b);act(child,a);nodes[at]['children'].append(pre(child,raises+(a>1)))
        return at
    pre(betting(rules),0)
    if len(nodes)>6000:raise MemoryError('bounded subgame node budget')
    return nodes
