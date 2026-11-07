"""Exact full-deck HU preflop reach, including both private-card orders.

Products of public-history policy likelihoods factor by acting seat until the
first board card. Blocker incidence sums replace6.5million repeated joint deals;
no uniform action reach, visits or sampled opponent subset is substituted.
Unknown positive-prefix factors make the result unavailable, never zero.
"""
from fractions import Fraction as F
from itertools import permutations
import json,math
from gto.hand169 import CLASSES,hand_class
from gto.native.hand169_bridge import card_name,context_of
from gto.native.preflop import decision,describe

PAIRS=tuple(permutations(range(52),2))


def blocker_sums(factors):
    if (not isinstance(factors,dict) or set(factors)!=set(PAIRS)
            or any(not isinstance(v,F) or v<0 or v>1 for v in factors.values())):
        raise ValueError('all2652 exact ordered opponent likelihoods required')
    denominator=math.lcm(*(v.denominator for v in factors.values()))
    values={pair:v.numerator*(denominator//v.denominator) for pair,v in factors.items()}
    incident=[0]*52;total=0
    for (a,b),v in values.items():total+=v;incident[a]+=v;incident[b]+=v
    compatible={pair:total-incident[pair[0]]-incident[pair[1]]+values[pair]+values[pair[::-1]] for pair in PAIRS}
    if any(v<0 for v in compatible.values()):raise ValueError('negative compatible likelihood')
    return compatible,denominator


def reached_classes(native,solver,game,history):
    from gto.native.initial_chance_reach import _verified_game
    _verified_game(game)
    if game.num_players()!=2 or not history:raise ValueError('HU nonempty public preflop prefix required')
    target=decision(native,game,history);desc=describe(target);hero=target.current_player()
    contexts=[context_of(decision(native,game,history[:i]).information_state_string(
        decision(native,game,history[:i]).current_player())) for i in range(len(history)+1)]
    def identity(c):return json.dumps(c,sort_keys=True,separators=(',',':'))
    lookup={identity(c):{} for c in contexts}
    for key in solver.keys():
        info=json.loads(key)
        if info['board']:continue
        ctx=identity({k:info[k] for k in ('board','betting_history','public_config','seat')})
        if ctx in lookup:lookup[ctx][tuple(info['hand'])]=key
    factors=[dict.fromkeys(PAIRS,F(1)),dict.fromkeys(PAIRS,F(1))]
    for index,action in enumerate(history):
        actor=contexts[index]['seat'];keys=lookup[identity(contexts[index])]
        for pair in PAIRS:
            row=solver.row(keys[pair]) if pair in keys else None
            value=None
            if row is not None and type(row.get('updates')) is int and row['updates']>0:
                if action not in row['actions']:raise ValueError('prefix action/learned row differs')
                total=sum((F(v) for v in row['average']),F(0))
                if total<=0:raise ValueError('updated policy not normalized')
                value=F(row['average'][row['actions'].index(action)])/total
            previous=factors[actor][pair]
            factors[actor][pair]=(F(0) if previous==0 or value==0 else
                previous*value if previous is not None and value is not None else None)
    missing=sum(v is None for v in factors[1-hero].values())
    result={'stage':desc['stage'],'history':list(history),'seat':hero,'actions':desc['legal_actions'],'expected_orderings':2652,
        'complete_frequency_classes':0,'missing_opponent_factor_orderings':missing,
        'arithmetic':'exact rational seat-factor products and blocker inclusion-exclusion; final frequencies rounded to binary64',
        'reach_model':'full uniform52card HU deal; ordered hero1/2652, compatible ordered opponent1/2450',
        'full_game_convergence_verified':False,'ev_bb':None,
        'scope':'history-conditioned learned frequencies only; not a GTO certificate or EV estimate'}
    if missing:return {**result,'status':'opponent_prefix_policy_missing','hands':None}
    compatible,denominator=blocker_sums(factors[1-hero])
    groups={label:[] for label in CLASSES}
    for pair in PAIRS:groups[hand_class([card_name(c) for c in pair])].append(pair)
    keys=lookup[identity(contexts[-1])];actions=target.legal_actions();hands={}
    for label,pairs in groups.items():
        selected=[];unknown=False
        for pair in pairs:
            if not compatible[pair]:continue
            own=factors[hero][pair]
            if own is None:unknown=True;continue
            if not own:continue
            row=solver.row(keys[pair]) if pair in keys else None
            if row is None or type(row.get('updates')) is not int or row['updates']<=0:
                unknown=True;continue
            if row['actions']!=actions:raise ValueError('target action identity differs')
            values=[F(v) for v in row['average']];total=sum(values)
            if total<=0 or any(v<0 for v in values):raise ValueError('target learned average unavailable')
            scale=math.lcm(*(v.denominator for v in values))
            integers=[v.numerator*(scale//v.denominator) for v in values]
            selected.append((compatible[pair],own,integers,sum(integers)))
        frequency=None
        if not unknown and selected:
            own_den=math.lcm(*(own.denominator for _,own,_,_ in selected))
            policy_den=math.lcm(*(total for _,_,_,total in selected))
            numerator=[0]*len(actions);mass=0
            for compatible_mass,own,integers,total in selected:
                weight=compatible_mass*own.numerator*(own_den//own.denominator)
                mass+=weight
                scale=policy_den//total
                numerator=[a+weight*v*scale for a,v in zip(numerator,integers)]
            # Exact integer numerator/denominator arithmetic; only the final
            # ratio is rounded for transport. Avoid gigantic rational GCDs.
            frequency=[v/(mass*policy_den) for v in numerator]
        hands[label]={'frequencies':frequency,'reach_known':not unknown,'positive_reach':bool(selected) if not unknown else None,'ev_bb':None}
    return {**result,'status':'computed_with_explicit_missing_target_rows','hands':hands,
        'complete_frequency_classes':sum(h['frequencies'] is not None for h in hands.values()),
        'opponent_factor_common_denominator_bits':denominator.bit_length()}
