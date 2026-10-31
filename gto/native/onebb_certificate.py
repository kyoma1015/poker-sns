"""Whole-game action bounds for the explicit HU1BB forced-blind-all-in game.

This is NOT an ordinary RFI/open/3bet certificate. The game has exactly one
strategic decision per ordered hero hand and no later player decisions. Thus
simultaneous action-value bounds really do bound whole-game improvement here.
The bound is statistical under uniform independent native chance sampling;
it is not a deterministic exact-equity proof or a generic poker regret bound.
"""
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from gto.hand169 import CLASSES,hand_class
from gto.native.hand169_bridge import card_name


def representative(label):
    if label not in CLASSES:raise ValueError('standard169class required')
    rank='23456789TJQKA'
    a=rank.index(label[0])*4;b=rank.index(label[1])*4
    return [a,b+(1 if len(label)==2 or label.endswith('o') else 0)]


def evaluate_counts(counts,*,failure_probability=Fraction(1,10**9)):
    """Recompute every sample mean/interval and the complete-game bound.

    Coverage expands169canonical classes by exact suit and own-card-order
    isomorphisms, not by claiming1326independently sampled hero combinations.
    """
    if (not isinstance(failure_probability,Fraction) or not 0<failure_probability<1
            or not isinstance(counts,dict) or set(counts)!=set(CLASSES)):
        raise ValueError('complete169count rows and exact failure probability required')
    hands={};minimum=math.inf;weighted_mean=Fraction(0);weighted_radius=0.0
    for label in CLASSES:
        row=counts[label]
        if (not isinstance(row,dict) or set(row)!={'wins','losses','ties','samples','seed'}
                or any(type(row[k]) is not int or row[k]<0 for k in row)
                or not 1<=row['samples']<=1000000 or row['wins']+row['losses']+row['ties']!=row['samples']):
            raise ValueError('complete bounded integer native sample counts required')
        n=row['samples'];mean=Fraction(row['wins']-row['losses'],n)
        radius=math.nextafter(2*math.sqrt(math.log(float(Fraction(2*169)/failure_probability))/(2*n)),math.inf)
        lower=max(-1.0,math.nextafter(float(mean)-radius,-math.inf))
        upper=min(1.0,math.nextafter(float(mean)+radius,math.inf))
        combinations=6 if len(label)==2 else 4 if label.endswith('s') else 12
        minimum=min(minimum,lower+.5)
        weighted_mean+=Fraction(combinations,1326)*mean
        weighted_radius+=combinations/1326*radius
        hands[label]={'combinations':combinations,'frequencies':[0.0,1.0],
            'evBb':float(mean),'evIntervalBb':[lower,upper],
            'samples':n,'canonicalCards':representative(label),
            'foldEvBb':-.5,'callDominanceLowerBb':lower+.5}
    if abs(float(weighted_mean))>weighted_radius:
        raise ValueError('symmetric ex-ante zero value outside aggregate sampling interval')
    return {'hands':hands,'all_classes_call_dominant':minimum>0,
        'minimum_dominance_lower_bb':minimum,
        'max_unilateral_gain_upper_bb':0.0 if minimum>0 else max(0.0,-minimum),
        'confidence':float(1-failure_probability),'failure_probability':str(failure_probability),
        'conditional_ev_simultaneous_radius_bb':max((h['evIntervalBb'][1]-h['evIntervalBb'][0])/2 for h in hands.values()),
        'ex_ante_profile_value_exact_bb':[0,0], 'weighted_sample_value_bb':float(weighted_mean),
        'strategic_infosets':2652,'hand_classes':169,'concrete_hero_combinations':1326,
        'direct_sampled_representatives':169,'coverage_method':'exact suit/order orbits of169canonical hero hands',
        'method':'two-sided Hoeffding +169class union bound; full-game action dominance',
        'scope':'HU1BB forced-blind-all-in full native game only; not ordinary RFI or3bet'}


def native_profile_bound(solver,counts):
    """Bound the actual learned average over every2652ordered hero infoset.

    Native initialization pseudocounts do not establish learning: rows with
    updates==0 remain unknown and receive a conservative worst-case gap bound.
    """
    evidence=evaluate_counts(counts);lower=Fraction(0);upper=Fraction(0);seen=set();updated=0
    records=[];by_class={label:[] for label in CLASSES}
    for key in solver.keys():
        info=json.loads(key)
        if info['seat']!=0 or info['board'] or info['betting_history']:
            raise ValueError('unexpected strategic infoset outside complete oneBB game')
        pair=tuple(info['hand'])
        if len(pair)!=2 or pair[0]==pair[1] or any(type(c) is not int or not 0<=c<52 for c in pair) or pair in seen:
            raise ValueError('unexpected ordered native hero identity')
        seen.add(pair);row=solver.row(key)
        if type(row['updates']) is not int or row['updates']<0:raise ValueError('native update provenance required')
        if not row['updates']:continue
        if row['actions']!=[0,1] or len(row['average'])!=2 or any(not math.isfinite(v) or v<0 for v in row['average']):
            raise ValueError('native fold/call average policy required')
        values=[Fraction(v) for v in row['average']];total=sum(values)
        if not total:continue
        fold=values[0]/total;updated+=1
        label=hand_class([card_name(c) for c in pair]);by_class[label].append(fold)
        lo,hi=evidence['hands'][label]['evIntervalBb']
        lower+=fold*max(Fraction(0),Fraction(lo)+Fraction(1,2))/2652
        upper+=fold*max(Fraction(0),Fraction(hi)+Fraction(1,2))/2652
        records.append([key,str(fold)])
    # Every absent or updater-unobserved row may choose the worst available action.
    max_gap=max(max(0.0,h['evIntervalBb'][1]+.5) for h in evidence['hands'].values())
    upper+=Fraction(2652-updated,2652)*Fraction(max_gap)
    classes={label:{'updated_orderings':len(rows),'expected_orderings':2*evidence['hands'][label]['combinations'],
        'mean_fold_frequency':float(sum(rows,Fraction())/len(rows)) if rows else None}
        for label,rows in by_class.items()}
    return {'iteration':solver.iteration,'updated_ordered_infosets':updated,'expected_ordered_infosets':2652,
        'complete_policy_coverage':updated==2652,'observed_classes':sum(bool(v) for v in by_class.values()),
        'full_game_unilateral_gain_interval_bb':[max(0.0,math.nextafter(float(lower),-math.inf)),
            math.nextafter(float(upper),math.inf)],
        'policy_digest':hashlib.sha256(json.dumps(sorted(records),separators=(',',':')).encode()).hexdigest(),
        'classes':classes,'confidence':evidence['confidence'],
        'scope':'complete oneBB game average-policy bound; unknown rows conservatively bounded, not filled'}


