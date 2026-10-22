"""Exact best-response metrics for a fixed synthetic matching-pennies game.

This component evaluates a supplied profile. It neither trains a solver nor
establishes convergence, poker accuracy or historical G11 compatibility.
"""
import math


def _policy(values):
    if not isinstance(values, (list, tuple)) or len(values) != 2:
        raise ValueError('a two-action probability list or tuple is required')
    if any(type(value) not in (int, float) or not 0 <= value <= 1
           or not math.isfinite(value) for value in values):
        raise ValueError('probabilities must be finite numbers in [0, 1]')
    if not math.isclose(math.fsum(values), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError('probabilities must sum to one')
    return tuple(values)


def matching_pennies_metrics(policy0, policy1):
    """Evaluate P0 match=+1/mismatch=-1, with P1 receiving the opposite payoff.

    Inputs are checked without normalization or mutation. Each best-response
    value assumes only that player's action is changed, holding the opponent's
    supplied policy fixed. NashConv sums both improvements; exploitability here
    is half that gap for this two-player zero-sum toy game only.
    """
    p0, p1 = _policy(policy0), _policy(policy1)
    difference0 = p0[0] - p0[1]
    difference1 = p1[0] - p1[1]
    utility0 = difference0 * difference1
    utility1 = -utility0
    best0, best1 = abs(difference1), abs(difference0)
    gap = math.fsum((best0 - utility0, best1 - utility1))
    return {
        'game': 'synthetic-matching-pennies-v1',
        'utility_p0': utility0,
        'utility_p1': utility1,
        'best_response_p0': best0,
        'best_response_p1': best1,
        'nash_conv': gap,
        'exploitability': gap / 2,
        'strategy_convergence_proof': False,
        'historical_baseline_used': False,
    }
