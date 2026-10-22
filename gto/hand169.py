"""Exact 1,326 concrete two-card combinations -> 169 preflop classes.

This is an export/validation component, not a solver or an EV estimate.
Input weights are caller-supplied reach mass, never inferred from frequencies.
"""
from itertools import combinations
import math

RANKS = 'AKQJT98765432'
SUITS = 'shdc'
DECK = tuple(rank + suit for rank in RANKS for suit in SUITS)
CLASSES = tuple([a + b + ('' if a == b else 's' if i < j else 'o')
                 for i, a in enumerate(RANKS) for j, b in enumerate(RANKS)])
# Matrix lower triangle labels must keep the higher rank first.
CLASSES = tuple(label if len(label) == 2 or label[2] == 's' else label[1]+label[0]+'o' for label in CLASSES)


def hand_class(cards):
    if not isinstance(cards, (list, tuple)) or len(cards) != 2 or any(card not in DECK for card in cards) or cards[0] == cards[1]:
        raise ValueError('two distinct standard rank/suit cards required')
    a, b = sorted(cards, key=lambda card: RANKS.index(card[0]))
    return a[0] + b[0] + ('' if a[0] == b[0] else 's' if a[1] == b[1] else 'o')


def aggregate(records, action_count, *, require_complete=True):
    """Validate and aggregate reach-weighted strategy/EV without hiding gaps.

    records: {cards:[As,Kh], weight:float, frequencies:[...], ev:float|None}.
    Complete export requires all 1,326 distinct concrete combinations. Zero-mass
    classes report None (unknown), never a fabricated all-zero strategy or EV.
    """
    if type(require_complete) is not bool:
        raise ValueError('boolean require_complete required')
    if type(action_count) is not int or action_count < 1:
        raise ValueError('positive integer action_count required')
    buckets = {label: [] for label in CLASSES}
    seen = set()
    for record in records:
        cards = record['cards']; label = hand_class(cards); key = tuple(sorted(cards))
        if key in seen: raise ValueError('duplicate concrete combination')
        seen.add(key)
        weight = record['weight']; frequencies = record['frequencies']; ev = record.get('ev')
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not math.isfinite(weight) or weight < 0:
            raise ValueError('finite nonnegative reach weight required')
        if not isinstance(frequencies, (list, tuple)) or len(frequencies) != action_count or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 or x > 1 for x in frequencies):
            raise ValueError('invalid action frequencies')
        if abs(math.fsum(frequencies) - 1) > 1e-9: raise ValueError('frequencies must sum to one')
        if ev is not None and (isinstance(ev, bool) or not isinstance(ev, (int, float)) or not math.isfinite(ev)):
            raise ValueError('EV must be finite or explicitly unknown')
        # Export iterators may reuse a mutable buffer for their next row.
        buckets[label].append((weight, tuple(frequencies), ev))
    if require_complete and len(seen) != 1326: raise ValueError('incomplete concrete hand coverage')
    output = {}
    for label, rows in buckets.items():
        try:
            mass = math.fsum(row[0] for row in rows)
        except OverflowError as error:
            raise ValueError('reach mass overflow') from error
        if not math.isfinite(mass): raise ValueError('reach mass overflow')
        # Divide weights before multiplying to avoid finite-input overflow.
        policy = [math.fsum((w / mass) * f[action] for w, f, _ in rows) for action in range(action_count)] if mass else None
        ev = math.fsum((w / mass) * e for w, _, e in rows if w > 0) if mass and all(e is not None for w, _, e in rows if w > 0) else None
        if ev is not None and not math.isfinite(ev): raise ValueError('aggregate EV overflow')
        output[label] = {'combinations': len(rows), 'reach_mass': mass, 'frequencies': policy, 'ev': ev}
    return {'schema': 'pokerid-hand169-v1', 'complete': len(seen) == 1326, 'concrete_combinations': len(seen), 'hands': output}
