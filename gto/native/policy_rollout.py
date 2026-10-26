"""Bounded Monte Carlo chip EV for a fixed explicit native policy.

Intervals bound sampling error conditional on the supplied complete state and
policy. They do not bound opponent-belief error or distance from equilibrium.
Missing learned policy rows propagate errors; no fallback strategy is invented.
"""
from fractions import Fraction
import math
import random
from gto.native.history_reach import _chance, _strategy


def policy_value(state, policy, *, samples, seed, confidence=0.95, max_steps=1000):
    if (type(samples) is not int or not 1 <= samples <= 100000
            or type(seed) is not int or not callable(policy)
            or type(max_steps) is not int or not 1 <= max_steps <= 10000
            or type(confidence) not in (int,float) or not math.isfinite(confidence)
            or not 0 < confidence < 1):
        raise ValueError('bounded samples/steps, integer seed and confidence in (0,1) required')
    start = state.clone()
    audit = start.audit()
    initial = audit['initial']
    players = audit['n']
    if len(initial) != players or not 2 <= players <= 9 or any(type(s) is not int or s <= 0 for s in initial):
        raise ValueError('native initial stack bounds required')
    total = sum(initial)
    sums = [0]*players
    rake_sum = 0
    rng = random.Random(seed)
    for _ in range(samples):
        node = start.clone()
        steps = 0
        while not node.is_terminal():
            if steps >= max_steps:
                raise ValueError('rollout step budget exceeded; no partial EV returned')
            if node.is_chance_node():
                outcomes = list(_chance(node))
                action = outcomes[rng.randrange(len(outcomes))]
            else:
                probabilities = _strategy(node, policy)
                denominator = math.lcm(*(p.denominator for p in probabilities.values()))
                ticket = rng.randrange(denominator)
                for action, mass in probabilities.items():
                    ticket -= mass.numerator*(denominator//mass.denominator)
                    if ticket < 0:
                        break
                else:
                    raise ValueError('invalid normalized policy')
            node.apply_action(action)
            steps += 1
        settlement = node.settlement()
        values = settlement['net']
        rake = settlement['rake']
        if (len(values) != players or any(type(v) is not int or not -initial[p] <= v <= total-initial[p]
                for p,v in enumerate(values)) or sum(values) != -rake):
            raise ValueError('terminal chip conservation or utility bound failed')
        sums = [a+b for a,b in zip(sums,values)]
        rake_sum += rake
    # Union bound makes the advertised confidence simultaneous across all seats.
    radius = total*math.sqrt(math.log(2*players/(1-confidence))/(2*samples))
    means = [Fraction(value,samples) for value in sums]
    return {'values':means, 'samples':samples, 'seed':seed, 'confidence':confidence,
            'simultaneous_chip_intervals':[[max(-initial[p],float(mean)-radius),
                min(total-initial[p],float(mean)+radius)] for p,mean in enumerate(means)],
            'mean_rake':Fraction(rake_sum,samples), 'method':'iid native policy rollouts; Hoeffding + seat union bound',
            'scope':'fixed complete state and explicit policy; not infoset/equilibrium EV',
            'native_infoset_ev':None, 'hand169_ev':None, 'strategy_convergence':'UNKNOWN'}
