"""Class-pair reach-weighted adapter for the isolated flop toy tree.

Requires caller-supplied conditional equity and flop policies. It does not
derive them from the frozen preflop CFR strategy or certify full-game GTO.
"""
import math
from gto.abstract.flop_tree_ablation import Policy, evaluate_flop


def conditional_flop_ev(*, stage, class_probability, hero_reach, villain_reach,
                        equity_by_pair, hero_policy, villain_policy,
                        pot_bb, bet_fraction=0.5, raise_multiplier=3.0):
    """Return BB model delta on a fixed, explicitly supplied class-pair distribution.

    class_probability is the ordered compatible-combination probability matrix
    from model.chance. hero_reach/villain_reach are fixed per-class weights at
    the chosen decision history, not learned or adjusted here.
    equity_by_pair is a conditional showdown-equity matrix with the SAME
    ordered seats, conditioning and card-blocker convention.
    """
    if stage not in ("vs_3bet", "vs_4bet"):
        raise ValueError("only explicit facing-3bet/4bet research stages")
    n = 169
    if any(len(x) != n for x in (hero_reach, villain_reach)) or any(len(x) != n*n for x in (class_probability, equity_by_pair)):
        raise ValueError("169 class vectors and ordered 169x169 matrices required")
    if not isinstance(hero_policy, Policy) or not isinstance(villain_policy, Policy):
        raise TypeError("fixed Policy objects required")
    if not isinstance(pot_bb, (float, int)) or not math.isfinite(pot_bb) or pot_bb <= 0:
        raise ValueError("finite positive pot_bb required")
    for seq in (class_probability, hero_reach, villain_reach, equity_by_pair):
        if any(not isinstance(v, (float, int)) or not math.isfinite(v) or v < 0 or v > 1 for v in seq):
            raise ValueError("finite probabilities in [0,1] required")
    mass = 0.0
    baseline = 0.0
    candidate = 0.0
    for i in range(n):
        for j in range(n):
            w = class_probability[i*n+j] * hero_reach[i] * villain_reach[j]
            if w == 0:
                continue
            e = equity_by_pair[i*n+j]
            mass += w
            baseline += w * e
            candidate += w * evaluate_flop(e, hero_policy, villain_policy,
                                            bet_fraction=bet_fraction,
                                            raise_multiplier=raise_multiplier)
    if mass <= 0:
        raise ValueError("zero reach-weighted probability")
    old_bb = baseline / mass * pot_bb
    new_bb = candidate / mass * pot_bb
    return {
        "stage": stage, "old_checkdown_ev_bb": old_bb,
        "new_flop_tree_ev_bb": new_bb,
        "model_delta_bb": new_bb - old_bb,
        "conditional_reach_mass": mass,
        "statistical_error_bb": None,
        "model_approximation_error_bb": None,
        "external_reference_deviation_bb": None,
        "full_game_gto_verified": False,
        "scope": "fixed class-pair reach-weighted toy tree; no flop-conditioned policy optimization"
    }
