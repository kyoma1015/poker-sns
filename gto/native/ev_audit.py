"""Independent HU no-ante/no-rake chip ledger and seven-card rank oracle.

Never calls native returns, settlement or rank functions to derive expected net.
The native audit is an observation of terminal cards/folds/remaining chips only.
No audit/private cards are inputs to a policy decision.
"""
from collections import Counter
from itertools import combinations


def rank_five(cards):
    ranks=[c//4+2 for c in cards];counts=Counter(ranks)
    groups=sorted(((n,r) for r,n in counts.items()),reverse=True)
    unique=sorted(counts,reverse=True)
    straight=(unique[0] if len(unique)==5 and unique[0]-unique[-1]==4 else
              5 if unique==[14,5,4,3,2] else 0)
    flush=len({c%4 for c in cards})==1
    if straight and flush:return (8,straight)
    if groups[0][0]==4:return (7,groups[0][1],groups[1][1])
    if [g[0] for g in groups]==[3,2]:return (6,groups[0][1],groups[1][1])
    if flush:return (5,*sorted(ranks,reverse=True))
    if straight:return (4,straight)
    if groups[0][0]==3:return (3,groups[0][1],*sorted((r for n,r in groups[1:]),reverse=True))
    if [g[0] for g in groups[:2]]==[2,2]:return (2,*sorted((groups[0][1],groups[1][1]),reverse=True),groups[2][1])
    if groups[0][0]==2:return (1,groups[0][1],*sorted((r for n,r in groups[1:]),reverse=True))
    return (0,*sorted(ranks,reverse=True))


def replay_debits(history,initial,bb):
    """Independent forced-blind and per-street target/call debits from history."""
    remaining=list(initial);street=[min(initial[0],bb//2),min(initial[1],bb)]
    remaining=[v-paid for v,paid in zip(remaining,street)];folded=[False,False];current=0
    for entry in history:
        if len(entry)!=5:raise ValueError('native public history shape differs')
        round_,seat,action,_,_=entry
        if seat not in (0,1) or not current<=round_<=3 or folded[seat]:raise ValueError('invalid debit history')
        if round_!=current:street=[0,0];current=round_
        if action==0:folded[seat]=True;continue
        debit=min(max(street)-street[seat],remaining[seat]) if action==1 else (1 if action==-3 else action)-street[seat]
        if not 0<=debit<=remaining[seat]:raise ValueError('invalid replayed debit')
        remaining[seat]-=debit;street[seat]+=debit
    return remaining,folded


def independent_net(audit,config):
    rules=config['rules'];initial=config['stacks']
    if (len(initial)!=2 or rules['bba'] or str(rules['rake_rate']) not in ('0','0/1')):
        raise ValueError('independent ledger limited to HU no ante/rake')
    if 'history' in audit:
        remaining_check,folded_check=replay_debits(audit['history'],initial,rules['bb'])
        if remaining_check!=list(audit['remaining']) or folded_check!=list(audit['folded']):
            raise ValueError('independent forced-blind/action debit replay differs')
    remaining=audit['remaining'];spent=[s-r for s,r in zip(initial,remaining)]
    if any(type(v) is not int or v<0 for v in remaining+spent):raise ValueError('invalid chip ledger')
    if list(audit['initial'])!=initial or any(audit['dead']):raise ValueError('unexpected initial/dead chips')
    if list(audit['live'])!=spent:raise ValueError('spent/live ledger differs')
    live=[p for p in range(2) if not audit['folded'][p]]
    if len(live)==1:
        payouts=[sum(spent) if p==live[0] else 0 for p in range(2)]
    elif len(live)==2 and len(audit['board'])==5:
        cards=audit['holes'][0]+audit['holes'][1]+audit['board']
        if len(cards)!=9 or len(set(cards))!=9 or any(type(c) is not int or not 0<=c<52 for c in cards):
            raise ValueError('invalid showdown cards')
        ranks=[max(rank_five(c) for c in combinations(h+audit['board'],5)) for h in audit['holes']]
        winners=[p for p in range(2) if ranks[p]==max(ranks)]
        matched=min(spent);payouts=[spent[p]-matched for p in range(2)]
        for p in winners:payouts[p]+=2*matched//len(winners)
    else:raise ValueError('terminal fold or full showdown required')
    net=[p-s for p,s in zip(payouts,spent)]
    if sum(net):raise ValueError('independent conservation failure')
    return net


def completion_sensitivity(native,game,snapshot,*,samples=12000,seed=100017):
    """Paired total-profile sensitivity; changing opponent is NOT a deviation.

    The same fixed worlds are reused, never counted as extra independent data.
    All four profiles share the frozen learned rows. Only missing rows differ.
    """
    import json,random
    from gto.native.feasible_response import CompletedPolicy,terminal_trajectory,moments_interval
    from gto.native.infoset_export import _digest
    config=json.loads(game._public_config_json)
    if config['stacks']!=[100,100] or config['rules']['bb']!=2 or config['rules']['bba'] or config['rules']['rake_rate']!='0':
        raise ValueError('sensitivity experiment requires explicit HU50BB no ante/rake')
    if type(samples) is not int or not 2<=samples<=100000:raise ValueError('fixed sample budget required')
    uniform=CompletedPolicy(snapshot,'uniform_legal_prior');passive=CompletedPolicy(snapshot,'check_call_prior')
    names=('uniform','sb_check_call','bb_check_call','both_check_call')
    moments={name:[[0,0,0],[0,0,0]] for name in names};usage={name:None for name in names}
    rng=random.Random(seed);config=json.loads(game._public_config_json);bb=config['rules']['bb']
    for _ in range(samples):
        cards=list(range(52));rng.shuffle(cards);action_seed=rng.getrandbits(128);baseline=None
        for name,base,response,hero in ((names[0],uniform,None,0),(names[1],uniform,passive,0),
                (names[2],uniform,passive,1),(names[3],passive,None,0)):
            values,counts=terminal_trajectory(native,game,cards,action_seed,base,response,hero,independent_audit=True)
            if baseline is None:baseline=values[0]
            if usage[name] is None:usage[name]={k:0 for k in counts}
            for k,v in counts.items():usage[name][k]+=v
            for row,v in zip(moments[name],(values[0],values[0]-baseline)):
                row[0]+=v;row[1]+=v*v;row[2]+=1
    reports={}
    for name,rows in moments.items():
        report={}
        for key,row,bounds in zip(('sb_ev','sb_difference_from_uniform'),rows,((-100,100),(-200,200))):
            data=moments_interval(*row,*bounds,.01/(4*2))
            data['mean_bb']=data.pop('mean')/bb;data['interval_bb']=[v/bb for v in data.pop('interval')]
            data.update(sum_chips=row[0],sum_squared_chips=row[1]);report[key]=data
        reports[name]={**report,'completion_usage':usage[name]}
    result={'schema':'pokerid-completion-sensitivity-v1','samples_per_profile':samples,'seed':seed,
        'policy_digest':snapshot.digest,'config_digest':_digest(config),'profiles':reports,
        'independent_terminal_audits':samples*4,'confidence':.99,
        'scope':'explicit total-profile sensitivity, not original partial-policy EV or equilibrium accuracy',
        'deviation_comparison_only':['sb_check_call'],
        'opponent_also_changed':['bb_check_call','both_check_call']}
    print('COMPLETION_SENSITIVITY '+json.dumps(result,sort_keys=True),flush=True)
    return result
