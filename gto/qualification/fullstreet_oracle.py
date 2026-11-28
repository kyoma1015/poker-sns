"""Complete tiny-game BR enumeration, independent path-product CF oracle."""
import itertools,math
import numpy as np
from gto.abstract import joint_update_audit as old,joint_history
from gto.qualification.fullstreet_solver import Game


def fixture(lib,equity=None,future=False):
    nodes=[dict(actor=a,children=c,round=0 if k<4 else (3 if future and k==6 else 1),c0=old.C0[k],c1=old.C1[k]) for k,(a,c) in enumerate(zip(old.ACTOR,old.CHILD))]
    eq=equity or old.EQUITY
    blocks=[dict(public=(b if future else 7*b),codes=[8*h+((b^h) if future else 0) for h in range(2)],mass=np.array(old.MASSES[b]).reshape(2,2).tolist(),equity=np.array(eq[b]).reshape(2,2).tolist(),weight=old.WEIGHT[b]) for b in range(2)]
    return Game(lib,nodes,blocks,2)

def bits(x,n):return tuple((x>>(n-1-i))&1 for i in range(n))

def worlds(game):
    out=[]
    for b in game.blocks:
        for h,hcode in enumerate(b['codes']):
            for v,vcode in enumerate(b['codes']):
                mass=b['mass'][h][v]*b['weight']
                if mass:out.append(dict(pub=bits(b['public'],3),private=(bits(hcode%8,3),bits(vcode%8,3)),classes=(hcode//8,vcode//8),mass=mass,equity=b['equity'][h][v]))
    return out

def key(game,k,w):
    owner=game.nodes[k]['actor'];r=game.nodes[k]['round']
    return (k,w['pub'][:r],w['classes'][owner],w['private'][owner][:r])

def slot(game,key):
    k,pub,c,private=key;n=len(game.nodes[k]['children']);r=len(pub)
    group=sum(x*2**(r-i-1) for i,x in enumerate(pub));signal=sum(x*2**(r-i-1) for i,x in enumerate(private))
    return game.base[k]+(group*game.C*2**r+c*2**r+signal)*n

def reference(game,pi,br_owner=None,choice=None):
    ws=worlds(game)
    def walk(k,w):
        node=game.nodes[k]
        if node['actor']<0:return node['c0']+node['c1']*w['equity']
        info=key(game,k,w)
        if node['actor']==br_owner:return walk(node['children'][choice[info]],w)
        start=slot(game,info);return math.fsum(pi[start+a]*walk(c,w) for a,c in enumerate(node['children']))
    return math.fsum(w['mass']*walk(0,w) for w in ws)

def pure_br(game,pi,owner):
    keys=sorted({key(game,k,w) for w in worlds(game) for k,n in enumerate(game.nodes) if n['actor']==owner})
    actions=[range(len(game.nodes[k[0]]['children'])) for k in keys]
    if math.prod(len(a) for a in actions)>4096:raise ValueError('tiny complete enumeration budget')
    return max((1 if owner==0 else -1)*reference(game,pi,owner,dict(zip(keys,p))) for p in itertools.product(*actions))

def path_oracle(game,pi,owner):
    grad=np.zeros(game.S);avg=grad.copy();den=grad.copy()
    def value(k,w):
        n=game.nodes[k]
        if n['actor']<0:return n['c0']+n['c1']*w['equity']
        start=slot(game,key(game,k,w));return sum(pi[start+a]*value(c,w) for a,c in enumerate(n['children']))
    def visit(k,w,r):
        n=game.nodes[k]
        if n['actor']<0:return
        start=slot(game,key(game,k,w))
        if n['actor']==owner:
            sign=1 if owner==0 else -1;v=value(k,w)
            for a,c in enumerate(n['children']):
                grad[start+a]+=w['mass']*r[1-owner]*sign*(value(c,w)-v);avg[start+a]+=w['mass']*r[owner]*pi[start+a];den[start+a]+=w['mass']*r[1-owner]
        for a,c in enumerate(n['children']):
            rr=list(r);rr[n['actor']]*=pi[start+a];visit(c,w,rr)
    for w in worlds(game):visit(0,w,[1.,1.])
    return grad,avg,den
