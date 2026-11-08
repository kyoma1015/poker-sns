"""Small independent enumeration oracle; never supplies production strategies."""
import ctypes as C,itertools,math
from gto.abstract import model,joint_stream as s

# Public tree: SB fold/bet, BB fold/call, public board, SB check/bet, BB fold/call.
ACTOR=[0,-1,1,-1,0,-1,1,-1,-1]
CHILD=[[1,2],[],[3,4],[],[5,6],[],[7,8],[],[]]
BASE=[0,-1,4,-1,8,-1,12,-1,-1]
C0=[0,-.5,0,1,0,-2,0,2,-3];C1=[0,0,0,0,0,4,0,0,6]
MASSES=[[.15,.35,.25,.25],[0.,.2,.7,.1]];WEIGHT=[.25,.75]
EQUITY=[[.1,.3,.65,.9],[.15,.4,.7,.95]]

def policies():
    return [[.2,.8,.9,.1,.35,.65,.75,.25,.4,.6,.6,.4,.8,.2,.1,.9],
            [.2,.8,.9,.1,.35,.65,.75,.25,.15,.85,.7,.3,.25,.75,.65,.35]]

def index(k,h,v):return BASE[k]+2*(h if ACTOR[k]==0 else v)

def oracle(board,pi):
    """Explicit path products, with zero-reach actions still counterfactual."""
    grad=[0.]*16;avg=[0.]*16;anum=[0.]*16;aden=[0.]*16;ev=0.
    for h,v in itertools.product(range(2),repeat=2):
        w=2*h+v;mass=MASSES[board][w];e=EQUITY[board][w]
        def value(k):
            if ACTOR[k]<0:return C0[k]+C1[k]*e
            i=index(k,h,v);return sum(pi[i+a]*value(c) for a,c in enumerate(CHILD[k]))
        ev+=mass*value(0)
        def walk(k,path):
            if ACTOR[k]<0:return
            owner=ACTOR[k];i=index(k,h,v);own=math.prod(p for seat,p in path if seat==owner);opp=math.prod(p for seat,p in path if seat!=owner);sign=1 if owner==0 else -1
            for a,c in enumerate(CHILD[k]):
                q=sign*value(c);grad[i+a]+=mass*opp*(q-sign*value(k));avg[i+a]+=mass*own*pi[i+a];anum[i+a]+=mass*opp*q;aden[i+a]+=mass*opp
                walk(c,path+[(owner,pi[i+a])])
        walk(0,[])
    return {'grad':grad,'avg':avg,'action_num':anum,'action_den':aden,'ev':ev}

def native(lib,board,pi):
    S=16;B=5;W=4
    grad=(C.c_double*S)();avg=(C.c_double*S)();leaf=(C.c_double*(2*B*169))();metrics=(C.c_double*3)();anum=(C.c_double*S)();aden=(C.c_double*S)()
    rc=lib.stream_block(9,W,S,B,model.ints(ACTOR),model.ints([len(x) for x in CHILD]),model.ints([c for row in CHILD for c in (row+[-1]*4)[:4]]),model.ints(BASE),model.ints([int(k>=4) for k in range(9)]),model.ints([-1,1,-1,3,4,-1,-1,-1,-1]),model.ints([0,0,1,1]),model.ints([0,1,0,1]),model.ints([0,0,1,1]),model.ints([0,1,0,1]),model.doubles(MASSES[board]),model.doubles(EQUITY[board]),model.doubles(C0),model.doubles(C1),model.doubles(pi),grad,avg,leaf,metrics,anum,aden)
    if rc:raise ValueError(rc)
    return {'grad':list(grad),'avg':list(avg),'action_num':list(anum),'action_den':list(aden),'ev':metrics[0],'leaf':list(leaf)}

def brute_br(pi,owner):
    """Enumerate ALL 64 legal pure behavioral policies per player. Hidden cards
    and the future board are never available at the preflop choice."""
    best=-math.inf
    for bits in itertools.product(range(2),repeat=6):
        total=0.
        for b,h,v in itertools.product(range(2),repeat=3):
            w=2*h+v;e=EQUITY[b][w]
            def value(k):
                if ACTOR[k]<0:return (C0[k]+C1[k]*e)*(1 if owner==0 else -1)
                own=h if owner==0 else v
                if ACTOR[k]==owner:
                    bit=own if k<4 else 2+b*2+own
                    return value(CHILD[k][bits[bit]])
                i=index(k,h,v);return sum(pi[b][i+a]*value(c) for a,c in enumerate(CHILD[k]))
            total+=WEIGHT[b]*MASSES[b][w]*value(0)
        best=max(best,total)
    return best

def native_br(outs):
    total=[sum(WEIGHT[b]*outs[b]['leaf'][i] for b in range(2)) for i in range(2*5*169)]
    def at(owner,node,t):return total[(owner*5+node)*169+t]
    return [sum(max(at(0,1,t),at(0,3,t)+at(0,4,t)) for t in range(2)),
            sum(at(1,1,t)+max(at(1,3,t),at(1,4,t)) for t in range(2))]
