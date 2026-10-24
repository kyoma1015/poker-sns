"""Finite full-state history reach and conditional explicit-policy chip EV.

Chance reach and each player's strategy reach are separate exact Fractions.
A supplied starting state has conditional reach one. A replay including the full
private deal measures that complete deal, NOT the hero marginal1/2652. This is
not an information-set/counterfactual reach estimator or a native EV-table fill.
"""
from fractions import Fraction
import math
from gto.native.poker_oracle import exact_policy_value


def _strategy(node, policy):
    before=node.audit()
    probabilities=policy(node)
    if node.audit()!=before:
        raise ValueError('policy mutated the supplied native state')
    legal=set(node.legal_actions())
    if (not isinstance(probabilities,dict) or not probabilities
            or any(type(a) is not int or a not in legal for a in probabilities)
            or any(not isinstance(p,Fraction) or p<0 for p in probabilities.values())
            or sum(probabilities.values())!=1):
        raise ValueError('exact normalized Fraction policy on legal actions required')
    return dict(probabilities)


def _chance(node):
    outcomes=node.chance_outcomes()
    if (not outcomes or len({a for a,_ in outcomes})!=len(outcomes)
            or any(type(a) is not int or not isinstance(p,(int,float))
                   or isinstance(p,bool) or not math.isfinite(p)
                   or abs(p-1/len(outcomes))>1e-12 for a,p in outcomes)):
        raise ValueError('native uniform-card chance contract required')
    # Exact uniformity is the reconstructed NativeState::chances source contract;
    # binary64 chance values are checked, not treated as arbitrary exact inputs.
    return {action:Fraction(1,len(outcomes)) for action,_ in outcomes}


def trace_history(state, actions, policy, *, max_steps=1000):
    if (type(max_steps) is not int or not 1<=max_steps<=10000
            or not isinstance(actions,(list,tuple)) or len(actions)>max_steps
            or any(type(a) is not int for a in actions) or not callable(policy)):
        raise ValueError('bounded explicit integer action history and policy required')
    node=state.clone();players=node.audit().get('n')
    if type(players) is not int or not 2<=players<=9:
        raise ValueError('native player count must be2..9')
    chance=Fraction(1);strategy=[Fraction(1) for _ in range(players)];steps=[]
    for action in actions:
        if node.is_terminal():raise ValueError('history continues after terminal')
        if node.is_chance_node():
            probabilities=_chance(node)
            if action not in probabilities:raise ValueError('illegal chance action')
            mass=probabilities[action];chance*=mass
            steps.append({'kind':'chance','actor':None,'action':action,'probability':mass})
        else:
            actor=node.current_player()
            if type(actor) is not int or not 0<=actor<players:
                raise ValueError('native actor outside player range')
            probabilities=_strategy(node,policy)
            if action not in node.legal_actions():raise ValueError('illegal strategy action')
            mass=probabilities.get(action,Fraction(0));strategy[actor]*=mass
            steps.append({'kind':'strategy','actor':actor,'action':action,'probability':mass})
        node.apply_action(action)
    joint=chance*math.prod(strategy)
    return {'state':node,'chance_reach':chance,'strategy_reach':strategy,
            'joint_reach':joint,'steps':steps,
            'scope':'full-state path conditional on supplied starting state; not infoset reach'}


def evaluate_history(state, actions, policy, *, max_steps=1000, max_nodes=10000):
    trace=trace_history(state,actions,policy,max_steps=max_steps)
    if type(max_nodes) is not int or not 1<=max_nodes<=1000000:
        raise ValueError('finite EV node budget required')
    target=trace.pop('state')
    if not trace['joint_reach']:
        values=None;contribution=None;nodes=0;terminals=0
    else:
        result=exact_policy_value(target,lambda node:_strategy(node,policy),max_nodes=max_nodes)
        values=result['values'];contribution=[v*trace['joint_reach'] for v in values]
        nodes=result['nodes'];terminals=result['terminal_nodes']
    return {'reach':trace,'conditional_ev':values,'branch_ev_contribution':contribution,
            'nodes':nodes,'terminal_nodes':terminals,'native_infoset_ev':None,
            'ev_scope':'explicit-policy complete-state subtree; unknown infoset EV stays null',
            'strategy_convergence':'UNKNOWN','historical_compatibility':'UNKNOWN'}


def native_average_policy(native, solver):
    """Snapshot adapter for existing learned rows only; no uniform/missing fill.

    Fractions normalize the serialized binary64 values exactly. They do not
    restore unrounded native long-double accumulators. Caller must not train or
    load concurrently; changed iteration/RNG is refused, not synchronized.
    """
    if not isinstance(solver,native.Solver) or solver.stats().get('native_engine') is not True:
        raise ValueError('actual native solver required')
    iteration=solver.iteration;rng=solver.rng_state();keys=set(solver.keys())
    def policy(node):
        if solver.iteration!=iteration or solver.rng_state()!=rng:
            raise ValueError('native policy snapshot changed')
        if node.is_terminal() or node.is_chance_node():
            raise ValueError('native policy requires a decision state')
        key=node.information_state_string(node.current_player())
        if key not in keys:raise ValueError('native policy row unobserved; EV remains unknown')
        row=solver.row(key);actions=row['actions'];average=row['average']
        if (list(actions)!=list(node.legal_actions()) or len(average)!=len(actions)
                or not average or any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in average)):
            raise ValueError('invalid native average-policy row')
        values=[Fraction(x) for x in average];total=sum(values)
        if not total:raise ValueError('unvisited native row has no estimated policy')
        return {a:p/total for a,p in zip(actions,values)}
    return policy


