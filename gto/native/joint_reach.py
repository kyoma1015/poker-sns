"""Actual native multiway history likelihood and bounded conditional policy EV.

All priors and policies are supplied explicitly. Exact reach is exact for that
support/policy, not proof of full-game learned support or poker equilibrium.
"""
from fractions import Fraction
import math
import random
from gto.native.history_reach import _strategy, trace_history
from gto.native.joint_support import condition_joint_support
from gto.native.policy_rollout import policy_value


def consistent_policy(policy,*,max_infosets=100000):
    """Check every queried actor's own information key across hidden deals."""
    if not callable(policy) or type(max_infosets) is not int or not 1<=max_infosets<=1000000:
        raise ValueError('explicit policy and bounded infoset budget required')
    seen={}
    def checked(node):
        row=_strategy(node,policy);actor=node.current_player()
        key=(actor,node.information_state_string(actor));legal=tuple(node.legal_actions())
        signature=(legal,tuple(row.get(a,Fraction(0)) for a in legal))
        if key in seen:
            if seen[key]!=signature:raise ValueError('policy differs at identical queried actor infoset')
        else:
            if len(seen)>=max_infosets:raise ValueError('joint infoset consistency budget exceeded')
            seen[key]=signature
        return row
    return checked


def _prepare(native,game,hero_cards,deals,public_cards,history,policy,*,hero_seat=0,
             max_deals=128,max_steps=1000,max_infosets=100000):
    if (type(max_steps) is not int or not 1<=max_steps<=10000
            or not isinstance(history,(list,tuple)) or len(history)>max_steps
            or any(type(a) is not int for a in history)
            or game.fixture is not None or game.root_actions):
        raise ValueError('bounded public history and full-deck native game required')
    root=native.NativeState(game);players=root.audit()['n']
    conditioned=condition_joint_support(players,hero_cards,deals,public_cards,
        hero_seat=hero_seat,max_deals=max_deals)
    checked=consistent_policy(policy,max_infosets=max_infosets)
    targets=[];records=[];evidence=Fraction(0);counterfactual=Fraction(0)
    for full,prior in conditioned['deals']:
        state=root.clone()
        for hand in full:
            for card in hand:state.apply_action(card)
        trace=trace_history(state,history,checked,max_steps=max_steps)
        target=trace['state']
        if target.audit()['board']!=list(public_cards):
            raise ValueError('public observation differs from replayed native board')
        mass=prior*trace['joint_reach'];evidence+=mass
        cf=prior*trace['chance_reach']*math.prod(p for i,p in enumerate(trace['strategy_reach']) if i!=hero_seat)
        counterfactual+=cf;targets.append((target,mass))
        records.append({'hands':[list(h) for h in full],'conditioned_prior':prior,
            'chance_reach':trace['chance_reach'],'strategy_reach':trace['strategy_reach'],
            'joint_reach':trace['joint_reach'],'mass':mass,'hero_excluded_mass':cf,
            'uniform_private_deal_probability':Fraction(1,math.perm(52,2*players)),
            'uniform_private_history_probability':Fraction(1,math.perm(52,2*players))*trace['joint_reach']})
    compatible=conditioned['compatible_prior_mass']
    report={**conditioned,'reach_records':records,
        'posterior':[mass/evidence for _,mass in targets] if evidence else None,
        'history_evidence_given_compatible_support':evidence,
        'observation_evidence_mass':compatible*evidence,
        'hero_excluded_evidence_mass':compatible*counterfactual,
        'history_validated':bool(targets),
        'reach_scope':'exact likelihood under supplied joint prior and queried-consistent policy',
        'policy_consistency':'all queried actors; unqueried infosets unproved',
        'native_infoset_ev':None,'hand169_ev':None,'strategy_convergence':'UNKNOWN'}
    return report,targets,checked


def joint_reach(native,game,hero_cards,deals,public_cards,history,policy,**budgets):
    return _prepare(native,game,hero_cards,deals,public_cards,history,policy,**budgets)[0]


