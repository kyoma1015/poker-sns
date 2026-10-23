"""Native preflop context -> explicit-mass 169-class frequency export.

Format comes from preserved g11_native_state.h State::info and row() in the
hash-pinned three G12 solvers. Caller reach weights are mandatory; sampled visits,
average-policy counts and uniform guesses are NOT substituted for reach mass.
"""
from fractions import Fraction
import json
import math

from gto.hand169 import aggregate


def card_name(card):
    # Header five(): rank=card/4+2, suit=card%4; reference docs name suits c/d/h/s.
    if type(card) is not int or not 0 <= card < 52:
        raise ValueError('native card must be integer 0..51')
    return '23456789TJQKA'[card//4] + 'cdhs'[card%4]


def _object(raw):
    def no_duplicates(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError('duplicate native infoset field')
            result[key]=value
        return result
    try:
        value=json.loads(raw,object_pairs_hook=no_duplicates,
                         parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    except (TypeError,json.JSONDecodeError) as e:
        raise ValueError('invalid native infoset JSON') from e
    if not isinstance(value,dict) or set(value) != {'hand','board','betting_history','seat','public_config'}:
        raise ValueError('unknown native infoset format')
    hand=value['hand']; board=value['board']; history=value['betting_history']; seat=value['seat']
    if (not isinstance(hand,list) or len(hand)!=2 or len(set(hand))!=2
            or not isinstance(board,list) or len(board) not in (0,3,4,5)
            or any(type(x) is not int or not 0 <= x < 52 for x in hand+board)
            or len(set(hand+board)) != len(hand+board)):
        raise ValueError('invalid native hand/board')
    config=value['public_config']
    if (type(seat) is not int or not isinstance(config,dict)
            or not isinstance(config.get('stacks'),list) or not 2<=len(config['stacks'])<=9
            or not 0<=seat<len(config['stacks']) or not isinstance(history,list)
            or any(not isinstance(row,list) or len(row)!=5 or any(type(x) is not int for x in row) for row in history)):
        raise ValueError('invalid native seat/context')
    return value


def context_of(infoset):
    value=_object(infoset)
    return {key:value[key] for key in ('board','betting_history','public_config','seat')}


def _number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError('explicit finite nonnegative weight required')
    try: valid=math.isfinite(value)
    except OverflowError: valid=False
    if not valid or value<0:raise ValueError('explicit finite nonnegative weight required')
    return Fraction(value)


def export_context(solver, context, reach_weights):
    """One seat/board/history/config/action context, observed coverage only.

    Native ordered-hole infosets collapse by concrete combination using explicitly
    provided mass. Both orderings must remain distinct in the input weight map.
    No missing hand gets an invented policy, no unknown EV gets zero.
    """
    if (not isinstance(context,dict) or set(context)!={'board','betting_history','public_config','seat'}
            or context['board']!=[] or not isinstance(reach_weights,dict)):
        raise ValueError('explicit preflop context and reach-weight map required')
    # Validate the context through the same native schema boundary.
    _object(json.dumps(dict(context,hand=[0,1])))
    selected=[]
    for key in solver.keys():
        info=_object(key)
        if {k:info[k] for k in context}==context: selected.append((key,info))
    if not selected or set(reach_weights)!={key for key,_ in selected}:
        raise ValueError('exact explicit weights for every selected infoset required')
    actions=None; combinations={}
    for key,info in selected:
        weight=_number(reach_weights[key])
        row=solver.row(key)
        offered=row['actions']; average=row['average']
        if (not isinstance(offered,(list,tuple)) or not offered
                or any(type(a) is not int or a<0 for a in offered)
                or len(set(offered))!=len(offered) or not isinstance(average,(list,tuple))
                or len(average)!=len(offered)):
            raise ValueError('invalid native row action identity')
        if actions is None:actions=list(offered)
        elif list(offered)!=actions:raise ValueError('action identity differs within selected context')
        totals=[_number(a) for a in average]; total=sum(totals)
        policy=[a/total for a in totals] if total else [Fraction(1,len(totals))]*len(totals)
        combo=tuple(sorted(card_name(card) for card in info['hand']))
        combinations.setdefault(combo,[]).append((weight,policy))
    records=[]
    for cards,rows in combinations.items():
        mass=sum(w for w,_ in rows)
        # Exact intermediate arithmetic preserves extreme finite ratios; final
        # aggregate is the existing reviewed PR103 component, reused unchanged.
        policy=[float(sum((w*f[a] for w,f in rows),Fraction())/mass) for a in range(len(actions))] if mass else [1/len(actions)]*len(actions)
        try: weight=float(mass)
        except OverflowError as e:raise ValueError('combined reach mass overflow') from e
        if not math.isfinite(weight):raise ValueError('combined reach mass overflow')
        records.append({'cards':list(cards),'weight':weight,'frequencies':policy,'ev':None})
    report=aggregate(records,len(actions),require_complete=False)
    report.update({'actions':actions,'context':context,'observed_infosets':len(selected),
        'weight_provenance':'explicit caller-supplied infoset reach weights',
        'ev_status':'not estimated by native outcome MCCFR table',
        'strategy_convergence':'UNKNOWN'})
    return report
