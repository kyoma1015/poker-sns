"""Extended action-tree comparison and separately labelled population EV study."""
import argparse,json,math
from collections import OrderedDict
from pathlib import Path
from gto.abstract import street_tree as st,chance_coverage as coverage,gap_models as gm
from gto.abstract import gap_study,flop_exact as exact,range_features as feature
from gto.abstract.generalization_features import uniform_strength
from gto.abstract.factorial_transfer import category
from gto.abstract.range_study import sha,mk
ROOT=Path('docs/qa/street-coverage-20261105');PROTOCOL=ROOT/'protocol.json';CHANCE=Path('docs/qa/model-gap-20261105/board-chance.json');STAGES=('vs_3bet','vs_4bet')
FILES=('street_tree.cc','street_tree.py','chance_coverage.py','street_study.py','gap_models.py','gap_reference.cc','range_features.py','generalization_features.py','flop_exact.py','flop_exact_matrix.cc','precision_native.cc','continuation_game.cc','frozen_flop_reach.py')

def sources():return {f:sha(Path(__file__).with_name(f)) for f in FILES}
def check(p):
 if p!=json.loads(PROTOCOL.read_text()) or p['board_chance_sha256']!=sha(CHANCE):raise ValueError('protocol/chance identity changed')
def setup(root):
 env=gap_study.setup(root/'old');return env,st.build(root/'street')
def model_for(env,m,stage,spec):
 _,aggregate,flib,pi,_,ref,_,reaches=env;r=reaches[stage];book=feature.books(flib,m,pi,stage,uniform_strength(m));variant={'name':'base','arms':4,'bet_fraction':.5,'stack_scale':1,'range':'actual'};g=gm.make_game(aggregate,ref,m,r,book,variant);t=st.tree(r['post_call_pot_bb'],r['remaining_stack_bb'],r['hero_actor'],spec['bet_fractions']);return g,book,st.prepare(aggregate,m,g,t)

def contexts(env,p,splits):
 rank,aggregate,flib,pi,_,ref,learners,reaches=env
 for split in splits:
  for row in p['split'][split]:
   m=exact.matrix(rank,row['cards'])
   for stage in STAGES:
    r=reaches[stage];g,book,half=model_for(env,m,stage,p['games'][0]);multi=st.prepare(aggregate,m,g,st.tree(r['post_call_pot_bb'],r['remaining_stack_bb'],r['hero_actor'],p['games'][1]['bet_fractions']));v={'name':'legacy5','arms':5,'bet_fraction':.5,'stack_scale':1,'range':'actual'};g5=gm.make_game(aggregate,ref,m,r,book,v)
    for seed in p['initialization_seeds']:
     prior=learners[mk(stage,seed)].materialize(g)
     # Separate legacy games are unchanged research baselines, not new CFR trees.
     legacy4,m4=gm.solve(ref,g,prior,4096);legacy5,m5=gm.solve(ref,g5,gm.lift(prior,g5),4096);context={'split':split,'flop':row['cards'],'category':row['category'],'stage':stage,'seed':seed}
     yield context,g,half,multi,legacy4,legacy5,m4,m5

def summaries(rows):
 def one(xs):return {'contexts':len(xs),'mean_nashconv_bb':math.fsum(x['metrics']['restricted_nashconv_bb'] for x in xs)/len(xs),'worst_nashconv_bb':max(x['metrics']['restricted_nashconv_bb'] for x in xs)}
 return {'overall':one(rows),'by_game':{g:one([r for r in rows if r['game']==g]) for g in ('full_half','full_multi')},'by_stage':{s:one([r for r in rows if r['stage']==s]) for s in STAGES}}
def choose(candidates):
 eligible=[c for c in candidates if c['summary']['overall']['worst_nashconv_bb']<=.1 and c['summary']['overall']['mean_nashconv_bb']<=.05]
 return min(eligible,key=lambda c:c['iterations'])['iterations'] if eligible else max(c['iterations'] for c in candidates),bool(eligible)

