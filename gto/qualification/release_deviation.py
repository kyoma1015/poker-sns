"""Independent legal river-value deviation against the explicit call controller."""
import argparse,itertools,json,math,random,time
from pathlib import Path
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.action_native import native_value
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame


def nuts(native,own,board):
    if len(own)!=2 or len(board)!=5 or len(set(own+board))!=7:raise ValueError('river own/public cards required')
    rank=native.rank7(list(own)+list(board));available=[c for c in range(52) if c not in own and c not in board]
    return not any(native.rank7(list(pair)+list(board))>rank for pair in itertools.combinations(available,2))

def binomial_lower(k,n,alpha=.001):
    """Invert P_p[X>=k]=alpha, exact Bernoulli tail, no asymptotic normal fit."""
    if not 0<=k<=n or n<=0:raise ValueError('binomial counts')
    if k==0:return 0.
    if k==n:return alpha**(1/n)
    lo=0.;hi=k/n
    def tail(p):
        if p<=0:return 0.
        if p>=1:return 1.
        term=math.exp(n*math.log1p(-p))
        if term==0:
            logs=[math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)+i*math.log(p)+(n-i)*math.log1p(-p) for i in range(k)]
            top=max(logs);return max(0.,min(1.,1-math.exp(top)*math.fsum(math.exp(v-top) for v in logs)))
        terms=[term]
        for i in range(k-1):term*=((n-i)/(i+1))*(p/(1-p));terms.append(term)
        return max(0.,min(1.,1-math.fsum(terms)))
    for _ in range(60):
        p=(lo+hi)/2
        if tail(p)<alpha:lo=p
        else:hi=p
    return lo

class RiverNuts:
    def __init__(self,base):self.base=base;self.jams=0;self.queries=0
    def row(self,o,average=False):
        if (o.actor==1 and o.round==3 and o.street[1]==o.price and 1 in o.actions
            and o.live[0]==o.live[1] and o.live[1] in (2,6,20) and o.remaining[1]>0):
            self.queries+=1
            if nuts(self.base.native,list(o.own),list(o.board)):
                self.jams+=1;a=max(o.actions)
                return [float(x==a) for x in o.actions]
        return self.base.row(o,True)


def evaluate(build,artifact,out):
    base=load_policy(build,artifact);deviation=RiverNuts(base);native=base.native;game=NativeGame([100,100])
    rng=random.Random(17118104);start=time.monotonic();n=8192;k=0;gain=ev0=ev1=0.
    for i in range(n):
        if time.monotonic()-start>25:raise RuntimeError('deviation gate incomplete/time cap')
        deck=rng.sample(range(52),9);tape=rng.getrandbits(128)
        a=native_value(base,native,game,deck,tape);b=native_value(deviation,native,game,deck,tape);g=a-b
        assert g>=0 and (g==0 or g>=40), 'guarded paired net proof violated'
        k+=g>0;gain+=g;ev0+=a;ev1+=b
    lower=40*binomial_lower(k,n)
    atomic(out,dict(status='COMPLETE_REFUTED_BY_LEGAL_DEVIATION' if lower>0 else 'COMPLETE_NO_POSITIVE_LOWER',
        source_policy_digest=base.policy_digest,seed=17118104,n=n,native_paths=2*n,seconds=time.monotonic()-start,
        deviation='BB only river known-nuts valuejam; other choices frozen B',
        hidden_card_access=False,compatible_opponent_pairs_per_nut_query=990,queries=deviation.queries,jams=deviation.jams,
        positive_gain_worlds=k,gain_mean_bb=gain/n,root_SB_baseline_EV_bb=ev0/n,root_SB_deviation_EV_bb=ev1/n,
        confidence=.999,br_gain_lower_bb=lower,nashconv_lower_bb=lower,
        bound='40BB * one-sided exact binomial P(positive gain) lower; gain>=0 and positive>=40 by known matched stakes',
        full_br_upper_bb=None,nashconv_bb=None,nashconv_upper_bb=None,ordinary_registry_admission=False,verified_strategy_count=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--artifact',required=True);p.add_argument('--output',required=True);a=p.parse_args();evaluate(a.build,a.artifact,a.output)