def _sample(report,targets,checked,*,samples_per_deal,seed,confidence,max_total_samples,
            max_steps,action=None):
    if (type(samples_per_deal) is not int or not 1<=samples_per_deal<=100000
            or type(seed) is not int or type(max_total_samples) is not int
            or not 1<=max_total_samples<=1000000
            or type(confidence) not in (int,float) or not math.isfinite(confidence)
            or not 0<confidence<1):
        raise ValueError('bounded sampling controls and confidence in (0,1) required')
    positive=sum(bool(mass) for _,mass in targets)
    if positive*samples_per_deal>max_total_samples:raise ValueError('joint sample budget exceeded')
    per_confidence=1-(1-confidence)/positive if positive else confidence
    if not per_confidence<1:raise ValueError('confidence cannot be represented for support size')
    players=report['players'];posterior=report['posterior'];rng=random.Random(seed)
    means=[Fraction(0)]*players if posterior is not None else None
    intervals=[[Fraction(0),Fraction(0)] for _ in range(players)] if posterior is not None else None
    rake=Fraction(0) if posterior is not None else None
    for index,(state,mass) in enumerate(targets):
        if not mass:continue
        target=state.clone()
        if action is not None:target.apply_action(action)
        result=policy_value(target,checked,samples=samples_per_deal,
            seed=rng.getrandbits(128),confidence=per_confidence,max_steps=max_steps)
        weight=posterior[index];rake+=weight*result['mean_rake']
        means=[a+weight*b for a,b in zip(means,result['values'])]
        for p in range(players):
            for bound in range(2):intervals[p][bound]+=weight*Fraction(result['simultaneous_chip_intervals'][p][bound])
    if intervals is not None:
        intervals=[[math.nextafter(float(lo),-math.inf),math.nextafter(float(hi),math.inf)] for lo,hi in intervals]
        if sum(means)!=-rake:raise ValueError('joint sample chip/rake conservation failed')
    return {**report,'sample_mean_values':means,'simultaneous_chip_intervals':intervals,
        'mean_rake':rake,'samples':positive*samples_per_deal,'seed':seed,'confidence':confidence,
        'intervention':action,'estimate_kind':'conditional sample means; sampling intervals only',
        'scope':'explicit joint belief and native continuation; not equilibrium EV'}


def joint_value(native,game,hero_cards,deals,public_cards,history,policy,*,samples_per_deal,seed,
                confidence=0.95,max_total_samples=100000,hero_seat=0,max_deals=128,
                max_steps=1000,max_infosets=100000):
    report,targets,checked=_prepare(native,game,hero_cards,deals,public_cards,history,policy,
        hero_seat=hero_seat,max_deals=max_deals,max_steps=max_steps,max_infosets=max_infosets)
    return _sample(report,targets,checked,samples_per_deal=samples_per_deal,seed=seed,
        confidence=confidence,max_total_samples=max_total_samples,max_steps=max_steps)


def joint_actions(native,game,hero_cards,deals,public_cards,history,actions,policy,*,
                  samples_per_deal,seed,confidence=0.95,max_total_samples=100000,
                  hero_seat=0,max_deals=128,max_steps=1000,max_infosets=100000):
    if (not isinstance(actions,(list,tuple)) or not 1<=len(actions)<=64
            or any(type(a) is not int for a in actions) or len(set(actions))!=len(actions)
            or type(max_total_samples) is not int or not 1<=max_total_samples<=1000000
            or type(confidence) not in (int,float) or not math.isfinite(confidence) or not 0<confidence<1):
        raise ValueError('bounded unique action interventions and sampling budget required')
    report,targets,checked=_prepare(native,game,hero_cards,deals,public_cards,history,policy,
        hero_seat=hero_seat,max_deals=max_deals,max_steps=max_steps,max_infosets=max_infosets)
    common=None
    for state,_ in targets:
        if state.is_terminal() or state.is_chance_node() or state.current_player()!=hero_seat:
            raise ValueError('common hero decision required')
        identity=(state.information_state_string(hero_seat),tuple(state.legal_actions()))
        if common is None:common=identity
        if identity!=common or any(a not in identity[1] for a in actions):
            raise ValueError('common hero information key and legal actions required')
    results={};used=0;per_confidence=1-(1-confidence)/len(actions)
    for action in actions:
        if used>=max_total_samples:raise ValueError('aggregate joint action sample budget exceeded')
        result=_sample(report,targets,checked,samples_per_deal=samples_per_deal,seed=seed,
            confidence=per_confidence,max_total_samples=max_total_samples-used,max_steps=max_steps,action=action)
        used+=result['samples'];results[action]=result
    return {'schema':'pokerid-joint-policy-actions-v1','reach':report,'actions':results,
        'confidence':confidence,'samples':used,'support_complete':report['support_complete'],
        'equilibrium_verified':False,'native_infoset_ev':None,'hand169_ev':None,'strategy_convergence':'UNKNOWN'}
