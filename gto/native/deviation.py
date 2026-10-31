"""Local unilateral action deviation diagnostics, never global exploitability.

No two-player zero-sum division by2 is applied to multiplayer values. A single
observed decision and explicit belief cannot establish whole-game equilibrium.
"""
from fractions import Fraction
import math


def local_deviation(profile,values,legal_actions,hero_seat):
    base={'global_exploitability':None,'nash_conv':None,'convergence_verified':False,
          'scope':'one queried decision under explicit belief; not global equilibrium'}
    if (not isinstance(legal_actions,(list,tuple)) or not legal_actions
            or any(type(a) is not int for a in legal_actions)
            or len(set(legal_actions))!=len(legal_actions)
            or not isinstance(values,dict) or any(type(a) is not int or a not in legal_actions for a in values)
            or type(hero_seat) is not int or not 0<=hero_seat<9):
        raise ValueError('native legal actions, action estimates and valid hero seat required')
    if profile is None:return {**base,'status':'target_policy_unobserved'}
    if (not isinstance(profile,dict) or set(profile)!=set(legal_actions)
            or any(not isinstance(p,Fraction) or p<0 for p in profile.values()) or sum(profile.values())!=1):
        raise ValueError('complete exact normalized target policy required')
    known={}
    for action,row in values.items():
        if row is None or row.get('sample_mean_values') is None:continue
        means=row['sample_mean_values'];intervals=row.get('simultaneous_chip_intervals')
        if (not isinstance(means,(list,tuple)) or not 2<=len(means)<=9 or hero_seat>=len(means)
                or any(not isinstance(v,Fraction) for v in means)
                or not isinstance(intervals,(list,tuple)) or len(intervals)!=len(means)
                or any(not isinstance(pair,(list,tuple)) or len(pair)!=2
                    or any(type(v) not in (int,float) or not math.isfinite(v) for v in pair)
                    or pair[0]>pair[1] for pair in intervals)):
            raise ValueError('exact sample means and finite ordered seat intervals required')
        known[action]=(means[hero_seat],intervals[hero_seat])
    if any(p>0 and a not in known for a,p in profile.items()):
        return {**base,'status':'profile_action_values_missing','known_actions':len(known),
                'legal_actions':len(legal_actions)}
    reference=sum((p*known[a][0] for a,p in profile.items() if p),Fraction())
    lower=sum((p*Fraction(known[a][1][0]) for a,p in profile.items() if p),Fraction())
    upper=sum((p*Fraction(known[a][1][1]) for a,p in profile.items() if p),Fraction())
    best=max(v[0] for v in known.values())
    lo=max(Fraction(0),max(Fraction(v[1][0]) for v in known.values())-upper)
    hi=max(Fraction(0),max(Fraction(v[1][1]) for v in known.values())-lower)
    complete=set(known)==set(legal_actions)
    return {**base,'status':'local_estimate_only','profile_sample_mean':reference,
        'best_evaluated_action_sample_mean':best,'estimated_restricted_gain':max(Fraction(0),best-reference),
        'restricted_gain_interval':[max(0.0,math.nextafter(float(lo),-math.inf)),
                                    math.nextafter(float(hi),math.inf)],
        'all_legal_actions_evaluated':complete,'known_actions':len(known),'legal_actions':len(legal_actions),
        'full_local_gain_upper_bound':math.nextafter(float(hi),math.inf) if complete else None,
        'confidence_scope':'requires simultaneous action intervals for the same fixed policy/belief'}
