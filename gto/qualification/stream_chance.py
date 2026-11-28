"""Streaming stratified public chance, unchanged active/private-vector kernel.
One immutable global policy per iteration. Raw CF/own-reach averages are summed
across weighted board chunks BEFORE CFR+ clipping. Finite catalog != full NLH.
"""
import gc,itertools,random
import numpy as np
from gto.qualification import active_chance as ac,public_chance_solver as pcs


def flop_features(board):
    rs={c//4+2 for c in board[:3]};paired=len(rs)<3;mono=len({c%4 for c in board[:3]})==1
    if 14 in rs:rs.add(1)
    connected=not paired and any(sum(r in rs for r in range(lo,lo+5))>=3 for lo in range(1,11))
    return paired,mono,connected


def strata():
    counts={}
    for flop in itertools.combinations(range(52),3):
        key=flop_features(flop);counts[key]=counts.get(key,0)+1
    out={};den=22100*49*48
    for (paired,mono,connected),count in counts.items():
        if paired:out[(7,mono,connected)]=count*49*48/den
        else:
            for public,ways in ((0,40*36),(1,40*12),(3,9*48)):out[(public,mono,connected)]=count*ways/den
    assert abs(sum(out.values())-1)<1e-12
    return out


def catalog(lib,seed,repetitions=1):
    if type(repetitions) is not int or not 1<=repetitions<=4:raise ValueError('bounded strata catalog')
    rng=random.Random(seed);out=[]
    from gto.qualification.fullstreet_solver import public_code
    for (public,mono,connected),weight in sorted(strata().items()):
        for _ in range(repetitions):
            for trial in range(200000):
                board=rng.sample(range(52),5)
                if public_code(board)==public and flop_features(board)[1:]==(mono,connected):break
            else:raise ValueError('stratum rejection budget')
            b=pcs.block(lib,board,weight/repetitions);b['stratum']=[public,mono,connected];out.append(b)
    return out


class Game(ac.Game):
    """Global active rows; only one board's CF state resides in the C++ kernel.
    Chunk-local BR maxima are a board-revealed relaxation, NOT restricted NC.
    Exact shared-information BR is evaluated separately by stream_br.
    """
    def __init__(self,lib,nodes,blocks,splits=()):
        if not blocks or abs(sum(b['weight'] for b in blocks)-1)>1e-12:raise ValueError('normalized public law')
        self.lib,self.nodes,self.blocks,self.C=lib,nodes,blocks,169;self.splits=set(map(tuple,splits));self.t=0;self.P=0
        self.keys=[None if n['actor']<0 else [] for n in nodes];lookup=[{} for _ in nodes];chunks=[]
        for b in blocks:
            q=ac.Game(lib,nodes,[dict(b,weight=1.)],self.splits);local_ids=[]
            for st,t,n,k in q.rows:
                ids=[]
                for key in q.keys[k]:
                    if key not in lookup[k]:lookup[k][key]=len(self.keys[k]);self.keys[k].append(key)
                    ids.append(lookup[k][key])
                local_ids.append((st,np.asarray(ids,dtype=np.int32),n,k))
            q.keys=None;q.observations=None;q.parent_rows=None
            q.R=q.A=q.prior=q.visits=None
            chunks.append((q,local_ids,float(b['weight'])))
        self.base=[];self.prebase=[];self.rows=[];self.S=0
        for k,n in enumerate(nodes):
            self.base.append(self.S);self.prebase.append(self.P if n['actor']>=0 and n['round']==0 else -1)
            if n['actor']<0:continue
            count=len(n['children']);t=len(self.keys[k]);self.rows.append((self.S,t,count,k));self.S+=t*count
            if n['round']==0:self.P+=169*count
        self.R=np.zeros(self.S);self.A=np.zeros(self.S);self.prior=np.zeros(self.S,dtype=np.float32);self.visits=np.zeros(self.S,dtype=np.uint16)
        self.grad=np.zeros(self.S);self.avg=np.zeros(self.S);self.den=np.zeros(self.S);self.num=np.zeros(self.P);self.evden=np.zeros(self.P)
        for st,t,n,k in self.rows:self.prior[st:st+t*n]=1/n
        self.chunks=[];active=[]
        for q,ids,weight in chunks:
            mapping=np.empty(q.S,dtype=np.int32)
            for st,gids,n,k in ids:mapping[st:st+len(gids)*n]=(self.base[k]+gids[:,None]*n+np.arange(n)).ravel()
            a=np.full_like(q.active,-1);valid=q.active>=0;a[valid]=mapping[q.active[valid]];active.append(a)
            q.active=None;self.chunks.append((q,mapping,weight))
        self.active=np.concatenate(active);del chunks,lookup;gc.collect()
        self.estimate_bytes=self.active.nbytes+self.S*54+max(q.estimate_bytes for q,_,_ in self.chunks)
        if self.estimate_bytes>1536*1024**2:raise MemoryError('1.5GiB numeric streaming budget (Python keys measured separately)')

    def evaluate_owner(self,pi,owner):
        for x in (self.grad,self.avg,self.den,self.num,self.evden):x.fill(0)
        result=np.zeros(2)
        for q,mapping,w in self.chunks:
            value=q.evaluate_owner(pi[mapping],owner)
            # Each chunk map is injective: sharing occurs across chunks, so indexed
            # addition is correct and avoids a slow Python per-hand update.
            self.grad[mapping]+=w*q.grad;self.avg[mapping]+=w*q.avg;self.den[mapping]+=w*q.den
            self.num+=w*q.num;self.evden+=w*q.evden;result+=w*np.asarray(value)
        return result.tolist()

    def measure(self):
        raise ValueError('chunk-local BR maxima are not shared-information NashConv; use stream_br.measure')

    def initialize(self,parent,old_to_new=None):
        """Behavioral warm transfer; new actions start at zero, new states uniform.
        New chance law does not inherit old cumulative regrets/average masses.
        """
        if old_to_new is None:old_to_new={k:k for k in range(len(parent.nodes))}
        reverse={v:k for k,v in old_to_new.items()};oldpi=parent.policy();look=[];back=[]
        for k,n in enumerate(parent.nodes):
            if n['actor']<0:look.append({});back.append({});continue
            count=len(n['children']);look.append({key:parent.base[k]+j*count for j,key in enumerate(parent.keys[k])});total={};mass={}
            for b,block in enumerate(parent.blocks):
                for at in parent.active[b,k]:
                    code=parent.keys[k][(int(at)-parent.base[k])//count][0];w=block['weight']/1081
                    total.setdefault(code,np.zeros(count));mass[code]=mass.get(code,0)+w;total[code]+=w*oldpi[at:at+count]
            back.append({c:x/mass[c] for c,x in total.items()})
        stats=dict(exact=0,parent=0,new_uniform=0)
        for st,t,n,k in self.rows:
            old=reverse.get(k);newactions=self.nodes[k]['native_actions']
            for j,key in enumerate(self.keys[k]):
                p=None
                if old is not None:
                    memory=tuple((reverse[a],f) for a,f in key[1] if a in reverse)
                    at=look[old].get((key[0],memory));oldactions=parent.nodes[old]['native_actions']
                    if at is not None:p=oldpi[at:at+len(oldactions)];stats['exact']+=1
                    elif key[0] in back[old]:p=back[old][key[0]];stats['parent']+=1
                    if p is not None:
                        d=dict(zip(oldactions,p));p=np.array([d.get(a,0.) for a in newactions]);z=p.sum();p=p/z if z else None
                if p is None:p=np.ones(n)/n;stats['new_uniform']+=1
                at=st+j*n;self.prior[at:at+n]=p;self.R[at:at+n]=p*1e-6;self.A[at:at+n]=p*.001
        self.initial_average=self.A.copy();self.initial_regret=self.R.copy();return stats


def node_map(old,new):
    tags=lambda n:(n['round'],n['actor'],tuple(map(tuple,n.get('native_prefix',[]))))
    table={tags(n):k for k,n in enumerate(new) if n['actor']>=0}
    return {k:table[tags(n)] for k,n in enumerate(old) if n['actor']>=0 and tags(n) in table}


def expanded_tree(rules,root_actions,extra_raise_actions):
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
            if raises==1:actions=sorted(set(actions).union(a for a in extra_raise_actions if a in offered))
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
