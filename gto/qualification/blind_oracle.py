"""Independent six-card blind-poker diagnostic. NOT the native HU50 game."""
import itertools,math,random,time
from collections import defaultdict
from gto.qualification.action_baseline import general_updates
from gto.qualification.native_mccfr import matching,choose

# Actions: F fold, C call/check, R raise. Complete finite public tree.
ACTIONS={():('F','C','R'),('C',):('C','R'),('R',):('F','C','R'),
         ('C','R'):('F','C'),('R','R'):('F','C')}
ACTOR={h:(0 if len(h)%2==0 else 1) for h in ACTIONS}
WORLDS=tuple(itertools.permutations(range(6),2))

def key(h,world):return (h,world[ACTOR[h]]//2)

def ledger(h):
    """Independent BB ledger, positive stack receipt minus own total payment."""
    paid=[.5,1.]
    for i,a in enumerate(h):
        p=i%2
        if a=='F':return paid,1-p
        if a=='C':paid[p]=max(paid)
        elif a=='R':paid[p]=3. if max(paid)<3 else 10.
    return paid,None

def payoff(h,world):
    paid,winner=ledger(h)
    if winner is None:
        rank=[c//2 for c in world]
        if rank[0]==rank[1]:return 0.
        winner=int(rank[1]>rank[0])
    return paid[1] if winner==0 else -paid[0]

def uniform(h):return [1/len(ACTIONS[h])]*len(ACTIONS[h])

def policy(rows,average=False):
    return {k:matching(v['S' if average else 'R']) for k,v in rows.items()}

def row(pi,h,w):return pi.get(key(h,w),uniform(h))

def exact(pi):
    """Full hidden-world tree; scalar recursion is independent of sampled update."""
    grad=defaultdict(lambda:None);avg=defaultdict(lambda:None);ev=0.
    def add(dst,k,v):
        if dst[k] is None:dst[k]=[0.]*len(v)
        dst[k]=[x+y for x,y in zip(dst[k],v)]
    def walk(h,w,reach):
        if h not in ACTIONS:return payoff(h,w)
        p=ACTOR[h];k=key(h,w);pirow=row(pi,h,w);values=[]
        for a,q in zip(ACTIONS[h],pirow):
            r=reach[:];r[p]*=q;values.append(walk(h+(a,),w,r))
        value=sum(q*v for q,v in zip(pirow,values));sign=1 if p==0 else -1
        add(grad,k,[sign*(v-value)*reach[1-p]/30 for v in values])
        add(avg,k,[q*reach[p]/30 for q in pirow])
        return value
    for w in WORLDS:ev+=walk((),w,[1.,1.])/30
    return ev,dict(grad),dict(avg)

def best_response(pi,owner):
    """Backward induction on private-rank infosets, integrate hidden cards FIRST."""
    choices={}
    for h in sorted(ACTIONS,key=len,reverse=True):
        if ACTOR[h]!=owner:continue
        for rank in range(3):
            vals=[]
            for a in ACTIONS[h]:
                total=0.
                for w in WORLDS:
                    if w[owner]//2!=rank:continue
                    opp=1.
                    for j,action in enumerate(h):
                        prefix=h[:j]
                        if ACTOR[prefix]!=owner:opp*=row(pi,prefix,w)[ACTIONS[prefix].index(action)]
                    def continuation(t):
                        if t not in ACTIONS:return payoff(t,w)*(1 if owner==0 else -1)
                        if ACTOR[t]==owner:return continuation(t+(choices[key(t,w)],))
                        return sum(q*continuation(t+(b,)) for b,q in zip(ACTIONS[t],row(pi,t,w)))
                    total+=opp*continuation(h+(a,))/30
                vals.append(total)
            choices[(h,rank)]=ACTIONS[h][max(range(len(vals)),key=lambda i:vals[i])]
    response=dict(pi)
    for k,a in choices.items():response[k]=[float(b==a) for b in ACTIONS[k[0]]]
    value=exact(response)[0]*(1 if owner==0 else -1)
    return value,choices

def assessment(pi):
    ev=exact(pi)[0];b0,_=best_response(pi,0);b1,_=best_response(pi,1)
    return dict(ev_bb=ev,br0_bb=b0,br1_bb=b1,nashconv_bb=b0+b1,
                sb_fold_gain_bb=-.5-ev,scope='six-card restricted diagnostic game ONLY')

class FiniteCFR:
    def __init__(self,method,seed=17):
        self.method=method;self.rng=random.Random(seed);self.rows={};self.iteration=0
        for h in ACTIONS:
            for rank in range(3):self.rows[(h,rank)]={f:[0.]*len(ACTIONS[h]) for f in ('R','S')}
    def snapshot(self):
        return dict(method=self.method,iteration=self.iteration,rng=self.rng.getstate(),
            rows=[dict(history=list(k[0]),rank=k[1],**v) for k,v in self.rows.items()])
    def restore(self,d):
        if self.method!=d['method']:raise ValueError('method mismatch')
        def tuples(x):return tuple(tuples(y) for y in x) if isinstance(x,list) else x
        self.rng.setstate(tuples(d['rng']));self.iteration=d['iteration']
        self.rows={(tuple(x['history']),x['rank']):{f:x[f][:] for f in ('R','S')} for x in d['rows']}
    def sampled(self,pi,owner,w,rng):
        h=();reach=[1.,1.];qprefix=1.;records=[];averages=[]
        while h in ACTIONS:
            p=ACTOR[h];k=key(h,w);pr=row(pi,h,w)
            if p!=owner:averages.append((k,[x*reach[p]/qprefix for x in pr]))
            q=[.6/len(pr)+.4*x for x in pr] if p==owner else pr
            a=choose(ACTIONS[h],q,rng);index=ACTIONS[h].index(a)
            records.append((k,pr,index,q[index],reach[1-owner]/qprefix,[0.]*len(pr),p==owner))
            reach[p]*=pr[index];qprefix*=q[index];h+=(a,)
        grads=[(k,d) for k,_,d,_ in general_updates(records,payoff(h,w)*(1 if owner==0 else -1))]
        return grads,averages
    def external(self,pi,owner,w,rng):
        grads=[];avgs=[]
        def walk(h,reach,qprefix):
            if h not in ACTIONS:return payoff(h,w)*(1 if owner==0 else -1)
            p=ACTOR[h];k=key(h,w);pr=row(pi,h,w)
            if p!=owner:
                avgs.append((k,[x*reach[p]/qprefix for x in pr]));a=choose(ACTIONS[h],pr,rng);j=ACTIONS[h].index(a)
                r=reach[:];r[p]*=pr[j];return walk(h+(a,),r,qprefix*pr[j])
            vals=[]
            for a,q in zip(ACTIONS[h],pr):
                r=reach[:];r[p]*=q;vals.append(walk(h+(a,),r,qprefix))
            value=sum(q*v for q,v in zip(pr,vals));grads.append((k,[v-value for v in vals]));return value
        walk((),[1.,1.],1.);return grads,avgs
    def step(self):
        pi=policy(self.rows)
        if self.method=='exact':
            _,g,a=exact(pi);batches=[(g.items(),a.items())]
        else:
            w=tuple(self.rng.sample(range(6),2));fn=self.sampled if self.method=='outcome' else self.external
            batches=[fn(pi,p,w,random.Random(self.rng.getrandbits(128))) for p in (0,1)]
        for grads,avgs in batches:
            for f,items in (('R',grads),('S',avgs)):
                for k,v in items:self.rows[k][f]=[x+y for x,y in zip(self.rows[k][f],v)]
        self.iteration+=1
