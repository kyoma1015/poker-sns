"""Legal river-nuts deviation lower bound, never a complete BR upper bound.

At a matched zero-rake river, the defender always check/calls. An own/public
absolute-nuts jam gains r if strictly winning and0 if tied, for EVERY compatible
opponent hand. No future chance remains. Thus gain is nonnegative half-BB lattice.
"""
import argparse,gzip,json,math
from pathlib import Path
from gto.qualification.release_deviation import binomial_lower
from gto.qualification.action_native import interval
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic


def cdf_lower(gains,alpha=.0005):
    if not gains or any(not 0<=x<=50 or abs(2*x-round(2*x))>1e-10 for x in gains):raise ValueError('nonnegative HU50 half-BB gain lattice required')
    n=len(gains);levels=[dict(threshold_bb=i/2,count=sum(x>=i/2 for x in gains)) for i in range(1,101)]
    for row in levels:row['probability_lower']=binomial_lower(row['count'],n,alpha/100)
    return .5*sum(x['probability_lower'] for x in levels),levels


def run(out):
    out=Path(out);raw=json.loads(gzip.decompress((out/'native-checkpoint.json.gz').read_bytes()));native=json.loads((out/'native.json').read_text());v=raw['values'];n=raw['completed']
    if n!=2048 or n!=raw['identity']['n'] or native['status']!='COMPLETE_UNVERIFIED':raise ValueError('fixed complete independent holdout required')
    gains=[a-b for a,b in zip(v[2],v[10])];lower,levels=cdf_lower(gains);lower=max(0.,lower-1e-8);delta=.0005/15
    profiles=[interval(x,-50,50,delta) for x in v[:4]];pairs=[]
    for qi in (2,3):
        for ci in (0,1):pairs.append(dict(candidate=qi,control=ci,EV_change_bb=interval([a-b for a,b in zip(v[qi],v[ci])],-100,100,delta)))
    kinds=['open3p5','threebet10p5','river_jam','fold','open2p5','threebet9','river_nuts'];deviations=[]
    for kind,x in zip(kinds,v[4:]):
        sign=1 if kind in ('open3p5','fold','open2p5') else -1
        deviations.append(dict(kind=kind,gain_bb=interval([sign*(a-b) for a,b in zip(x,v[2])],-100,100,delta)))
    atomic(out/'river-bound.json',dict(policy_digest=raw['identity']['policy_digests'][2],n=n,source_sha256=sha(Path(__file__)),measurement_identity=raw['identity'],
        confidence_family=.999,numerical_guard_bb=1e-8,allocation=dict(original15_intervals_failure=.0005,CDF100thresholds_failure=.0005),
        theorem='matched HU50 zero-rake river; own/public absolute nuts; fixed defender check/calls; gain remaining stake if wins else0; no opponent/future input',
        levels=levels,positive_events=sum(x>0 for x in gains),gain_point_bb=sum(gains)/n,independent_native_BR_gain_lower_bb=lower,native_NashConv_lower_bb=lower,
        complete_native_BR_upper_bb=None,complete_native_NashConv_bb=None,complete_native_NashConv_upper_bb=None,
        revised_profile_intervals=profiles,revised_EV_comparisons=pairs,revised_deviation_intervals=deviations,formal_acceptance=0,ordinary_registry_admission=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();run(a.out)
