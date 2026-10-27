"""Ordinary HU50BB learning and full-continuation readiness, never release data."""
from fractions import Fraction as F
from itertools import permutations
import hashlib
import json
from pathlib import Path
import random
from gto.hand169 import CLASSES,hand_class
from gto.native.hand169_bridge import card_name,context_of
from gto.native.infoset_export import PolicySnapshot,report_json,_digest
from gto.native.full_game_bounds import world_bounds
from gto.native.preflop import decision,describe
from gto.native.training import NativeGame,train_batch


def context_coverage(native,solver,game,history):
    state=decision(native,game,history);desc=describe(state);ctx=desc['context']
    rows={label:[] for label in CLASSES};ordered=set();actions=state.legal_actions();created=0
    for key in solver.keys():
        info=json.loads(key)
        if {k:info[k] for k in ctx}!=ctx:continue
        created+=1;row=solver.row(key)
        if type(row.get('updates')) is not int or row['updates']<=0:continue
        hand=tuple(info['hand'])
        if hand in ordered or list(row['actions'])!=actions:raise ValueError('native context row identity differs')
        ordered.add(hand);values=[F(v) for v in row['average']];total=sum(values)
        if total<=0:raise ValueError('updated native row has no policy')
        rows[hand_class([card_name(c) for c in hand])].append([v/total for v in values])
    hands={}
    for label,values in rows.items():
        expected=2*(6 if len(label)==2 else 4 if label.endswith('s') else 12)
        complete=len(values)==expected
        # Only initial RFI has proven uniform own-hand reach. Later decisions
        # need genuine history-dependent private-deal posterior, not visit weights.
        frequency=([sum(v[i] for v in values)/expected for i in range(len(actions))]
            if complete and not history else None)
        hands[label]={'updated_orderings':len(values),'expected_orderings':expected,
            'frequencies':frequency,'ev_bb':None,'ev_interval_bb':None,
            'reach_status':'exact_initial_1/2652' if not history else 'history_posterior_not_integrated'}
    return {'stage':desc['stage'],'history':list(history),'seat':desc['seat'],
        'actions':desc['legal_actions'],'created_orderings':created,'updated_orderings':len(ordered),
        'expected_orderings':2652,'complete_frequency_classes':sum(h['frequencies'] is not None for h in hands.values()),
        'hands':hands,'full_game_convergence_verified':False}