def experiment(runtime,output,*,samples=10000):
    import importlib
    import sys
    from gto.native.build_onebb import build
    from gto.native.training import NativeGame,train_batch
    from gto.native.learned_preflop import learning_batch
    runtime=Path(runtime).resolve();output=Path(output);output.mkdir(exist_ok=False)
    metadata=build(runtime)
    sys.path[:0]=[str(runtime/'onebb'),str(runtime/'g12_next')]
    sampler=importlib.import_module('pokerid_onebb');native=importlib.import_module('pokerid_g12')
    game=NativeGame([2,2]);runs=[]
    for seed in (17,29):
        counts={}
        for index,label in enumerate(CLASSES):
            counts[label]=dict(sampler.sample(game,representative(label),samples,seed*1000+index))
            if index%40==0:print(json.dumps({'phase':'onebb full-game sampling','seed':seed,'classes':index+1}),flush=True)
        evidence=evaluate_counts(counts)
        if not evidence['all_classes_call_dominant']:raise ValueError('whole-game dominance not certified; no UI candidate')
        runs.append({'seed':seed,'counts':counts,'evidence':evidence})
    source={k:v for k,v in metadata.items() if k in ('source_sha256','rules_sha256','native_state_sha256')}
    candidate={'schema':'pokerid-onebb-complete-game-evidence-v1','formal_profile':False,
        'model':'HU1BB forced blind all-in; full52card native game; no ante/rake',
        'config':json.loads(game._public_config_json),'sources':source,'runs':runs,
        'strategy':'SB call always; BB has no choice; no further player decisions',
        'ordinary_rfi_open_certificate':False,'ordinary_threebet_certificate':False,
        'primary_seed':17,'joint_confidence':float(1-2*Fraction(1,10**9))}
    encoded=json.dumps(candidate,sort_keys=True,separators=(',',':'),allow_nan=False)
    frozen=Path(__file__).resolve().parents[2]/'docs/qa/full-game-calibration-20261027/onebb-evidence.json'
    if samples==10000 and frozen.exists() and frozen.read_text().rstrip('\n')!=encoded:
        raise ValueError('full native experiment differs from frozen reproducibility evidence')
    (output/'onebb-evidence.json').write_text(encoded+'\n')
    digest=hashlib.sha256(encoded.encode()).hexdigest()
    solver=native.Solver(game,.6,17,True,True,.1);curves=[]
    for checkpoint in (2000,20000,100000):
        train_batch(solver,game,checkpoint-solver.iteration,output/f'onebb-{checkpoint}.bin')
        curves.append(native_profile_bound(solver,runs[0]['counts']))
    (output/'onebb-native-learning.json').write_text(json.dumps(curves,sort_keys=True)+'\n')
    # Existing representative test models remain separate from the solved calibration.
    queries=[{'hero_cards':[48,49],'deals':[([[0,1]],Fraction(1))],'hero_seat':seat,
        'history':history,'actions':[0],'samples_per_deal':1,'seed':17}
        for seat,history in ((0,[]),(1,[8]),(0,[8,20]))]
    representative_report=learning_batch(native,NativeGame([100,100]),queries,[200,2000],output/'representative',seed=17)
    summary={'evidence_sha256':digest,'samples_per_class':samples,'classes':169,'seeds':[17,29],
        'direct_terminal_evaluations':samples*169*2,'joint_confidence':candidate['joint_confidence'],
        'minimum_dominance_lower_bb':min(r['evidence']['minimum_dominance_lower_bb'] for r in runs),
        'native_learning':[{'iteration':r['iteration'],'updated_ordered_infosets':r['updated_ordered_infosets'],
            'full_game_unilateral_gain_interval_bb':r['full_game_unilateral_gain_interval_bb']} for r in curves],
        'representative_queries':[{'iteration':o['iteration'],'queries':[{'stage':q['decision']['stage'],
            'frequency_observed':q['target_policy'] is not None,'actions':q['action_status'],
            'full_game_convergence_verified':False} for q in o['queries']]} for o in representative_report['observations']]}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('ONEBB_SUMMARY '+json.dumps(summary,sort_keys=True),flush=True)
    print('ONEBB_EVIDENCE '+encoded,flush=True)
    return summary


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=10000)
    args=parser.parse_args();experiment(args.runtime,args.output,samples=args.samples)
