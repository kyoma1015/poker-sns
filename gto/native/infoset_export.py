"""Provenance-bound finite explicit-belief action reports, not equilibrium EV.

Records are immutable data contracts, not signed attestations of execution. The
caller supplies exact hero reach weights and explicit opponent beliefs; neither
visits nor uniform guesses are silently used as reach. No native/169 EV is filled.
"""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from types import MappingProxyType

from gto.hand169 import CLASSES,hand_class
from gto.native.hand169_bridge import card_name
from gto.native.belief_observation import compare_hero_actions,_cards


def _digest(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class UnknownPolicyRow(ValueError):
    """No observed policy at the requested native information key."""


class PolicySnapshot:
    """Immutable explicit native-information-key policies with exact row identity.

    Missing rows fail closed. Values are rational, not rounded serialized floats.
    This may describe a deliberately bounded policy; it is not a solved strategy.
    """
    __slots__=('_rows','digest','_frozen')
    def __init__(self,rows,*,max_rows=100000):
        if (type(max_rows) is not int or not 1<=max_rows<=1000000 or not isinstance(rows,dict)
                or not 1<=len(rows)<=max_rows):raise ValueError('bounded nonempty policy rows required')
        copied={}
        for key,row in rows.items():
            if (not isinstance(key,str) or not key or not isinstance(row,dict) or not row
                    or any(type(a) is not int or not isinstance(p,Fraction) or p<0 for a,p in row.items())
                    or sum(row.values())!=1):raise ValueError('exact normalized native policy row required')
            copied[key]=MappingProxyType(dict(row))
        object.__setattr__(self,'_rows',MappingProxyType(copied))
        object.__setattr__(self,'digest',_digest([[key,[[a,str(p)] for a,p in sorted(row.items())]] for key,row in sorted(copied.items())]))
        object.__setattr__(self,'_frozen',True)
    @classmethod
    def from_solver(cls,native,solver,*,max_rows=100000):
        """Copy observed native averages; absent/unvisited rows stay unavailable.

        Caller must exclude concurrent training. Iteration/RNG/key checks detect
        ordinary mutation; they are not a synchronization primitive.
        """
        from gto.native.history_reach import native_average_policy
        import math
        native_average_policy(native,solver)
        iteration=solver.iteration;rng=solver.rng_state();keys=tuple(solver.keys())
        if type(max_rows) is not int or not 1<=max_rows<=1000000 or len(keys)>max_rows:
            raise ValueError('snapshot exceeds row budget')
        rows={}
        for key in keys:
            row=solver.row(key);actions=row['actions'];values=row['average']
            if (not actions or len(actions)!=len(values) or len(set(actions))!=len(actions)
                    or any(type(a) is not int for a in actions)
                    or any(type(p) not in (int,float) or not math.isfinite(p) or p<0 for p in values)):
                raise ValueError('invalid observed native policy row')
            exact=[Fraction(p) for p in values];total=sum(exact)
            if total:rows[key]={a:p/total for a,p in zip(actions,exact)}
        if solver.iteration!=iteration or solver.rng_state()!=rng or tuple(solver.keys())!=keys:
            raise ValueError('solver changed during snapshot')
        return cls(rows,max_rows=max_rows)
    def __setattr__(self,key,value):raise AttributeError('policy snapshot is immutable')
    def observed_row(self,state):
        """Return a copied observed row or None; never fabricate missing policy."""
        if state.is_terminal() or state.is_chance_node():raise ValueError('decision policy required')
        key=state.information_state_string(state.current_player());row=self._rows.get(key)
        if row is None:return None
        if set(row)!=set(state.legal_actions()):raise ValueError('snapshot actions differ')
        return dict(row)
    def __call__(self,state):
        row=self.observed_row(state)
        if row is None:raise UnknownPolicyRow('snapshot row missing or actions differ')
        return row


@dataclass(frozen=True)
class ComboActionRecord:
    cards: tuple
    public_cards: tuple
    actions: tuple
    action_values: tuple | None
    hero_mass: Fraction
    observation_digest: str
    config_digest: str
    policy_digest: str
    hero_information_digest: str | None
    support_digest: str
    support_size: int
    support_complete: bool
    observation_evidence_mass: Fraction
    hero_counterfactual_mass: Fraction


def evaluate_combo(native,game,hero_cards,deals,public_cards,history,actions,policy,hero_mass,**budgets):
    """Compute one hero-combo record via the existing real native action oracle.

    The digest excludes private hero/opponent cards from the shared observation,
    but includes exact game configuration/history/board/action identity. Opponent
    support has its own digest. Hero mass is explicit caller-supplied reach, not
    the conditional posterior or actor-excluded counterfactual mass.
    """
    if type(policy) is not PolicySnapshot or not isinstance(hero_mass,Fraction) or hero_mass<0:
        raise ValueError('immutable exact policy and nonnegative exact hero reach required')
    hero=_cards(hero_cards,2);board=_cards(public_cards)
    result=compare_hero_actions(native,game,hero,deals,board,history,actions,policy,**budgets)
    config=json.loads(game._public_config_json)
    observation={'config':config,'board':board,'history':list(history),'seat':0,'actions':list(actions)}
    values=result['action_values']
    values=(tuple(values[a][0] for a in actions) if values and all(values[a] is not None for a in actions) else None)
    return ComboActionRecord(tuple(sorted(hero)),tuple(board),tuple(actions),values,hero_mass,
        _digest(observation),_digest(config),policy.digest,result.get('hero_information_sha256'),
        _digest([[sorted(cards),str(prior)] for cards,prior in deals]),len(deals),False,
        result['observation_evidence_mass'],result['hero_counterfactual_mass'])


def export_action_classes(records,*,max_records=1326):
    """169 rows with explicit coverage and separate partial observed action means.

    A complete-class mean is exposed only when all board-compatible combinations
    have supplied records and every positive-reach row has computed action values.
    Even that value is conditional on caller explicit beliefs, not native infoset
    EV, full opponent coverage, or equilibrium. All generic EV fields remain null.
    """
    if (type(max_records) is not int or not 1<=max_records<=1326 or not isinstance(records,(list,tuple))
            or not 1<=len(records)<=max_records or any(type(r) is not ComboActionRecord for r in records)):
        raise ValueError('bounded nonempty combo records required')
    first=records[0]
    if (not isinstance(first.actions,tuple) or not first.actions or len(set(first.actions))!=len(first.actions)
            or any(type(a) is not int for a in first.actions)):
        raise ValueError('nonempty unique integer action identity required')
    signature=(first.public_cards,first.actions,first.observation_digest,first.config_digest,first.policy_digest)
    eligible={label:0 for label in CLASSES};buckets={label:[] for label in CLASSES};seen=set()
    board=set(_cards(first.public_cards))
    for pair in combinations([c for c in range(52) if c not in board],2):
        eligible[hand_class([card_name(c) for c in pair])]+=1
    for r in records:
        if (r.public_cards,r.actions,r.observation_digest,r.config_digest,r.policy_digest)!=signature:
            raise ValueError('observation/config/policy/actions must be identical')
        cards=tuple(sorted(_cards(r.cards,2)))
        if set(cards)&board or cards in seen:raise ValueError('duplicate or blocked hero combination')
        if (not isinstance(r.hero_mass,Fraction) or r.hero_mass<0
                or r.action_values is not None and (len(r.action_values)!=len(r.actions)
                    or any(not isinstance(v,Fraction) for v in r.action_values))):
            raise ValueError('exact mass and action values required')
        seen.add(cards);buckets[hand_class([card_name(c) for c in cards])].append(r)
    hands={}
    for label,rows in buckets.items():
        mass=sum((r.hero_mass for r in rows),Fraction())
        known=mass>0 and all(r.action_values is not None for r in rows if r.hero_mass)
        means=([sum((r.hero_mass*r.action_values[a] for r in rows if r.hero_mass),Fraction())/mass
                for a in range(len(first.actions))] if known else None)
        complete=len(rows)==eligible[label]
        hands[label]={'observed_combinations':len(rows),'eligible_combinations':eligible[label],
            'coverage_complete':complete,'explicit_hero_mass':mass,'observed_action_values':means,
            'complete_class_action_values':means if complete else None,'ev':None}
    return {'schema':'pokerid-explicit-belief-action169-v1','actions':list(first.actions),'hands':hands,
        'concrete_combinations':len(seen),'public_cards':list(first.public_cards),
        'combo_provenance':[{'cards':list(r.cards),'hero_information_digest':r.hero_information_digest,
            'support_digest':r.support_digest,'support_size':r.support_size,'support_complete':r.support_complete,
            'action_values':list(r.action_values) if r.action_values is not None else None,
            'explicit_hero_mass':r.hero_mass,'observation_evidence_mass':r.observation_evidence_mass,
            'hero_counterfactual_mass':r.hero_counterfactual_mass} for r in records],
        'observation_digest':first.observation_digest,
        'config_digest':first.config_digest,'policy_digest':first.policy_digest,
        'weight_provenance':'explicit caller-supplied exact hero reach; not inferred from visits',
        'support_complete':False,'native_infoset_ev':None,'hand169_ev':None,
        'scope':'finite explicit-belief action values, not full-strategy or equilibrium EV',
        'strategy_convergence':'UNKNOWN'}


def report_json(report):
    """Exact JSON transport: rationals carry decimal numerator/denominator strings.

    Strings avoid JavaScript integer precision loss. Clients must not interpret
    the tagged rational object as a normalized policy or a computed missing EV.
    """
    def exact(value):
        if isinstance(value,Fraction):
            return {'rational':{'numerator':str(value.numerator),'denominator':str(value.denominator)}}
        if isinstance(value,dict):return {key:exact(item) for key,item in value.items()}
        if isinstance(value,(list,tuple)):return [exact(item) for item in value]
        return value
    return json.dumps(exact(report),sort_keys=True,separators=(',',':'),allow_nan=False)
