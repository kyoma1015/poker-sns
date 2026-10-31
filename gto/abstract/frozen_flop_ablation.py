"""Explicit research bridge: frozen preflop reach + sampled showdown equity.

The existing all-in kernel is UNCONDITIONAL on a specific flop. Consequently
these EV differences are a model ablation, not flop-conditioned GTO estimates.
No policy is trained or modified.
"""
import math
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.flop_reach_adapter import conditional_flop_ev


def evaluate_frozen_ablation(stage, strategy, kernel, hero_policy, villain_policy,
                             *, pot_bb, bet_fraction=0.5, raise_multiplier=3):
    reach = frozen_reach(stage, strategy)
    n = 169
    if not isinstance(kernel, dict) or "mean" not in kernel or len(kernel["mean"]) < n*n:
        raise ValueError("complete showdown kernel required")
    if kernel.get("models", ["allin_showdown"])[0] != "allin_showdown":
        raise ValueError("first kernel plane must be all-in showdown")
    # Kernel plane zero stores signed net chips for a 100-chip matched
    # showdown. Converting this to equity is only valid for zero-rake,
    # zero-side-pot HU winner/tie split; clip only rounding noise.
    equities = []
    for value in kernel["mean"][:n*n]:
        if not isinstance(value, (int, float)) or not math.isfinite(value) or not -100.0000001 <= value <= 100.0000001:
            raise ValueError("invalid all-in showdown payoff")
        equities.append(min(1., max(0., (value / 100. + 1.) / 2.)))
    result = conditional_flop_ev(
        stage=stage, class_probability=reach["class_probability"],
        hero_reach=reach["hero_reach"], villain_reach=reach["villain_reach"],
        equity_by_pair=equities, hero_policy=hero_policy,
        villain_policy=villain_policy, pot_bb=pot_bb,
        bet_fraction=bet_fraction, raise_multiplier=raise_multiplier)
    result["equity_source"] = "all-in showdown kernel, unconditional over public boards"
    result["policy_source"] = "caller-supplied fixed flop toy policy; NOT derived from CFR"
    result["sampling_error_bb"] = None
    result["model_approximation_error_bb"] = None
    result["external_gto_deviation_bb"] = None
    result["full_game_gto_verified"] = False
    return result
