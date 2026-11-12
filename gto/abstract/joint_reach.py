"""Independent finite joint preflop/continuation game; NOT full-poker GTO.

No policy-weighted posterior is baked into chance. Counterfactual values use
opponent-only reach. Preflop information never includes the future board.
"""
import ctypes as C
import math
import subprocess
from array import array
from pathlib import Path
from gto.abstract.model import IP,DP,ints,doubles

def observation(node, world):
    seat=node['actor']
    if seat not in (0,1):raise ValueError('decision required')
    own=world['signals'][seat]
    return (own//8,) if node['street']=='preflop' else (tuple(world['flop']),own)

def prepare(nodes,worlds):
    """Each public node has a unique parent: full public history is implicit.

    World signals are class*8+own/public flags. Equities may use hidden cards;
    observation() cannot. Perfect recall is checked along every world path.
    """
    if not nodes or not worlds:raise ValueError('nonempty finite game')
    if any(not math.isfinite(w['mass']) or w['mass']<=0 or not 0<=w['equity']<=1 for w in worlds) or not math.isclose(math.fsum(w['mass'] for w in worlds),1,abs_tol=1e-10):raise ValueError('normalized unweighted joint chance required')
    for w in worlds:
        if len(w['signals'])!=2 or any(type(x) is not int or not 0<=x<169*8 for x in w['signals']):raise ValueError('own169 class/flags required')
        if len(w['flop'])!=3 or len(set(w['flop']))!=3 or any(type(c) is not int or not 0<=c<52 for c in w['flop']):raise ValueError('legal public flop')
    parents={};width=[];info=array('i');keys=[];memory=[{} for _ in nodes]
    for k,n in enumerate(nodes):
        children=n['children'];count=len(children)
        if n.get('street') not in ('preflop','flop') or any(not math.isfinite(n.get(x,0)) for x in ('c0','c1')):raise ValueError('finite cashflow and explicit street required')
        if n['actor'] not in (-1,0,1) or count>4 or (n['actor']<0)!=(count==0):raise ValueError('legal actor/actions')
        for a,c in enumerate(children):
            if not k<c<len(nodes) or c in parents:raise ValueError('tree with unique public histories required')
            parents[c]=(k,a)
        if k and k not in parents:raise ValueError('connected public tree')
        rows={}
        for wi,w in enumerate(worlds):
            if n['actor']<0:info.append(-1);continue
            key=observation(n,w)
            # Retained own observations/actions: equal current key must imply
            # identical own-information history (perfect recall).
            hist=[];j=k
            while j:
                p,a=parents[j]
                if nodes[p]['actor']==n['actor']:hist.append((p,observation(nodes[p],w),a))
                j=p
            history=tuple(hist)
            if key in memory[k] and memory[k][key]!=history:raise ValueError('imperfect recall information key')
            memory[k][key]=history
            if key not in rows:
                rows[key]=len(width);width.extend([count]*count);keys.append((k,key,rows[key]))
            info.append(rows[key])
    return {'nodes':nodes,'worlds':worlds,'info':info,'width':width,'keys':keys}

def build(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    out=directory/'joint-reach.so'
    subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(Path(__file__).with_suffix('.cc')),'-o',str(out)],check=True)
    lib=C.CDLL(str(out.resolve()));lib.joint_run.argtypes=[C.c_int]*4+[IP]*5+[DP]*9;lib.joint_run.restype=C.c_int
    return lib

