"""Bounded Monte Carlo chip EV for a fixed explicit native policy.

Intervals bound sampling error conditional on the supplied complete state and
policy. They do not bound opponent-belief error or distance from equilibrium.
Missing learned policy rows propagate errors; no fallback strategy is invented.
"""
from fractions import Fraction
import math
import random
from gto.native.history_reach import _chance, _strategy


def policy_value(state, policy, *, samples, seed, confidence=0.95, max_steps=1000):
    if (type(samples) is not int or not 1 <= samples <= 100000
            or type(seed) is not int or not callable(policy)
            or type(max_steps) is not int or not 1 <= max_steps <= 10000
            or type(confidence) not in (int,float) or not math.isfinite(confidence)
            or not 0 < confidence < 1):
        raise ValueError('bounded samples/steps, integer seed and confidence in (0,1) required')
    start = state.clone()
    audit = start.audit()
    initial = audit['initial']
    players = audit['n']
    if len(initial) != players or not 2 <= players <= 9 or any(type(s) is not int or s <= 0 for s in initial):
        raise ValueError('native initial stack bounds required')
    total = sum(initial)
    sums = [0]*players
    rake_sum = 0
    rng = random.Random(seed)
    for _ in range(samples):
        node = start.clone()
        steps = 0
        while not node.is_terminal():
            if steps >= max_steps:
                raise ValueError('rollout step budget exceeded; no partial EV returned')
            if node.is_chance_node():
                outcomes = list(_chance(node))
                action = outcomes[rng.randrange(len(outcomes))]
            else:
                probabilities = _strategy(node, policy)
                denominator = math.lcm(*(p.denominator for p in probabilities.values()))
                ticket = rng.randrange(denominator)
                for action, mass in probabilities.items():
                    ticket -= mass.numerator*(denominator//mass.denominator)
                    if ticket < 0:
                        break
                else:
                    raise ValueError('invalid normalized policy')
            node.apply_action(action)
            steps += 1
        settlement = node.settlement()
        values = settlement['net']
        rake = settlement['rake']
        if (len(values) != players or any(type(v) is not int or not -initial[p] <= v <= total-initial[p]
                for p,v in enumerate(values)) or sum(values) != -rake):
            raise ValueError('terminal chip conservation or utility bound failed')
        sums = [a+b for a,b in zip(sums,values)]
        rake_sum += rake
    # Union bound makes the advertised confidence simultaneous across all seats.
    radius = total*math.sqrt(math.log(2*players/(1-confidence))/(2*samples))
    means = [Fraction(value,samples) for value in sums]
    return {'values':means, 'samples':samples, 'seed':seed, 'confidence':confidence,
            'simultaneous_chip_intervals':[[max(-initial[p],float(mean)-radius),
                min(total-initial[p],float(mean)+radius)] for p,mean in enumerate(means)],
            'mean_rake':Fraction(rake_sum,samples), 'method':'iid native policy rollouts; Hoeffding + seat union bound',
            'scope':'fixed complete state and explicit policy; not infoset/equilibrium EV',
            'native_infoset_ev':None, 'hand169_ev':None, 'strategy_convergence':'UNKNOWN'}


def belief_value(native, game, hero_cards, deals, public_cards, history, policy, *,
                 samples_per_deal, seed, confidence=0.95, max_deals=128,
                 max_total_samples=100000, max_steps=1000, intervention=None):
    """Preflop-capable EV under an explicit heads-up opponent-hand belief.

    Reuses exact public-observation/blocker conditioning and per-player reach.
    Continuations are sampled without truncating betting or skipping postflop.
    Means remain rational sample statistics, never exact expectation claims.
    Simultaneous intervals also account for the union over sampled support rows.
    """
    from gto.native.belief_observation import condition_public_cards, infoset_consistent_policy
    from gto.native.history_reach import trace_history
    if (type(samples_per_deal) is not int or not 1<=samples_per_deal<=100000
            or type(seed) is not int or type(max_total_samples) is not int
            or not 1<=max_total_samples<=1000000
            or type(confidence) not in (int,float) or not math.isfinite(confidence)
            or not 0<confidence<1
            or type(max_steps) is not int or not 1<=max_steps<=10000
            or intervention is not None and type(intervention) is not int
            or not isinstance(history,(list,tuple)) or len(history)>1000
            or any(type(a) is not int for a in history)):
        raise ValueError('bounded sample budget and public history required')
    conditioned=condition_public_cards(hero_cards,deals,public_cards,max_deals=max_deals)
    root=native.NativeState(game)
    if root.audit()['n']!=2 or game.fixture is not None or game.root_actions:
        raise ValueError('full-deck heads-up native game required')
    checked=infoset_consistent_policy(policy)
    targets=[];evidence=Fraction(0);common=None
    for cards,prior in conditioned['deals']:
        state=root.clone()
        for card in list(hero_cards)+cards:state.apply_action(card)
        trace=trace_history(state,history,checked)
        target=trace['state']
        if target.audit()['board']!=list(public_cards):
            raise ValueError('public observation differs from native history')
        if intervention is not None:
            if target.is_terminal() or target.is_chance_node() or target.current_player()!=0:
                raise ValueError('hero decision required for action intervention')
            identity=(target.information_state_string(0),tuple(target.legal_actions()))
            if common is None:common=identity
            if common!=identity or intervention not in identity[1]:
                raise ValueError('common hero infoset and legal intervention required')
            target.apply_action(intervention)
        mass=prior*trace['joint_reach']
        targets.append((target,mass));evidence+=mass
    positive=sum(bool(mass) for _,mass in targets)
    if positive*samples_per_deal>max_total_samples:
        raise ValueError('aggregate rollout sample budget exceeded')
    means=[Fraction(0),Fraction(0)] if evidence else None
    intervals=[[Fraction(0),Fraction(0)],[Fraction(0),Fraction(0)]] if evidence else None
    sampled_rake=Fraction(0) if evidence else None
    posterior=[mass/evidence for _,mass in targets] if evidence else None
    # One shared wrapper rejects inconsistent queried hero infosets across deals.
    per_confidence=1-(1-confidence)/positive if positive else confidence
    if positive and not per_confidence<1:
        raise ValueError('confidence cannot be represented for support budget')
    seed_stream=random.Random(seed)
    for index,(target,mass) in enumerate(targets):
        if not mass:continue
        result=policy_value(target,checked,samples=samples_per_deal,
            seed=seed_stream.getrandbits(128),confidence=per_confidence,max_steps=max_steps)
        weight=posterior[index]
        means=[a+weight*b for a,b in zip(means,result['values'])]
        sampled_rake+=weight*result['mean_rake']
        for p in range(2):
            for bound in range(2):
                intervals[p][bound]+=weight*Fraction(result['simultaneous_chip_intervals'][p][bound])
    if intervals is not None:
        intervals=[[math.nextafter(float(lo),-math.inf),math.nextafter(float(hi),math.inf)]
                   for lo,hi in intervals]
    return {**conditioned,'sample_mean_values':means,'posterior':posterior,
            'observation_evidence_mass':conditioned['compatible_prior_mass']*evidence,
            'simultaneous_chip_intervals':intervals,'confidence':confidence,
            'samples':positive*samples_per_deal,'mean_rake':sampled_rake,
            'history_validated':bool(targets),
            'intervention':intervention,
            'scope':'sampled explicit observed heads-up belief; not equilibrium EV',
            'native_infoset_ev':None,'hand169_ev':None,'strategy_convergence':'UNKNOWN'}


def action_values(native,game,hero_cards,deals,public_cards,history,actions,policy,*,
                  samples_per_deal,seed,confidence=0.95,max_total_samples=100000,max_deals=128):
    """Common-prefix action EVs; target policy probability is not multiplied in.

    Explicit support and sampling uncertainty stay visible. Confidence is shared
    across actions as well as support and seats; no best-action/GTO label follows.
    """
    from gto.native.belief_observation import infoset_consistent_policy
    if (not isinstance(actions,(list,tuple)) or not 1<=len(actions)<=64
            or any(type(a) is not int for a in actions) or len(set(actions))!=len(actions)
            or type(samples_per_deal) is not int or samples_per_deal<1
            or type(max_total_samples) is not int or not 1<=max_total_samples<=1000000
            or type(confidence) not in (int,float) or not math.isfinite(confidence)
            or not 0<confidence<1):
        raise ValueError('bounded unique actions and aggregate sampling budget required')
    checked=infoset_consistent_policy(policy)
    results={};used=0
    per_confidence=1-(1-confidence)/len(actions)
    for action in actions:
        if used>=max_total_samples:raise ValueError('aggregate action sample budget exceeded')
        result=belief_value(native,game,hero_cards,deals,public_cards,history,checked,
            samples_per_deal=samples_per_deal,seed=seed,confidence=per_confidence,
            max_total_samples=max_total_samples-used,intervention=action,max_deals=max_deals)
        used+=result['samples'];results[action]=result
    return {'actions':results,'samples':used,'confidence':confidence,
            'scope':'sampled common-hero action values under explicit support; not equilibrium',
            'native_infoset_ev':None,'hand169_ev':None,'strategy_convergence':'UNKNOWN'}


def preflop_action_report(native,game,hero_cards,deals,history,actions,policy,*,
                          samples_per_deal,seed,confidence=0.95,max_total_samples=100000,max_deals=128):
    """Bind a sampled preflop comparison to immutable policy/config/input data.

    This uses a separate schema from exact expectation/169 exports. Hashes bind
    supplied data; they do not attest that it is complete or strategically solved.
    """
    import json
    from gto.native.infoset_export import PolicySnapshot, _digest
    from gto.native.preflop import decision, describe
    if type(policy) is not PolicySnapshot:
        raise ValueError('immutable PolicySnapshot required for report transport')
    configuration=json.loads(game._public_config_json)
    manifest=configuration['rules']
    expected_rules={key:value for key,value in manifest.items() if key!='version'}
    rate=Fraction(manifest['rake_rate'])
    expected_rules.update(rate_num=rate.numerator,rate_den=rate.denominator)
    if game.stacks!=configuration['stacks'] or game._native_rules!=expected_rules:
        raise ValueError('native configuration differs from advertised manifest')
    # Validate prior/card support before selecting the replay representative.
    from gto.native.belief_observation import condition_public_cards
    support=condition_public_cards(hero_cards,deals,[],max_deals=max_deals)
    representative=support['deals'][0][0]
    target=decision(native,game,history,cards=list(hero_cards)+representative)
    description=describe(target)
    result=action_values(native,game,hero_cards,deals,[],history,actions,policy,
        samples_per_deal=samples_per_deal,seed=seed,confidence=confidence,
        max_total_samples=max_total_samples,max_deals=max_deals)
    identity={'config':configuration,'hero_cards':list(hero_cards),'history':list(history),
        'actions':list(actions),'policy_digest':policy.digest,
        'support':[[list(cards),str(prior)] for cards,prior in deals],
        'samples_per_deal':samples_per_deal,'seed':seed,'confidence':confidence}
    return {'schema':'pokerid-sampled-preflop-action-v1',**result,
            'decision':description,'config_digest':_digest(configuration),
            'policy_digest':policy.digest,'input_digest':_digest(identity),
            'estimate_kind':'sample_mean_with_sampling_intervals',
            'support_complete':False,'equilibrium_verified':False}
