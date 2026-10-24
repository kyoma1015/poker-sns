"""Source-scoped exact chance reach for the first native preflop decision.

This is not a general action-history or counterfactual-reach estimator. With a
full uniform 52-card deck and no action, fixture or root-prefix conditioning,
P(ordered own hand)=P(50,2n-2)/P(52,2n)=1/(52*51). Visits and average counts do
not participate in this proof. Other contexts retain PR120's explicit-caller API.
"""
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

from gto.native.hand169_bridge import context_of, export_context
from gto.native.training import NativeGame


def ordered_hand_marginal(players):
    if type(players) is not int or not 2<=players<=9:
        raise ValueError('2..9 players required')
    return Fraction(math.perm(50,2*players-2),math.perm(52,2*players))


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def _verified_game(game):
    if type(game) is not NativeGame or game.fixture is not None or game.root_actions != []:
        raise ValueError('unconditioned NativeGame with no fixture/root prefix required')
    try:
        config=json.loads(game._public_config_json)
        rules=config['rules'];rate=Fraction(rules['rake_rate'])
        canonical=NativeGame(config['stacks'],bb=rules['bb'],bba=rules['bba'],
                             rake_num=rate.numerator,rake_den=rate.denominator)
        if (canonical._public_config_json != game._public_config_json
                or _canonical(canonical.stacks)!=_canonical(game.stacks)
                or _canonical(canonical._native_rules)!=_canonical(game._native_rules)):
            raise ValueError('runtime/public-config drift')
    except (KeyError,TypeError,OverflowError,ZeroDivisionError) as e:
        raise ValueError('invalid canonical native game configuration') from e
    return config


def initial_chance_export(native, solver, game, context):
    """Export observed first-decision policies with mathematically justified mass.

    Full concrete-combination coverage and all2652 ordered-hand observations are
    reported separately; absent ordered policies are never filled. The float
    aggregation uses the correctly rounded rational mass, while evidence retains
    numerator/denominator exactly. AllEV remains unknown, not inferred from reach.
    """
    config=_verified_game(game)
    if not isinstance(solver,native.Solver) or solver.stats().get('native_engine') is not True:
        raise ValueError('actual native-engine solver required')
    state=native.NativeState(game)
    players=len(config['stacks'])
    # Preserve the exact header contract: full remaining deck and uniform card
    # chance on this representative deal; the symbolic permutation calculation
    # marginalizes the other players' cards, it does not enumerate sample visits.
    for card in range(2*players):
        if not state.is_chance_node():raise ValueError('native initial deal diverged')
        outcomes=state.chance_outcomes();remaining=52-card
        if (len(outcomes)!=remaining or {a for a,_ in outcomes}!=set(range(card,52))
                or any(not math.isfinite(p) or abs(p-1/remaining)>1e-15 for _,p in outcomes)):
            raise ValueError('full uniform native card-deal contract not observed')
        state.apply_action(card)
    if state.is_terminal() or state.is_chance_node() or state.current_player()<0:
        raise ValueError('no first preflop decision in this configuration')
    expected=context_of(state.information_state_string(state.current_player()))
    if (not isinstance(context,dict) or _canonical(context)!=_canonical(expected)
            or context['board']!=[] or context['betting_history']!=[]):
        raise ValueError('only the exact first native preflop actor/context is proved')
    probability=ordered_hand_marginal(players)
    selected=[key for key in solver.keys() if context_of(key)==expected]
    # This weight is derived from the deal model, not a uniform policy/visit guess.
    report=export_context(solver,expected,{key:float(probability) for key in selected})
    if report['actions']!=state.legal_actions():
        raise ValueError('native solver row actions do not match the proved game context')
    observed_orderings=len(selected)
    if observed_orderings>2652:raise ValueError('duplicate/unexpected ordered native hand coverage')
    report['weight_provenance']='proven uniform full-deck initial-deal chance marginal; no action history'
    report['reach_evidence']={
        'scope':'initial chance marginal only, not general strategy/counterfactual reach',
        'players':players,'seat':state.current_player(),
        'ordered_hand_probability':{'numerator':probability.numerator,'denominator':probability.denominator},
        'total_ordered_deals':str(math.perm(52,2*players)),
        'other_player_completions':str(math.perm(50,2*players-2)),
        'expected_ordered_hands':2652,'observed_ordered_hands':observed_orderings,
        'complete_ordered_coverage':observed_orderings==2652,
        'public_config_sha256':hashlib.sha256(game._public_config_json.encode()).hexdigest(),
        'native_module_sha256':hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        'float_weight_note':'aggregation uses rounded binary64 1/2652; exact rational is retained above',
        'historical_compatibility':'UNKNOWN','strategy_convergence':'UNKNOWN'}
    return report
