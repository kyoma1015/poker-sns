"""Exact finite-subtree evaluation of an explicit policy on actual NativeState.

This evaluates a supplied policy, not best response or equilibrium. Perfect-card
fixture values cannot establish a hidden-information full-poker Nash equilibrium.
"""
from fractions import Fraction
import math


def exact_policy_value(state, policy, *, max_nodes=10000):
    if type(max_nodes) is not int or not 1<=max_nodes<=1000000 or not callable(policy):
        raise ValueError('finite node budget and explicit policy required')
    count=0; terminal_count=0
    def walk(node):
        nonlocal count,terminal_count
        count+=1
        if count>max_nodes:raise ValueError('oracle node budget exceeded')
        if node.is_terminal():
            terminal_count+=1; result=node.returns()
            if not isinstance(result,(list,tuple)) or not 2<=len(result)<=9:
                raise ValueError('invalid terminal returns')
            if any(not math.isfinite(x) or x!=int(x) for x in result):
                raise ValueError('integer chip terminal return required')
            return [Fraction(int(x)) for x in result]
        if node.is_chance_node():
            outcomes=node.chance_outcomes()
            if not outcomes:raise ValueError('empty chance distribution')
            # NativeState::chances is exactly uniform over the remaining deck.
            if len({a for a,_ in outcomes})!=len(outcomes) or any(not math.isfinite(p) or abs(p-1/len(outcomes))>1e-12 for _,p in outcomes):
                raise ValueError('oracle only supports native uniform-card chance')
            probabilities={a:Fraction(1,len(outcomes)) for a,_ in outcomes}
        else:
            probabilities=policy(node)
            if not isinstance(probabilities,dict) or not probabilities:
                raise ValueError('explicit action policy required')
            legal=set(node.legal_actions())
            if any(type(a) is not int or a not in legal for a in probabilities):
                raise ValueError('illegal policy action')
            if any(not isinstance(p,Fraction) or p<0 for p in probabilities.values()) or sum(probabilities.values())!=1:
                raise ValueError('exact normalized Fraction policy required')
        result=None
        for action,mass in probabilities.items():
            if not mass:continue
            child=node.clone(); child.apply_action(action); value=walk(child)
            if result is None:result=[Fraction() for _ in value]
            if len(result)!=len(value):raise ValueError('player count changed')
            result=[a+mass*b for a,b in zip(result,value)]
        return result
    result=walk(state.clone())
    return {'values':result,'nodes':count,'terminal_nodes':terminal_count,
            'scope':'explicit-policy finite native poker subtree; not equilibrium/exploitability'}