def select(root,p):
 check(p);env,lib=setup(root);candidates=[{'iterations':n,'validation':[]} for n in p['candidate_iterations']];training=[];legacy=[]
 for context,g,half,multi,p4,p5,m4,m5 in contexts(env,p,('train','validation')):
  for name,prepared in (('full_half',half),('full_multi',multi)):
   for label,policy,normal in (('legacy4',p4,m4),('legacy5',p5,m5)):
    lifted=st.lift_legacy(policy,prepared);metrics=st.evaluate(lib,prepared,lifted);error=abs(metrics['profile_hero_ev_bb']-normal['profile_hero_ev_bb'])
    if error>1e-9:raise ValueError('legacy normal-form/behavioral profile EV mismatch')
    legacy.append({**context,'game':name,'method':label,'metrics':metrics,'normal_form_metrics':normal,'profile_lift_error_bb':error})
   results=st.trajectory(lib,prepared,st.lift_legacy(p5,prepared),p['candidate_iterations'])
   for budget,(_,metrics) in zip(p['candidate_iterations'],results):
    row={**context,'game':name,'metrics':metrics,'public_nodes':len(prepared['tree']['nodes']),'behavioral_scalars':prepared['offsets'][-1]}
    if context['split']=='validation':next(c for c in candidates if c['iterations']==budget)['validation'].append(row)
    else:training.append(row)
 for c in candidates:c['summary']=summaries(c['validation'])
 selected,accepted=choose(candidates)
 return {'schema':'pokerid-street-selection-v1','protocol_sha256':sha(PROTOCOL),'source_sha256':sources(),'frozen_policy_digest':env[4],'frozen_predictor_sha256':sha(gap_study.OLD),'accessed_splits':['train','validation'],'selected_iterations':selected,'validation_criteria_pass':accepted,'candidate_validation':candidates,'training_curves':training,'legacy_reference_rows':legacy,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN','formal_acceptance_complete':0}

def validate(selection,path):
 if selection['protocol_sha256']!=sha(PROTOCOL) or selection['source_sha256']!=sources() or selection['frozen_predictor_sha256']!=sha(gap_study.OLD) or selection['accessed_splits']!=['train','validation']:raise ValueError('selected source/data identity changed')
 lock=json.loads((ROOT/'selection-lock.json').read_text())
 if lock['selection_sha256']!=sha(path):raise ValueError('selected bytes changed')

def final(root,p,selection,path):
 check(p);validate(selection,path);env,lib=setup(root)
 if env[4]!=selection['frozen_policy_digest']:raise ValueError('frozen preflop policy changed')
 rows=[];legacy=[];cross=[];budget=selection['selected_iterations']
 for context,g,half,multi,p4,p5,m4,m5 in contexts(env,p,('final_test',)):
  solved={}
  for name,prepared in (('full_half',half),('full_multi',multi)):
   for label,policy,normal in (('legacy4',p4,m4),('legacy5',p5,m5)):
    metric=st.evaluate(lib,prepared,st.lift_legacy(policy,prepared));error=abs(metric['profile_hero_ev_bb']-normal['profile_hero_ev_bb'])
    if error>1e-9:raise ValueError('final legacy plan lift failed')
    legacy.append({**context,'game':name,'method':label,'metrics':metric,'normal_form_metrics':normal,'profile_lift_error_bb':error})
   policy,metrics=st.trajectory(lib,prepared,st.lift_legacy(p5,prepared),[budget])[0];solved[name]=policy;rows.append({**context,'game':name,'metrics':metrics,'public_nodes':len(prepared['tree']['nodes']),'behavioral_scalars':prepared['offsets'][-1]})
  extended=st.extend_half(solved['full_half'],half,multi);metric=st.evaluate(lib,multi,extended);profile_error=abs(metric['profile_hero_ev_bb']-next(x['metrics']['profile_hero_ev_bb'] for x in reversed(rows) if x['game']=='full_half'))
  if profile_error>1e-9:raise ValueError('half-to-multi extension changed realized profile')
  cross.append({**context,'metrics':metric,'extension':p['half_to_multi_extension'],'realized_profile_ev_error_bb':profile_error,'not_a_unique_offtree_extension':True})
 summary=summaries(rows);reference={name:summaries([r for r in legacy if r['method']==name]) for name in ('legacy4','legacy5')};flags={'both_games_worst_below_0_1':summary['overall']['worst_nashconv_bb']<=.1,'both_games_mean_below_0_05':summary['overall']['mean_nashconv_bb']<=.05,'both_references_mean_reduction_50percent':all(summary['by_game'][g]['mean_nashconv_bb']<=reference['legacy5']['by_game'][g]['mean_nashconv_bb']*.5 for g in ('full_half','full_multi')),'reference_worst_nonincrease':all(summary['by_game'][g]['worst_nashconv_bb']<=reference['legacy5']['by_game'][g]['worst_nashconv_bb']+1e-7 for g in ('full_half','full_multi'))}
 return {'schema':'pokerid-street-final-v1','protocol_sha256':sha(PROTOCOL),'selection_sha256':sha(path),'source_sha256':sources(),'selected_iterations':budget,'rows':rows,'summary':summary,'legacy_reference_rows':legacy,'legacy_reference_summaries':reference,'half_policy_extended_to_multi':cross,'criteria':flags,'all_criteria_pass':all(flags.values()),'global_model_updated':False,'selection_performed':False,'sampling_error_fixed_board_bb':0,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN','formal_acceptance_complete':0}

def population(root,p,selection,path,cache_dir):
 check(p);validate(selection,path)
 if not (ROOT/'final-results.json').exists():raise ValueError('population integration only after locked final, never for selection')
 env,lib=setup(root);rank,aggregate,flib,pi,digest,ref,learners,reaches=env;chance=json.loads(CHANCE.read_text())['stages'];probabilities={s:{tuple(b):v for b,v in zip(chance[s]['flops'],chance[s]['probabilities'])} for s in STAGES};identity_base={'protocol_sha256':sha(PROTOCOL),'source_sha256':sources(),'frozen_policy_digest':digest,'game':'full_multi','iterations':p['population']['solver_iterations'],'initialization':'uniform'};result={};mcache=OrderedDict();all_evaluated=[]
 for stage in STAGES:
  config=p['population']['allocations'][stage];weights=config['stratum_probability'];strata={k:[] for k in weights};checkpoints=[];previous=None
  for checkpoint in config['checkpoints']:
   for kind,n in sorted(checkpoint['by_stratum'].items()):
    while len(strata[kind])<n:
     flop=p['population']['draws'][stage][kind][len(strata[kind])];identity={**identity_base,'stage':stage,'flop':flop};key=coverage.digest(identity);cache=cache_dir/(key+'.json');row=coverage.cache_load(cache,identity)
     if row is None:
      b=tuple(flop)
      if b not in mcache:
       mcache[b]=exact.matrix(rank,flop)
       while len(mcache)>2:mcache.popitem(last=False)
      m=mcache[b];g,book,prepared=model_for(env,m,stage,p['games'][1]);_,metric=st.trajectory(lib,prepared,st.uniform(prepared),[p['population']['solver_iterations']])[0];row={**coverage.sample_row(metric,reaches[stage]['post_call_pot_bb'],p['numerical_guard_bb']),'flop':flop,'board_probability':probabilities[stage][tuple(flop)],'stage':stage,'stratum':kind,'source':'exact card-removal/showdown moments; uniform512behavioralCFR'};coverage.cache_write(cache,identity,row)
     strata[kind].append(row);all_evaluated.append(flop)
   current=coverage.interval(strata,weights,reaches[stage]['post_call_pot_bb'],p['population']['one_sided_tail_probability'],previous)
   if current['draw_count']!=checkpoint['total_draws']:raise ValueError('incomplete checkpoint; no missing-value imputation')
   checkpoints.append(current);previous=current;cache_dir.mkdir(parents=True,exist_ok=True);(cache_dir/(stage+'-checkpoint-'+str(current['draw_count'])+'.json')).write_text(json.dumps(current,sort_keys=True,indent=2)+'\n');print(json.dumps({'population_stage':stage,'draws':current['draw_count'],'physical_probability':current['evaluated_board_probability'],'model_value_interval':current['restricted_game_value_interval_bb'],'empty':current['empty_intersection_failure']}),flush=True)
  rows=[x for values in strata.values() for x in values];last=checkpoints[-1];pot=reaches[stage]['post_call_pot_bb'];result[stage]={'checkpoints':checkpoints,'draw_rows':rows,'criteria':{'physical_probability_at_least_0_003':last['evaluated_board_probability']>=p['population']['coverage_target_probability'],'game_value_width_at_most_half_safe_range':last['restricted_game_value_interval_bb'][1]-last['restricted_game_value_interval_bb'][0]<=pot*.5,'profile_interval_width_at_most50bb':last['uniform512_profile_ev_interval_bb'][1]-last['uniform512_profile_ev_interval_bb'][0]<=50,'no_empty_intersection':not any(c['empty_intersection_failure'] for c in checkpoints)}}
 from itertools import permutations
 def canonical(b):return min(tuple(sorted(c//4*4+q[c%4] for c in b)) for q in permutations(range(4)))
 used={canonical(b) for b in p['excluded_previous_flops']}
 used.update(canonical(r['cards']) for rows in p['split'].values() for r in rows);used.update(canonical(b) for b in all_evaluated)
 return {'schema':'pokerid-street-population-v1','protocol_sha256':sha(PROTOCOL),'selection_sha256':sha(path),'source_sha256':sources(),'stages':result,'family_confidence':1-p['population']['family_failure_probability'],'confidence_assumption':'preregistered IID within-stratum PRNG draws with replacement; simultaneous both stages,3checkpoints,4tails','fixed_population_solver_iterations':p['population']['solver_iterations'],'fixed_population_initialization':'uniform; distinct from selected warm-inference profile','full_physical_chance_support':22100,'exact_computation_coverage_not_statistical_coverage':True,'next_unseen_excluded_orbits':[list(b) for b in sorted(used)],'next_unseen_excluded_orbit_count':len(used),'population_used_for_selection':False,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN','formal_acceptance_complete':0}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('select','final','population'),required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--selection',type=Path,default=ROOT/'selection.json');p.add_argument('--cache-dir',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():p.error('fresh output required; never overwrite original final evidence')
 protocol=json.loads(PROTOCOL.read_text())
 if a.phase=='select':out=select(a.build_dir,protocol)
 else:
  selected=json.loads(a.selection.read_text())
  if a.phase=='population' and not a.cache_dir:p.error('guarded --cache-dir required')
  out=final(a.build_dir,protocol,selected,a.selection) if a.phase=='final' else population(a.build_dir,protocol,selected,a.selection,a.cache_dir)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({'phase':a.phase,'selected_iterations':out.get('selected_iterations'),'criteria':out.get('criteria'),'population_stages':list(out.get('stages',{}))}))