def immutable_average_policy(native, solver, *, max_rows=100000):
    """Copy observed rows; later training cannot alter this finite policy.

    Construction requires exclusive access by the caller. Pre/post iteration,
    RNG and key checks detect ordinary concurrent training, not synchronization.
    Missing rows never receive an invented policy.
    """
    if type(max_rows) is not int or not 1<=max_rows<=1000000:
        raise ValueError('bounded snapshot row limit required')
    native_average_policy(native,solver)
    iteration=solver.iteration;rng=solver.rng_state();keys=tuple(solver.keys());rows={}
    if len(keys)>max_rows:raise ValueError('snapshot exceeds row budget')
    for key in keys:
        row=solver.row(key);actions=tuple(row['actions']);values=tuple(row['average'])
        if (not actions or len(actions)!=len(values) or len(set(actions))!=len(actions)
                or any(type(a) is not int for a in actions)
                or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in values)):
            raise ValueError('invalid snapshot row')
        total=sum(Fraction(v) for v in values)
        if total:rows[key]=(actions,tuple(Fraction(v)/total for v in values))
    if solver.iteration!=iteration or solver.rng_state()!=rng or tuple(solver.keys())!=keys:
        raise ValueError('solver changed during snapshot')
    def policy(node):
        if node.is_terminal() or node.is_chance_node():raise ValueError('decision required')
        key=node.information_state_string(node.current_player())
        if key not in rows:raise ValueError('snapshot row unknown; EV remains null')
        actions,values=rows[key]
        if list(actions)!=list(node.legal_actions()):raise ValueError('snapshot action mismatch')
        return dict(zip(actions,values))
    return policy


def bounded_belief_value(native, game, hero_cards, deals, history, policy, *,
                         max_deals=128,max_nodes=10000,counterfactual_player=None):
    """Heads-up finite explicit conditional belief, not a native infoset EV.

    Hero is seat0. Priors are normalized conditional on the supplied support and
    hero blockers, never asserted to represent all legal opponent hands. Private
    deal chance is already conditioned in priors; it is NOT multiplied twice.
    Callback is an explicit full-state policy; no information-set consistency or
    equilibrium is inferred. Counterfactual mass excludes only one actor's path
    strategy factor, keeping prior and public chance factors.
    """
    if (type(max_deals) is not int or not 1<=max_deals<=10000
            or type(max_nodes) is not int or not 1<=max_nodes<=1000000
            or not isinstance(deals,(list,tuple)) or not 1<=len(deals)<=max_deals
            or not isinstance(hero_cards,(list,tuple)) or len(hero_cards)!=2
            or any(type(c) is not int or not 0<=c<52 for c in hero_cards)
            or len(set(hero_cards))!=2
            or counterfactual_player is not None and
               (type(counterfactual_player) is not int or counterfactual_player not in (0,1))):
        raise ValueError('bounded heads-up explicit conditional belief required')
    root=native.NativeState(game)
    if root.audit().get('n')!=2:raise ValueError('belief oracle currently heads-up only')
    checked=[];seen=set()
    for item in deals:
        if not isinstance(item,(list,tuple)) or len(item)!=2:raise ValueError('cards/prior pair required')
        cards,prior=item
        if (not isinstance(cards,(list,tuple)) or len(cards)!=2
                or any(type(c) is not int or not 0<=c<52 for c in cards)
                or len(set(cards))!=2 or set(cards)&set(hero_cards)
                or not isinstance(prior,Fraction) or prior<0):
            raise ValueError('valid disjoint cards and exact nonnegative prior required')
        identity=tuple(sorted(cards))
        if identity in seen:raise ValueError('duplicate unordered opponent hand')
        seen.add(identity);checked.append((tuple(cards),prior))
    if sum(p for _,p in checked)!=1:raise ValueError('conditional prior must sum exactly to one')
    records=[];total=Fraction(0);cf=Fraction(0);used=0
    for cards,prior in checked:
        state=root.clone()
        for action in list(hero_cards)+list(cards):state.apply_action(action)
        traced=trace_history(state,history,policy)
        reach=traced['joint_reach'];mass=prior*reach
        cf_mass=(prior*traced['chance_reach']*math.prod(
            p for actor,p in enumerate(traced['strategy_reach']) if actor!=counterfactual_player)
            if counterfactual_player is not None else None)
        if mass:
            if used>=max_nodes:raise ValueError('aggregate EV budget exceeded')
            ev=exact_policy_value(traced['state'],lambda node:_strategy(node,policy),max_nodes=max_nodes-used)
            used+=ev['nodes'];values=ev['values']
        else:values=None
        records.append({'opponent_cards':list(cards),'prior':prior,'chance_reach':traced['chance_reach'],
                        'strategy_reach':traced['strategy_reach'],'mass':mass,'values':values})
        total+=mass
        if cf_mass is not None:cf+=cf_mass
    values=([sum(r['mass']*r['values'][p] for r in records if r['values'] is not None)/total
             for p in range(2)] if total else None)
    return {'support':records,'evidence_mass':total,
            'posterior':[r['mass']/total for r in records] if total else None,
            'conditional_ev':values,'counterfactual_mass':cf if counterfactual_player is not None else None,
            'nodes':used,'native_infoset_ev':None,'hand169_ev':None,
            'scope':'heads-up explicit support conditional belief and full-state policy; not equilibrium',
            'support_complete':False,'strategy_convergence':'UNKNOWN'}