def evaluate_rfi(native,game,policy,*,samples_per_class=2,max_nodes=64,seed=101):
    """Every169class, actual ordered hands uniformly within each class.

    Deck worlds are IID under Python random's uniform PRNG model. Profile EVs
    and clairvoyant response bounds include all subsequent legal actions; finite
    cuts remain pessimistic utility intervals. This can be extremely loose.
    """
    import math
    from gto.native.initial_chance_reach import _verified_game
    _verified_game(game)
    if game.num_players()!=2 or type(policy) is not PolicySnapshot:
        raise ValueError('HU full-deck immutable policy evaluation required')
    if (type(samples_per_class) is not int or not 1<=samples_per_class<=10000
            or type(seed) is not int):raise ValueError('bounded fixed evaluation schedule required')
    pairs={label:[] for label in CLASSES}
    for pair in permutations(range(52),2):pairs[hand_class([card_name(c) for c in pair])].append(pair)
    rng=random.Random(seed);results={};failure=1e-6;n=game.num_players()
    for label in CLASSES:
        lower=[F(0)]*n;upper=[F(0)]*n;br=[F(0)]*n;unknown=cutoffs=terminals=0
        for _ in range(samples_per_class):
            hero=rng.choice(pairs[label]);remaining=[c for c in range(52) if c not in hero];rng.shuffle(remaining)
            # Explicit HU ordinary root; all opponent holes and board sampled
            # from full remaining deck, not a caller's tiny fixed belief.
            state=decision(native,game,[],cards=list(hero)+remaining[:2])
            value=world_bounds(state,policy,remaining[2:],game.stacks,max_nodes=max_nodes)
            for player,(lo,hi) in enumerate(value['profile_intervals_chips']):
                lower[player]+=lo;upper[player]+=hi;br[player]+=value['clairvoyant_response_upper_chips'][player]
            for traversal in value['traversals']:
                unknown+=traversal['unknown'];cutoffs+=traversal['cutoffs'];terminals+=traversal['terminals']
        # Union bound over169classes,2players and3one-sided expectations.
        radius=math.nextafter(sum(game.stacks)*math.sqrt(math.log(169*n*3/failure)/(2*samples_per_class)),math.inf)
        intervals=[];br_upper=[]
        for player in range(n):
            lo=-game.stacks[player];hi=sum(game.stacks)-game.stacks[player]
            intervals.append([max(lo,math.nextafter(float(lower[player]/samples_per_class)-radius,-math.inf)),
                              min(hi,math.nextafter(float(upper[player]/samples_per_class)+radius,math.inf))])
            br_upper.append(min(hi,math.nextafter(float(br[player]/samples_per_class)+radius,math.inf)))
        results[label]={'profile_ev_interval_chips':intervals,'clairvoyant_response_upper_chips':br_upper,
            'samples':samples_per_class,'unknown_policy_cuts':unknown,'budget_cuts':cutoffs,'terminal_nodes':terminals}
    global_upper=[0.0]*n
    for label,row in results.items():
        weight=(6 if len(label)==2 else 4 if label.endswith('s') else 12)/1326
        for player in range(n):global_upper[player]+=weight*(row['clairvoyant_response_upper_chips'][player]-row['profile_ev_interval_chips'][player][0])
    bb=json.loads(game._public_config_json)['rules']['bb']
    return {'schema':'pokerid-full-continuation-bound-v1','hands':results,'confidence':1-failure,
        'policy_digest':policy.digest,'config_digest':_digest(json.loads(game._public_config_json)),
        'per_player_global_gain_upper_bb':[math.nextafter(max(0,v/bb),math.inf) for v in global_upper],
        'full_game_convergence_verified':False,'global_gain_lower_bb':0,
        'note':'conservative sampled whole-game upper envelopes, not exact exploitability; unknown policies remain interval-valued',
        'sampling_assumption':'IID uniform deck/within-class ordered hand model; reproducible PRNG',
        'seed':seed,'samples_per_class':samples_per_class,'max_nodes_per_traversal':max_nodes}


def experiment(native,output):
    output=Path(output);output.mkdir(exist_ok=False);game=NativeGame([100,100]);all_runs=[]
    for seed in (17,29):
        solver=native.Solver(game,.6,seed,True,True,.1);run=[]
        for target in (2000,20000):
            training=train_batch(solver,game,target-solver.iteration,output/f'seed-{seed}-{target}.bin')
            contexts=[context_coverage(native,solver,game,h) for h in ([],[7],[7,20],[7,20,44])]
            observation={'seed':seed,'iteration':target,'contexts':contexts,'training':training,
                'source_checkpoint_sha256':hashlib.sha256((output/f'seed-{seed}-{target}.bin').read_bytes()).hexdigest()}
            if target==20000:
                policy=PolicySnapshot.from_solver(native,solver,max_rows=1000000)
                observation['full_continuation']=evaluate_rfi(native,game,policy,seed=seed+1000)
            (output/f'seed-{seed}-{target}.json').write_text(report_json(observation)+'\n');run.append(observation)
            print('ORDINARY_PROGRESS '+json.dumps({'seed':seed,'iteration':target,'contexts':[{k:c[k] for k in ('stage','updated_orderings','complete_frequency_classes')} for c in contexts]}),flush=True)
        all_runs.append(run);del solver
    summary={'schema':'pokerid-ordinary-preflop-study-v1','formal_profile':False,
        'config':json.loads(game._public_config_json),'runs':[[{'seed':o['seed'],'iteration':o['iteration'],
        'contexts':[{k:c[k] for k in ('stage','updated_orderings','created_orderings','complete_frequency_classes')} for c in o['contexts']],
        'global_gain_upper_bb':o.get('full_continuation',{}).get('per_player_global_gain_upper_bb'),
        'checkpoint_sha256':o['source_checkpoint_sha256']} for o in r] for r in all_runs],
        'verified_ordinary_ranges':0,'formal_acceptance_complete':0}
    (output/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print('ORDINARY_SUMMARY '+json.dumps(summary,sort_keys=True),flush=True)
    return summary


if __name__=='__main__':
    import argparse,importlib,sys
    parser=argparse.ArgumentParser();parser.add_argument('--module-dir',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.module_dir.resolve()));experiment(importlib.import_module('pokerid_g12'),args.output)
