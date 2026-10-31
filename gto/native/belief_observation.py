"""Bounded public-card conditioning and observed hero-policy consistency.

No complete information-set strategy or equilibrium proof is implied. Explicit
support priors and public observation likelihood remain separate quantities.
"""
from fractions import Fraction
from gto.native.history_reach import _strategy,trace_history,bounded_belief_value


def _cards(cards, count=None):
    if (not isinstance(cards,(list,tuple)) or count is not None and len(cards)!=count
            or any(type(c) is not int or not 0<=c<52 for c in cards)
            or len(set(cards))!=len(cards)):
        raise ValueError('distinct integer cards required')
    return list(cards)


def condition_public_cards(hero_cards,deals,public_cards,*,max_deals=128):
    """Filter explicit support blockers, retaining exact removed/retained mass.

    This conditions only on compatibility. Public draw probability and strategy
    likelihood must still be applied through an actual native legal history.
    """
    hero=_cards(hero_cards,2);board=_cards(public_cards)
    if len(board)>5 or set(hero)&set(board):raise ValueError('invalid public cards')
    if (type(max_deals) is not int or not 1<=max_deals<=10000
            or not isinstance(deals,(list,tuple)) or not 1<=len(deals)<=max_deals):
        raise ValueError('bounded nonempty support required')
    seen=set();compatible=[];mass=Fraction(0);total=Fraction(0)
    for item in deals:
        if not isinstance(item,(list,tuple)) or len(item)!=2:raise ValueError('cards/prior pair required')
        cards,prior=item;cards=_cards(cards,2);identity=tuple(sorted(cards))
        if (set(cards)&set(hero) or identity in seen or not isinstance(prior,Fraction) or prior<0):
            raise ValueError('disjoint unique hands and exact nonnegative priors required')
        seen.add(identity);total+=prior
        if not set(cards)&set(board):compatible.append((cards,prior));mass+=prior
    if total!=1:raise ValueError('prior must sum exactly to one')
    return {'deals':[(cards,p/mass) for cards,p in compatible] if mass else [],
            'compatible_prior_mass':mass,'removed_prior_mass':1-mass,
            'original_support_size':len(deals),'support_complete':False}


def infoset_consistent_policy(policy,*,player=0,max_infosets=100000):
    """Reject differing queried policies at the same native hero information key.

    Checks only nodes actually visited, not unqueried full strategy. Opponent
    policy is not constrained here. This is a bounded sequential oracle wrapper,
    not synchronization for concurrent callers.
    """
    if (not callable(policy) or type(player) is not int or not 0<=player<9
            or type(max_infosets) is not int or not 1<=max_infosets<=1000000):
        raise ValueError('bounded policy and valid player required')
    seen={}
    def checked(node):
        probabilities=_strategy(node,policy)
        if node.current_player()==player:
            key=node.information_state_string(player)
            signature=(tuple(node.legal_actions()),tuple((a,probabilities.get(a,Fraction(0))) for a in node.legal_actions()))
            if key in seen:
                if seen[key]!=signature:raise ValueError('hero policy differs at identical queried infoset')
            else:
                if len(seen)>=max_infosets:raise ValueError('infoset consistency budget exceeded')
                seen[key]=signature
        return dict(probabilities)
    return checked


def evaluate_observation(native,game,hero_cards,deals,public_cards,history,policy,*,
                         max_deals=128,max_nodes=10000,max_infosets=100000):
    """Conditional finite support EV with explicit compatibility mass accounting."""
    conditioned=condition_public_cards(hero_cards,deals,public_cards,max_deals=max_deals)
    if (not isinstance(history,(list,tuple)) or len(history)>1000
            or any(type(a) is not int for a in history)
            or type(max_nodes) is not int or not 1<=max_nodes<=1000000):
        raise ValueError('bounded explicit history and EV budget required')
    root=native.NativeState(game)
    if root.audit().get('n')!=2:raise ValueError('heads-up observation oracle required')
    checked=infoset_consistent_policy(policy,max_infosets=max_infosets)
    compatible=conditioned['deals'];mass=conditioned['compatible_prior_mass']
    if not compatible:
        return {**conditioned,'conditional_ev':None,'posterior':None,
                'observation_evidence_mass':Fraction(0),'native_infoset_ev':None,
                'hand169_ev':None,'history_validated':False,
                'scope':'empty compatible support; history not evaluable'}
    # Every compatible hand receives the same public action history in the
    # underlying strict oracle. Here verify that the advertised observation is
    # exactly what that history reveals, rather than conditioning on future cards.
    state=root.clone()
    for card in list(hero_cards)+compatible[0][0]:state.apply_action(card)
    trace=trace_history(state,history,checked)
    if trace['state'].audit()['board']!=list(public_cards):
        raise ValueError('public observation differs from replayed native board')
    result=bounded_belief_value(native,game,hero_cards,compatible,history,checked,
                               max_deals=max_deals,max_nodes=max_nodes)
    return {**result,**conditioned,
            'observation_evidence_mass':mass*result['evidence_mass'],
            'history_validated':True,'policy_consistency':'queried hero infosets only',
            'scope':'conditional explicit support and queried-consistent hero policy; not equilibrium'}


