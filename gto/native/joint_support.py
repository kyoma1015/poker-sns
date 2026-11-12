"""Seat-labelled ordered private-deal priors with exact multiway card removal.

Input prior mass is explicit, not inferred from visits. Reversed hole-card order
is a different native deal/information key. Seat swaps are different deals too.
Independent-range products are labelled products, never claimed as learned
posteriors. Bounded enumeration fails instead of pruning or renormalizing a tail.
"""
from fractions import Fraction
from itertools import product
import math
from gto.native.belief_observation import _cards


def _inputs(players, hero_seat, hero_cards, public_cards):
    if (type(players) is not int or not 2<=players<=9 or type(hero_seat) is not int
            or not 0<=hero_seat<players):
        raise ValueError('2..9 players and valid hero seat required')
    hero=tuple(_cards(hero_cards,2));board=tuple(_cards(public_cards))
    if len(board) not in (0,3,4,5) or set(hero)&set(board):
        raise ValueError('valid disjoint observed hero/public cards required')
    return hero,board


def _assignment(players,hero_seat,hero,board,hands):
    if not isinstance(hands,(list,tuple)) or len(hands)!=players-1:
        raise ValueError('one ordered hand per non-hero seat required')
    opponents=[tuple(_cards(hand,2)) for hand in hands]
    full=list(opponents);full.insert(hero_seat,hero)
    flat=[card for hand in full for card in hand]
    compatible=len(set(flat))==len(flat) and not set(flat)&set(board)
    return tuple(full),compatible


def _summary(players,hero_seat,hero,board,retained,mass,original_size,provenance):
    full_count=math.perm(50-len(board),2*(players-1))
    positive=sum(bool(prior) for _,prior in retained)
    return {'players':players,'hero_seat':hero_seat,'hero_cards':list(hero),
        'public_cards':list(board),
        'deals':[(hands,prior/mass) for hands,prior in retained] if mass else [],
        'compatible_prior_mass':mass,'removed_prior_mass':1-mass,
        'original_support_size':original_size,'positive_compatible_deals':positive,
        'full_ordered_opponent_deals':str(full_count),
        'uniform_ordered_support_fraction':Fraction(positive,full_count),
        'support_complete':positive==full_count,
        'prior_provenance':provenance,'equilibrium_verified':False}


def condition_joint_support(players,hero_cards,deals,public_cards=(),*,hero_seat=0,max_deals=128):
    """Condition a normalized explicit joint prior on all private/public blockers.

    `deals` rows are (opponent hands by increasing seat excluding hero, prior).
    Invalid cards/duplicate ordered assignments fail. Cross-seat/hero/board
    collisions remove probability mass, which remains explicitly accounted for.
    """
    hero,board=_inputs(players,hero_seat,hero_cards,public_cards)
    if (type(max_deals) is not int or not 1<=max_deals<=1000000
            or not isinstance(deals,(list,tuple)) or not 1<=len(deals)<=max_deals):
        raise ValueError('bounded nonempty explicit joint support required')
    seen=set();retained=[];mass=Fraction(0);total=Fraction(0)
    for item in deals:
        if not isinstance(item,(list,tuple)) or len(item)!=2:
            raise ValueError('joint opponent hands/prior pair required')
        hands,prior=item
        if not isinstance(prior,Fraction) or prior<0:
            raise ValueError('exact nonnegative joint prior required')
        full,compatible=_assignment(players,hero_seat,hero,board,hands)
        if full in seen:raise ValueError('duplicate ordered joint deal')
        seen.add(full);total+=prior
        if compatible:retained.append((full,prior));mass+=prior
    if total!=1:raise ValueError('joint prior must sum exactly to one')
    return _summary(players,hero_seat,hero,board,retained,mass,len(deals),
                    'explicit normalized joint prior; not inferred from visits')


def product_support(players,hero_cards,ranges,public_cards=(),*,hero_seat=0,
                    max_candidates=100000,max_deals=10000):
    """Enumerate declared independent seat ranges, then condition on collisions.

    Ranges map each non-hero seat to (ordered cards, normalized Fraction mass)
    rows. Input native card order is preserved. Supply both orderings explicitly
    if the prior covers both; suit/ordering invariance is never assumed.
    """
    hero,board=_inputs(players,hero_seat,hero_cards,public_cards)
    seats=[seat for seat in range(players) if seat!=hero_seat]
    if (not isinstance(ranges,dict) or any(type(s) is not int for s in ranges)
            or set(ranges)!=set(seats) or type(max_candidates) is not int
            or not 1<=max_candidates<=1000000 or type(max_deals) is not int
            or not 1<=max_deals<=1000000):
        raise ValueError('all opponent ranges and finite enumeration budgets required')
    copied=[]
    for seat in seats:
        rows=ranges[seat]
        if not isinstance(rows,(list,tuple)) or not rows or len(rows)>max_candidates:
            raise ValueError('bounded nonempty ordered seat range required')
        clean=[];seen=set();total=Fraction(0)
        for item in rows:
            if not isinstance(item,(list,tuple)) or len(item)!=2:raise ValueError('cards/mass required')
            hand,prior=item;hand=tuple(_cards(hand,2))
            if hand in seen or not isinstance(prior,Fraction) or prior<0:
                raise ValueError('unique ordered hands and exact nonnegative mass required')
            seen.add(hand);total+=prior;clean.append((hand,prior))
        if total!=1:raise ValueError('each seat range must sum exactly to one')
        copied.append(clean)
    count=math.prod(len(rows) for rows in copied)
    if count>max_candidates:raise ValueError('joint candidate budget exceeded; no range pruned')
    retained=[];mass=Fraction(0)
    for combination in product(*copied):
        full,compatible=_assignment(players,hero_seat,hero,board,[row[0] for row in combination])
        prior=math.prod(row[1] for row in combination)
        if compatible:
            if len(retained)>=max_deals:raise ValueError('retained joint support budget exceeded')
            retained.append((full,prior));mass+=prior
    return _summary(players,hero_seat,hero,board,retained,mass,count,
                    'declared independent seat-range product conditioned on blockers; not learned range')
