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
