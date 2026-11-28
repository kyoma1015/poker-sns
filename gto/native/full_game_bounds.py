"""Conservative full-continuation policy/response envelopes on fixed card worlds.

A future deck is fixed independently of actions. Revealing it to a deviator is a
perfect-information relaxation, so its value is an UPPER bound on a legal poker
best response, never a feasible deviation or exact exploitability. Unknown policy
rows and exhausted node budgets retain utility bounds, not invented strategies.
A single-world result is not an equilibrium certificate or an expectation.
Increasing the budget cannot remove this information relaxation. See
feasible_response.py for complementary held-out LOWER bounds from deployable
information-set policies against an explicitly declared fixed total profile.
"""
from fractions import Fraction as F
from gto.native.history_reach import _strategy
from gto.native.infoset_export import UnknownPolicyRow


def world_bounds(state, policy, future_deck, stacks, *, max_nodes=512):
    if (not isinstance(stacks,(list,tuple)) or not 2<=len(stacks)<=9
            or any(type(s) is not int or s<=0 for s in stacks)
            or type(max_nodes) is not int or not 1<=max_nodes<=1000000
            or not isinstance(future_deck,(list,tuple))
            or any(type(c) is not int or not 0<=c<52 for c in future_deck)
            or len(set(future_deck))!=len(future_deck) or not callable(policy)):
        raise ValueError('bounded native full-world evaluation inputs required')
    n=len(stacks);bounds=[(-F(s),F(sum(stacks)-s)) for s in stacks]
    audit=state.audit()
    if audit.get('n')!=n or set(future_deck)!=set(audit.get('deck',[])):
        raise ValueError('full remaining native deck permutation required')
    nodes=terminals=unknown=cutoffs=0
    def walk(node,offset,deviator):
        nonlocal nodes,terminals,unknown,cutoffs
        if nodes>=max_nodes:
            cutoffs+=1;return list(bounds)
        nodes+=1
        if node.is_terminal():
            terminals+=1;values=node.returns()
            if (len(values)!=n or any(type(x) not in (int,float) or x!=int(x)
                    or not bounds[i][0]<=x<=bounds[i][1] for i,x in enumerate(values))
                    or sum(values)>0):raise ValueError('terminal utility/conservation boundary differs')
            return [(F(int(x)),F(int(x))) for x in values]
        if node.is_chance_node():
            if offset>=len(future_deck):raise ValueError('future deck exhausted')
            outcomes=node.chance_outcomes();legal={a for a,_ in outcomes}
            if (future_deck[offset] not in legal or len(legal)!=len(outcomes)
                    or any(abs(p-1/len(outcomes))>1e-12 for _,p in outcomes)):
                raise ValueError('future deck/native uniform chance differs')
            child=node.clone();child.apply_action(future_deck[offset])
            return walk(child,offset+1,deviator)
        actor=node.current_player()
        if type(actor) is not int or not 0<=actor<n:raise ValueError('native actor differs')
        if actor==deviator:
            probabilities=None
        else:
            try:probabilities=_strategy(node,policy)
            except UnknownPolicyRow:probabilities=None;unknown+=1
        actions=node.legal_actions() if probabilities is None else [a for a,p in probabilities.items() if p]
        if not actions:raise ValueError('empty legal strategy')
        if probabilities is None:
            # Unknown opponent/own policies may be completed arbitrarily. Each
            # player's envelope uses extrema; no incompatible completion is
            # advertised as one feasible joint policy.
            result=None
            for a in actions:
                child=node.clone();child.apply_action(a);value=walk(child,offset,deviator)
                if result is None:result=value
                else:result=[(min(x[0],y[0]),max(x[1],y[1])) for x,y in zip(result,value)]
            return result
        result=[(F(0),F(0)) for _ in range(n)]
        for a in actions:
            child=node.clone();child.apply_action(a);value=walk(child,offset,deviator);p=probabilities[a]
            result=[(lo+p*v[0],hi+p*v[1]) for (lo,hi),v in zip(result,value)]
        return result
    # Separate budgets make the response bounds independent of traversal order
    # between the profile and different deviators.
    profile=walk(state.clone(),0,None);counts=[{'nodes':nodes,'terminals':terminals,'unknown':unknown,'cutoffs':cutoffs}]
    responses=[]
    for player in range(n):
        nodes=terminals=unknown=cutoffs=0
        result=walk(state.clone(),0,player);responses.append(result[player][1])
        counts.append({'nodes':nodes,'terminals':terminals,'unknown':unknown,'cutoffs':cutoffs})
    return {'profile_intervals_chips':profile,'clairvoyant_response_upper_chips':responses,
        'traversals':counts,'full_game_convergence_verified':False,
        'response_is_feasible':False,'positive_upper_proves_exploitability':False,
        'scope':'one fixed-card world, full continuation; expectation/confidence still required',
        'response_method':'perfect-information relaxation, including future cards; upper bound only'}