def compare_hero_actions(native,game,hero_cards,deals,public_cards,history,actions,policy,*,
                         max_deals=128,max_nodes=10000,max_actions=64,max_infosets=100000):
    """Finite common-infoset do-action values under an explicit observed belief.

    The prefix posterior is shared by all interventions, with no target policy
    probability multiplied into an action value. Hero counterfactual prefix mass
    is reported separately and is NOT used as a posterior. Values are conditional
    complete-state continuation-oracle expectations, not solved infoset/169EV.
    Pure deterministic policy callbacks and sequential use are required.
    """
    import math
    import hashlib
    from gto.native.poker_oracle import exact_policy_value
    if (type(max_actions) is not int or not 1<=max_actions<=10000
            or not isinstance(actions,(list,tuple)) or not 1<=len(actions)<=max_actions
            or any(type(a) is not int for a in actions) or len(set(actions))!=len(actions)
            or not isinstance(history,(list,tuple)) or len(history)>1000
            or any(type(a) is not int for a in history)
            or type(max_nodes) is not int or not 1<=max_nodes<=1000000):
        raise ValueError('bounded unique integer actions, history and node budget required')
    conditioned=condition_public_cards(hero_cards,deals,public_cards,max_deals=max_deals)
    checked=infoset_consistent_policy(policy,max_infosets=max_infosets)
    root=native.NativeState(game)
    if root.audit().get('n')!=2:raise ValueError('heads-up action comparison required')
    if not conditioned['deals']:
        return {**conditioned,'posterior':None,'action_values':None,
                'observation_evidence_mass':Fraction(0),'hero_counterfactual_mass':Fraction(0),
                'history_validated':False,'native_infoset_ev':None,'hand169_ev':None}
    targets=[];total=Fraction(0);cf=Fraction(0);common=None
    for cards,prior in conditioned['deals']:
        state=root.clone()
        for c in list(hero_cards)+cards:state.apply_action(c)
        traced=trace_history(state,history,checked);target=traced['state']
        if (target.is_terminal() or target.is_chance_node() or target.current_player()!=0
                or target.audit()['board']!=list(public_cards)):
            raise ValueError('common observed hero decision required')
        identity=(target.information_state_string(0),tuple(target.legal_actions()))
        if common is None:common=identity
        if identity!=common:raise ValueError('support does not share hero information set/actions')
        if any(a not in identity[1] for a in actions):raise ValueError('illegal hero intervention')
        mass=prior*traced['joint_reach'];total+=mass
        cf+=prior*traced['chance_reach']*math.prod(traced['strategy_reach'][1:])
        targets.append((target,mass))
    posterior=[mass/total for _,mass in targets] if total else None
    values={};used=0;counts={}
    for action in actions:
        aggregate=[Fraction(0),Fraction(0)] if total else None;start=used
        for index,(target,mass) in enumerate(targets):
            if not mass:continue
            if used>=max_nodes:raise ValueError('aggregate action EV node budget exceeded')
            child=target.clone();child.apply_action(action)
            result=exact_policy_value(child,checked,max_nodes=max_nodes-used)
            used+=result['nodes']
            aggregate=[a+posterior[index]*b for a,b in zip(aggregate,result['values'])]
        values[action]=aggregate;counts[action]=used-start
    original_mass=conditioned['compatible_prior_mass']
    return {**conditioned,'posterior':posterior,'action_values':values,'action_nodes':counts,
            'nodes':used,'observation_evidence_mass':original_mass*total,
            'hero_counterfactual_mass':original_mass*cf,'history_validated':True,
            'hero_information_sha256':hashlib.sha256(common[0].encode()).hexdigest(),
            'legal_actions':list(common[1]),'native_infoset_ev':None,'hand169_ev':None,
            'scope':'explicit observed belief, common hero decision interventions; not equilibrium',
            'policy_consistency':'queried hero infosets only','strategy_convergence':'UNKNOWN'}
