"""All169/action conditional EVs, exact fold cells and restricted response bounds."""
import argparse,json,math,random,time
from pathlib import Path
from gto.abstract.model import classes,CLASSES
from gto.qualification.mccfr_evaluate import interval,open_posterior
from gto.qualification.native_mccfr import betting,rollout
from gto.qualification.policy import act,legal
from gto.qualification.public_response import observe
from gto.qualification.evaluate import atomic
from gto.qualification.action_native import load_solver
from gto.qualification.build import load
from gto.qualification.conditional_action import AllinConditioner,integrated_rollout,restricted_gain

def cell_interval(mean,action,own,context,model,n,logterm):
    lo,hi=-50.,50.
    if model and action==0:lo=hi=(-.5 if context=='rfi' else -1.)
    elif model and action==102:lo,hi=model.bounds(own,context)
    radius=(hi-lo)*math.sqrt(logterm/(2*n))
    return [max(lo,mean-radius),min(hi,mean+radius)]

def evaluate_conditional(s, output, samples=4, seconds=90, conditional=True, evaluation_seed=17118091):
    if samples<4 or samples%2: raise ValueError('even samples>=4 required for disjoint fit/holdout')
    rules=s.rules;before=s.policy_digest
    model=AllinConditioner(s) if conditional else None
    rng=random.Random(evaluation_seed);start=time.monotonic(); reports=[]
    # Conservative family budget > all cells, baselines and fixed-response tests.
    logterm=math.log(2*100000/.001);radius=100*math.sqrt(logterm/(2*samples))
    groups=classes(); unconditional=[len(g)/1326 for g in groups]
    # Exact source-open reach and BB-class posterior, including card removal.
    open_reach,posterior,opens=open_posterior(s)
    for context in ('rfi','vs_3bb_open'):
        b=betting(rules); prefix=[] if context=='rfi' else [8]
        if prefix: act(b,8)
        owner=b.actor;actions=legal(b);hands={};baseline=0.;response=0.; baseline_half=0.
        weights=unconditional if not prefix else posterior
        for label,group,weight in zip(CLASSES,groups,weights):
            if time.monotonic()-start>seconds:
                atomic(output,dict(status='INCOMPLETE_TIME_LIMIT',policy_digest=before,reports=reports,
                                   current_context=context,completed_classes=len(hands),partial_hands=hands))
                return
            values={a:[] for a in actions}; baselines=[]; frequencies={a:0. for a in actions}
            for wi in range(samples):
                attempts=0
                while True:
                    own=list(rng.choice(group));remaining=[c for c in range(52) if c not in own]
                    other_and_board=rng.sample(remaining,7);attempts+=1
                    if not prefix or rng.random()<opens[tuple(sorted(other_and_board[:2]))]: break
                    if attempts>100000 or time.monotonic()-start>seconds:
                        raise RuntimeError('posterior sampling budget exhausted; no completed receipt')
                deck=(own+other_and_board[:2] if owner==0 else other_and_board[:2]+own)+other_and_board[2:]
                tape_seed=rng.getrandbits(128)
                o=observe(b,own,[]);pi=s.row(o,True)
                for a,p in zip(actions,pi): frequencies[a]+=p/samples
                for a in actions:
                    values[a].append(model.value(own,context,random.Random(tape_seed)) if conditional and a==102 else (integrated_rollout if conditional else rollout)(s,deck,random.Random(tape_seed),prefix+[a])[owner])
                baselines.append(math.fsum(p*values[a][-1] for a,p in zip(actions,pi)))
            # Exact deterministic fold and conditional all-in payoff ranges.
            if conditional:
                value=-.5 if context=='rfi' else -1.
                assert all(v==value for v in values[0])
            # Fit a class-only pure action, then measure on disjoint worlds.
            half=samples//2;selected=max(actions,key=lambda a:sum(values[a][:half])/half)
            mean=sum(baselines)/samples;held=sum(values[selected][half:])/half
            baseline+=weight*mean;baseline_half+=weight*sum(baselines[half:])/half
            response+=weight*held
            hands[label]=dict(combinations=len(group),n=samples,baseline_ev_bb=mean,
                baseline_interval_bb=interval(mean,radius),sampled_frequencies=frequencies,selected_action=selected,
                selected_action_holdout_ev_bb=held,
                action_ev_bb={str(a):dict(mean=sum(v)/samples,interval=cell_interval(sum(v)/samples,a,group[0],context,model,samples,logterm),sample_variance=sum((x-sum(v)/samples)**2 for x in v)/(samples-1))
                              for a,v in values.items()})
        aggregate_radius=100*math.sqrt(logterm*sum(w*w/samples for w in weights)/2)
        gain_radius=200*math.sqrt(logterm*sum(w*w/(samples//2) for w in weights)/2)
        gain=response-baseline_half
        reports.append(dict(context=context,range_law='exact source3BB open reach/card-removal posterior with within-class rejection sampling' if prefix else 'true uniform root deal',
            source_open_reach=open_reach if prefix else None, class_weights=weights,
            action_count=len(actions),hands=hands,baseline_ev_bb=baseline,
            baseline_interval_bb=interval(baseline,aggregate_radius),
            class_pure_response_holdout_ev_bb=response,
            class_pure_response_gain_bb=gain,root_gain_scale=open_reach if prefix else 1.,gain_interval_bb=[max(-100,gain-gain_radius),min(100,gain+gain_radius)],
            full_br_ev_upper_bb=None,full_br_gain_upper_bb=None,
            full_br_point_bb=None,all169_precision_pass=False))
        reports[-1]['restricted_first_decision_BR']=restricted_gain(hands,actions,weights)
        atomic(output,dict(status='RUNNING',policy_digest=before,reports=reports))
    assert before==s.policy_digest
    atomic(output,dict(status='BLOCKED_UNVERIFIED',policy_digest=before,
        iteration=s.iteration,visited_information_sets=len(s.rows),reports=reports,
        elapsed_seconds=time.monotonic()-start,nashconv_bb=None,nashconv_upper_bb=None,
        surrogate_continuation_model_used=False,full_native_rollout=False,
        full_game_reference_rollout=True,native_terminal_rank=True,
        surrogate_model_error_bb=0,uniform_execution_discrepancy_upper_bb=None,
        uniform_conditional_ev_error_upper_bb=None,
        continuation_error_note='no surrogate; sampling and optimization uncertainty NOT zero',
        ordinary_registry_admission=False,confidence=.999,
        evaluation_worlds_per_class=samples,conditional=conditional,evaluation_seed=evaluation_seed,last_world_tape_seed=tape_seed,formal_acceptance_complete=0))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--output',required=True);p.add_argument('--sampled',action='store_true');a=p.parse_args()
    rules,native=load(a.build);s=load_solver(rules,native,a.checkpoint);evaluate_conditional(s,a.output,conditional=not a.sampled)
