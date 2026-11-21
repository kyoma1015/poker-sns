"""Exact all-in response conditioning, no surrogate payoff model. HU50 zero rake."""
import itertools,math,random
from gto.qualification.native_mccfr import betting,choose
from gto.qualification.policy import act,legal,hand
from gto.qualification.public_response import observe
from gto.hand169 import CLASSES


def mixed_value(fold_value,call_mass,call_value):
    return (1-call_mass)*fold_value+call_mass*call_value


class AllinConditioner:
    def __init__(self,s):
        if s.id['key']!='exact-suit-orbit':raise ValueError('class intervals require exact suit invariant policy')
        self.s=s;self.tables={};root=betting(s.rules);bb=betting(s.rules);act(bb,102)
        sb=betting(s.rules);act(sb,8);act(sb,102)
        for pair in itertools.combinations(range(52),2):
            po=dict(zip(legal(root),s.row(observe(root,pair,[]),True)))[8]
            cr=dict(zip(legal(bb),s.row(observe(bb,pair,[]),True)))[1]
            cv=dict(zip(legal(sb),s.row(observe(sb,pair,[]),True)))[1]
            self.tables[pair]=(po,cr,cv)
        self.masses={}

    def mass(self,own,context):
        key=(tuple(sorted(own)),context)
        if key not in self.masses:
            weights=[(1. if context=='rfi' else p[0],p[1] if context=='rfi' else p[2]) for h,p in self.tables.items() if not set(h).intersection(own)]
            denominator=math.fsum(w for w,_ in weights)
            if denominator==0:raise ValueError('unreachable conditional source history')
            self.masses[key]=math.fsum(w*c for w,c in weights)/denominator
        return self.masses[key]

    def bounds(self,own,context):
        m=self.mass(own,context);fold=1. if context=='rfi' else 3.
        return mixed_value(fold,m,-50.),mixed_value(fold,m,50.)

    def value(self,own,context,rng):
        m=self.mass(own,context);fold=1. if context=='rfi' else 3.
        if m==0:return fold
        available=[c for c in range(52) if c not in own]
        for _ in range(100000):
            other=rng.sample(available,2);p=self.tables[tuple(sorted(other))]
            weight=p[1] if context=='rfi' else p[0]*p[2]
            if rng.random()<weight:break
        else:raise RuntimeError('conditional-call sampling budget')
        board=rng.sample([c for c in available if c not in other],5)
        a,b=self.s.native.rank7(list(own)+board),self.s.native.rank7(other+board)
        call=50.*((a>b)-(a<b))
        return mixed_value(fold,m,call)


def integrated_rollout(s,deck,rng,forced=None,state=None):
    if state is not None:raise ValueError('use independent native oracle separately')
    b=betting(s.rules);holes=[deck[:2],deck[2:4]];steps=0
    while not b.done:
        if forced and steps<len(forced):a=forced[steps]
        else:
            p=b.actor;o=observe(b,holes[p],deck[4:4+(0,3,4,5)[b.round]]);pi=s.row(o,True)
            # Native HU50 equal-stack zero-rake all-in response: fold/call are
            # terminal in betting, with any board runout already sampled.
            if tuple(o.actions)==(0,1) and b.remaining[1-p]==0 and b.live[1-p]==100 and b.live[p]+b.remaining[p]==100 and not any(b.dead):
                ranks=[s.native.rank7(h+deck[4:]) for h in holes]
                call=50.*((ranks[p]>ranks[1-p])-(ranks[p]<ranks[1-p]))
                u=mixed_value(-b.live[p]/2,pi[1],call)
                return [u,-u] if p==0 else [-u,u]
            a=choose(o.actions,pi,rng)
        act(b,a);steps+=1
        if steps>512:raise RuntimeError('path budget')
    ranks=[s.native.rank7(h+deck[4:]) for h in holes]
    return [v/2 for v in b.settle(ranks,b.round>=1)['net']]


def restricted_gain(hands,actions,weights):
    """Only first-decision deviations; action expectations integrated BEFORE max."""
    lo=hi=0.
    for (label,row),w in zip(hands.items(),weights):
        intervals=[row['action_ev_bb'][str(a)]['interval'] for a in actions]
        pi=[row['sampled_frequencies'][a] for a in actions]
        lower=math.fsum(p*x[0] for p,x in zip(pi,intervals));upper=math.fsum(p*x[1] for p,x in zip(pi,intervals))
        lo+=w*(max(x[0] for x in intervals)-upper)
        hi+=w*(max(x[1] for x in intervals)-lower)
    return dict(gain_lower_bb=max(0,lo),gain_upper_bb=max(0,hi),
        scope='all first legal actions; private-class pure response; frozen future policy',
        complete_br_upper_bb=None,nashconv_upper_bb=None)
