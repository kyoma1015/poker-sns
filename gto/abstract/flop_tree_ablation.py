"""Independent, fixed-policy one-street flop continuation ablation.

This is a conditional toy-game evaluator, NOT a calibrated poker solver.
All payoffs are net from the beginning of this street, in pot units.
Equity is a caller-supplied showdown probability; no card/range inference.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Policy:
    bet: float
    raise_after_bet: float
    call_bet: float
    call_raise: float

    def __post_init__(self):
        for name in ("bet", "raise_after_bet", "call_bet", "call_raise"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be a finite probability")


def _showdown(equity, pot, hero_invested, villain_invested):
    # Hero net profit: wins existing pot plus villain's additional contribution,
    # loses hero's additional contribution. Ties split both contributions.
    return equity * (pot + villain_invested) - (1 - equity) * hero_invested


def evaluate_flop(equity, hero: Policy, villain: Policy, *, pot=1.0, bet_fraction=0.5, raise_multiplier=3.0):
    """Evaluate a fixed-policy, IP hero vs OOP villain flop tree.

    OOP villain checks or bets. Following a check, IP hero checks or bets.
    A bet may be called, folded, or raised once; a raise may be called or folded.
    Policies are conditional probabilities. After the flop, all hands check
    through to showdown; equity is not updated on turns/rivers.
    """
    if not isinstance(equity, (int, float)) or not math.isfinite(equity) or not 0 <= equity <= 1:
        raise ValueError("equity must be in [0,1]")
    if not math.isfinite(pot) or pot <= 0 or not math.isfinite(bet_fraction) or bet_fraction <= 0:
        raise ValueError("pot and bet fraction must be positive finite")
    if not math.isfinite(raise_multiplier) or raise_multiplier < 2:
        raise ValueError("raise multiplier must be at least 2")
    b = pot * bet_fraction
    r = b * raise_multiplier

    # Villain bets first: hero folds, calls, or raises to r total.
    hero_raise = (1 - villain.call_raise) * (pot + b) + villain.call_raise * _showdown(equity, pot, r, r)
    hero_faces_bet = (
        (1 - hero.call_bet) * (1 - hero.raise_after_bet) * (-0.0)
        + hero.call_bet * (1 - hero.raise_after_bet) * _showdown(equity, pot, b, b)
        + hero.raise_after_bet * hero_raise
    )

    # Villain checks: hero checks, or bets; villain can raise to r.
    hero_faces_raise = (1 - hero.call_raise) * (-b) + hero.call_raise * _showdown(equity, pot, r, r)
    hero_bets = (
        (1 - villain.call_bet) * (1 - villain.raise_after_bet) * pot
        + villain.call_bet * (1 - villain.raise_after_bet) * _showdown(equity, pot, b, b)
        + villain.raise_after_bet * hero_faces_raise
    )
    hero_after_check = (1 - hero.bet) * _showdown(equity, pot, 0, 0) + hero.bet * hero_bets
    return villain.bet * hero_faces_bet + (1 - villain.bet) * hero_after_check


def compare_to_checkdown(equity, hero, villain, **kwargs):
    pot = kwargs.get("pot", 1.0)
    baseline = equity * pot
    candidate = evaluate_flop(equity, hero, villain, **kwargs)
    return {"checkdown_ev_pot_units": baseline, "flop_tree_ev_pot_units": candidate,
            "model_delta_pot_units": candidate - baseline,
            "statistical_error": None, "real_game_approximation_error": None,
            "external_gto_deviation": None, "validated_gto": False}
