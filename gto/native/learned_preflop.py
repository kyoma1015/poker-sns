"""Frozen learned-policy preflop reports and finite checkpoint learning batches.

Unknown rows/continuations remain unavailable per action. Local deviations and
policy drift are diagnostics, not convergence or whole-game exploitability.
"""
from fractions import Fraction
import json
from pathlib import Path
from gto.native.deviation import local_deviation
from gto.native.infoset_export import PolicySnapshot,UnknownPolicyRow,_digest,report_json
from gto.native.joint_reach import _prepare,_sample
from gto.native.preflop import decision,describe
from gto.native.training import train_batch,contract_for


def _configuration(game):
    config=json.loads(game._public_config_json);rules=config['rules']
    expected={k:v for k,v in rules.items() if k!='version'};rate=Fraction(rules['rake_rate'])
    expected.update(rate_num=rate.numerator,rate_den=rate.denominator)
    if game.stacks!=config['stacks'] or game._native_rules!=expected:
        raise ValueError('native configuration differs from advertised manifest')
    return config


def learned_report(native,game,hero_cards,deals,history,actions,policy,*,hero_seat=0,
                   samples_per_deal=10,seed=17,confidence=0.95,max_deals=128,
                   max_total_samples=100000,max_infosets=100000):
    if type(policy) is not PolicySnapshot:raise ValueError('immutable learned/explicit PolicySnapshot required')
    config=_configuration(game)
    # Validate history/common decision first even when the target policy is absent.
    from gto.native.joint_support import condition_joint_support
    support=condition_joint_support(game.num_players(),hero_cards,deals,[],hero_seat=hero_seat,max_deals=max_deals)
    if not support['deals']:raise ValueError('no compatible joint support for preflop query')
    full=support['deals'][0][0]
    target=decision(native,game,history,cards=[c for h in full for c in h]);desc=describe(target)
    legal=target.legal_actions()
    if (target.current_player()!=hero_seat or not isinstance(actions,(list,tuple)) or not 1<=len(actions)<=64
            or any(type(a) is not int or a not in legal for a in actions) or len(set(actions))!=len(actions)):
        raise ValueError('common hero decision and bounded unique legal interventions required')
    if (type(seed) is not int or type(samples_per_deal) is not int or not 1<=samples_per_deal<=100000
            or type(max_total_samples) is not int or not 1<=max_total_samples<=1000000
            or type(confidence) not in (int,float) or not 0<confidence<1):
        raise ValueError('bounded evaluation controls required')
    profile=policy.observed_row(target)
    identity={'config':config,'hero_cards':list(hero_cards),'hero_seat':hero_seat,
        'deals':[[[list(hand) for hand in hands],str(prior)] for hands,prior in deals],
        'history':list(history),'actions':list(actions),'policy_digest':policy.digest,
        'samples_per_deal':samples_per_deal,'seed':seed,'confidence':confidence}
    base={'schema':'pokerid-learned-joint-preflop-v1','config_digest':_digest(config),
        'policy_digest':policy.digest,'input_digest':_digest(identity),'decision':desc,
        'target_policy':profile,'native_infoset_ev':None,'hand169_ev':None,
        'equilibrium_verified':False,'strategy_convergence':'UNKNOWN',
        'scope':'frozen policy conditional on explicit joint support; not solved GTO'}
    try:
        reach,targets,checked=_prepare(native,game,hero_cards,deals,[],history,policy,
            hero_seat=hero_seat,max_deals=max_deals,max_infosets=max_infosets)
    except UnknownPolicyRow:
        return {**base,'reach':None,'action_values':{a:None for a in actions},
            'action_status':{a:'prefix_policy_unobserved' for a in actions},
            'samples_reserved':0,'samples_completed':0,
            'deviation':{'status':'prefix_policy_unobserved','convergence_verified':False}}
    common=(target.information_state_string(hero_seat),tuple(legal))
    for state,_ in targets:
        if (state.is_terminal() or state.is_chance_node() or state.current_player()!=hero_seat
                or (state.information_state_string(hero_seat),tuple(state.legal_actions()))!=common):
            raise ValueError('support does not share queried native hero infoset')
    reserved=sum(bool(mass) for _,mass in targets)*samples_per_deal*len(actions)
    if reserved>max_total_samples:raise ValueError('aggregate reserved action sample budget exceeded')
    values={};status={};completed=0;per_confidence=1-(1-confidence)/len(actions)
    for action in actions:
        try:
            result=_sample(reach,targets,checked,samples_per_deal=samples_per_deal,seed=seed,
                confidence=per_confidence,max_total_samples=max_total_samples,max_steps=1000,action=action)
            values[action]=result;completed+=result['samples']
            status[action]='sampled' if result['sample_mean_values'] is not None else 'zero_reach'
        except UnknownPolicyRow:
            values[action]=None;status[action]='continuation_policy_unobserved'
    return {**base,'reach':reach,'action_values':values,'action_status':status,
        'samples_reserved':reserved,'samples_completed':completed,'confidence':confidence,
        'deviation':local_deviation(profile,values,legal,hero_seat)}