class Solver:
    def __init__(self,lib,g):
        self.lib,self.g=lib,g;ns=g['nodes'];ws=g['worlds'];s=len(g['width'])
        self.args=[len(ns),len(ws),s,ints([n['actor'] for n in ns]),ints([len(n['children']) for n in ns]),ints([x for n in ns for x in (n['children']+[-1]*4)[:4]]),ints(g['info']),ints(g['width']),doubles([w['mass'] for w in ws]),doubles([w['equity'] for w in ws]),doubles([n.get('c0',0.) for n in ns]),doubles([n.get('c1',0.) for n in ns])]
        self.regret=(C.c_double*s)();self.sums=(C.c_double*s)();self.policy=(C.c_double*s)();self.action_ev=(C.c_double*s)();self.iterations=0
    def run(self,iterations):
        if type(iterations) is not int or iterations<0:raise ValueError('nonnegative sweep count')
        out=(C.c_double*8)();n,w,s,*args=self.args
        if self.lib.joint_run(n,w,s,iterations,*args,self.regret,self.sums,self.policy,self.action_ev,out):raise ValueError('joint CFR/BR failed')
        self.iterations+=iterations
        ev,h,v,nc,mass,lo,hi,bound=out
        if min(h-ev,v+ev,nc)<-1e-8:raise ValueError('invalid BR lower bound')
        if self.iterations and nc>bound/self.iterations+1e-8:raise ValueError('external regret certificate mismatch')
        return {'iterations':self.iterations,'sb_ev_bb':ev,'sb_br_gain_bb':h-ev,'bb_br_gain_bb':v+ev,'joint_nashconv_bb':nc,'positive_regret_bound_bb':bound/self.iterations if self.iterations else None,'unresolved_nonallin_showdown_mass':mass,'future_ev_lower_bb':lo,'future_ev_upper_bb':hi,'sampling_error_bb':0,'real_game_approximation_error':'UNKNOWN','external_GTO_comparison':'NOT PERFORMED','normal_GTO_registration':False}

def independent_br(g,policy,owner):
    """Slow Python oracle: integrate hidden/future worlds BEFORE own maximization."""
    ns,ws=g['nodes'],g['worlds'];W=len(ws);r=[[1.]*W for _ in ns]
    for k,n in enumerate(ns):
        for a,c in enumerate(n['children']):
            r[c]=[r[k][w]*(policy[g['info'][k*W+w]+a] if n['actor']!=owner else 1.) for w in range(W)]
    values=[None]*len(ns)
    for k in range(len(ns)-1,-1,-1):
        n=ns[k]
        if n['actor']<0:values[k]=[(n['c0']+n['c1']*w['equity'])*(1 if owner==0 else -1) for w in ws];continue
        if n['actor']==owner:
            totals={}
            for w,world in enumerate(ws):
                i=g['info'][k*W+w];row=totals.setdefault(i,[0.]*len(n['children']))
                for a,c in enumerate(n['children']):row[a]+=world['mass']*r[k][w]*values[c][w]
            best={i:max(range(len(row)),key=row.__getitem__) for i,row in totals.items()}
            values[k]=[values[n['children'][best[g['info'][k*W+w]]]][w] for w in range(W)]
        else:values[k]=[math.fsum(policy[g['info'][k*W+w]+a]*values[c][w] for a,c in enumerate(n['children'])) for w in range(W)]
    return math.fsum(w['mass']*v for w,v in zip(ws,values[0]))

def conditional_opponent(g,policy,node,own_observation):
    """Opponent class posterior at a public history, excluding own action reach.

    Conditioning is on OWN abstraction and public history only. The actual
    opponent signal is integrated out. Zero mass is returned as missing, not0EV.
    """
    ns,ws=g['nodes'],g['worlds'];owner=ns[node]['actor'];parents={c:(k,a) for k,n in enumerate(ns) for a,c in enumerate(n['children'])}
    path=[];k=node
    while k:k,a=parents[k];path.append((k,a))
    mass=[0.]*169;W=len(ws)
    for w,world in enumerate(ws):
        if observation(ns[node],world)!=own_observation:continue
        z=world['mass']
        for k,a in path:
            if ns[k]['actor']!=owner:z*=policy[g['info'][k*W+w]+a]
        mass[world['signals'][1-owner]//8]+=z
    total=math.fsum(mass)
    return {'counterfactual_mass':total,'opponent_class_probability':[z/total for z in mass] if total else None,'own_reach_included':False}