def learning_batch(native,game,queries,checkpoints,output_root,*,seed=17,max_rows=100000):
    """Train existing native solver, freeze/evaluate at finite iteration counts.

    Each new checkpoint is immutable. All reports retain unknown coverage and
    convergence flags. No scheduler, production adoption or automatic restart.
    """
    if (type(seed) is not int or not isinstance(checkpoints,(list,tuple)) or not checkpoints
            or len(checkpoints)>20 or any(type(i) is not int or not 1<=i<=100000 for i in checkpoints)
            or list(checkpoints)!=sorted(set(checkpoints))
            or not isinstance(queries,(list,tuple)) or not 1<=len(queries)<=32
            or any(not isinstance(q,dict) for q in queries)
            or type(max_rows) is not int or not 1<=max_rows<=1000000):
        raise ValueError('bounded queries and increasing finite native checkpoints required')
    config=_configuration(game);root=Path(output_root);root.mkdir(parents=False,exist_ok=False)
    solver=native.Solver(game,.6,seed,True,True,.1);observations=[];previous=[None]*len(queries)
    for iteration in checkpoints:
        training=train_batch(solver,game,iteration-solver.iteration,root/f'iteration-{iteration}.bin')
        policy=PolicySnapshot.from_solver(native,solver,max_rows=max_rows);reports=[]
        for index,query in enumerate(queries):
            report=learned_report(native,game,policy=policy,**query)
            current=report['target_policy'];old=previous[index]
            drift=(sum(abs(current[a]-old[a]) for a in current)/2
                if old is not None and current is not None and set(old)==set(current) else None)
            report['observed_policy_total_variation']=drift
            report['drift_is_convergence_proof']=False
            previous[index]=current;reports.append(report)
        observation={'iteration':iteration,'policy_digest':policy.digest,'training':training,'queries':reports}
        (root/f'iteration-{iteration}.json').write_text(report_json(observation)+'\n')
        observations.append(observation)
    result={'schema':'pokerid-native-learning-observations-v1','config_digest':_digest(config),
        'contract':contract_for(game),'seed':seed,'observations':observations,
        'convergence_verified':False,'global_exploitability':None,'nash_conv':None,
        'scope':'finite native learning plus conditional policy evaluation; not solver convergence proof'}
    (root/'summary.json').write_text(report_json(result)+'\n')
    return result


def main():
    import argparse
    import importlib
    import sys
    from gto.native.training import NativeGame
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module-dir',type=Path,required=True)
    parser.add_argument('--stacks',type=int,nargs='+',required=True)
    parser.add_argument('--bb',type=int,default=2)
    parser.add_argument('--bba',type=int,default=0)
    parser.add_argument('--rake-num',type=int,default=0)
    parser.add_argument('--rake-den',type=int,default=1)
    parser.add_argument('--rake-cap',type=int)
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--checkpoints',type=int,nargs='+',required=True)
    parser.add_argument('--queries',type=Path,required=True,
        help='JSON query list; deal priors must be exact strings such as "1/2"')
    parser.add_argument('--output',type=Path,required=True,help='fresh output directory')
    args=parser.parse_args()
    if args.queries.stat().st_size>1024*1024:parser.error('query file exceeds1MiB budget')
    queries=json.loads(args.queries.read_text(),parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite query JSON')))
    if not isinstance(queries,list) or not 1<=len(queries)<=32:parser.error('bounded query list required')
    for query in queries:
        if not isinstance(query,dict) or not isinstance(query.get('deals'),list):parser.error('query/deals required')
        rows=[]
        for item in query['deals']:
            if not isinstance(item,list) or len(item)!=2 or not isinstance(item[1],str):parser.error('exact string prior required')
            rows.append((item[0],Fraction(item[1])))
        query['deals']=rows
    sys.path.insert(0,str(args.module_dir.resolve()));native=importlib.import_module('pokerid_g12')
    game=NativeGame(args.stacks,bb=args.bb,bba=args.bba,rake_num=args.rake_num,
        rake_den=args.rake_den,rake_cap=args.rake_cap)
    print(report_json(learning_batch(native,game,queries,args.checkpoints,args.output,seed=args.seed)))


if __name__=='__main__':main()
