"""Preregistered conditional target transfer versus bounded public-board planning."""
import argparse,json,math,time
from pathlib import Path
from gto.abstract import flop_exact as exact,continuation_game as base,range_features as feature
from gto.abstract import value_response as learning
from gto.abstract.factorial_game import game
from gto.abstract.factorial_study import initialize,mk,sha,summary,modelkey
from gto.abstract.factorial_transfer import Transfer
from gto.abstract.generalization_features import uniform_strength
ROOT=Path('docs/qa/value-response-20261104');PROTOCOL=ROOT/'protocol.json';STAGES=('vs_3bet','vs_4bet');SOURCES=('value_study.py','value_response.py','value_response.cc')

def sources():return {p:sha(Path(__file__).with_name(p)) for p in SOURCES}
def check_protocol(p):
 if p!=json.loads(PROTOCOL.read_text()):raise ValueError('protocol differs from preregistration')
def aggregate(rows):
 return {'overall':summary(rows),'by_stage':{s:summary([r for r in rows if r['stage']==s]) for s in STAGES}}
def noninferior(candidate,baseline,tolerance=1e-7):
 return all(candidate['by_stage'][s][m]<=baseline['by_stage'][s][m]+tolerance for s in STAGES for m in ('mean_nashconv_bb','worst_nashconv_bb'))
def choose(candidates):
 baseline=next(c for c in candidates if c['config']['family']=='probability')['summary'];options=[c for c in candidates if c['config']['family']!='probability'];eligible=[c for c in options if noninferior(c['summary'],baseline)]
 winner=min(eligible,key=lambda c:c['summary']['overall']['mean_nashconv_bb']) if eligible else min(options,key=lambda c:c['summary']['overall']['worst_nashconv_bb'])
 return winner['config'],bool(eligible)
def criteria(candidate,baseline,p):
 c,u=candidate['overall'],baseline['overall'];t=p['final_criteria']
 return {'mean_reduction':c['mean_nashconv_bb']<=u['mean_nashconv_bb']*(1-t['mean_reduction_vs_probability_at_least']),'global_worst_nonincrease':c['worst_nashconv_bb']<=u['worst_nashconv_bb']+1e-7,'vs_3bet_noninferiority':all(candidate['by_stage']['vs_3bet'][m]<=baseline['by_stage']['vs_3bet'][m]+t['vs_3bet_mean_and_worst_noninferiority_tolerance_bb'] for m in ('mean_nashconv_bb','worst_nashconv_bb')),'vs_4bet_noninferiority':all(candidate['by_stage']['vs_4bet'][m]<=baseline['by_stage']['vs_4bet'][m]+t['vs_4bet_mean_and_worst_noninferiority_tolerance_bb'] for m in ('mean_nashconv_bb','worst_nashconv_bb')),'absolute_maximum':c['worst_nashconv_bb']<=t['absolute_worst_nashconv_bb']}
def prediction_error(g,control,learner):
 truth=learning.conditional_targets(g,control);weighted=[];worst=0.;n=0
 for k,row in truth.items():
  if row['own_marginal_mass']<=0:continue
  pred=learner.predict(k,'conditional_arm_ev_bb');errors=[abs(a-b) for a,b in zip(pred,row['conditional_arm_ev_bb'])];weighted.append(row['own_marginal_mass']*math.fsum(errors)/8);worst=max(worst,max(errors));n+=1
 return {'own_chance_weighted_mean_absolute_arm_error_bb':math.fsum(weighted),'maximum_conditional_arm_error_bb':worst,'positive_own_types':n,'reference':'conditional utility against fixed matched probability-control opponent; NOT external GTO','sampling_error_bb':0}
def apply_candidate(g,learner,lib,timings,context):
 start=time.perf_counter();p=learner.materialize(g);predict_seconds=time.perf_counter()-start;start=time.perf_counter()
 if learner.config['family']=='response':p,metrics=learning.respond(lib,g,p,learner.config['iterations'])
 else:metrics=base.evaluate(g,p)
 timings.append({**context,'method':learner.config['name'],'prediction_seconds':predict_seconds,'planning_and_exact_metric_seconds':time.perf_counter()-start})
 return p,metrics

def select(root,protocol,timings):
 check_protocol(protocol);rank,lib,flib,pi,digest=initialize(root);rlib=learning.build(root/'response');models={mk(s,se):{'records':[],'stage':s,'seed':se} for s in STAGES for se in protocol['learning_initialization_seeds']};teachers=[]
 for row in protocol['split']['train']:
  m=exact.matrix(rank,row['cards']);uniform=uniform_strength(m)
  for stage in STAGES:
   g=game(lib,m,pi,stage,feature.books(flib,m,pi,stage,uniform))
   for seed in protocol['learning_initialization_seeds']:
    p,metrics=base.solve(lib,g,protocol['teacher_iterations'],seed);targets=learning.conditional_targets(g,p);zero=0
    for k,t in sorted(targets.items()):
     if t['own_marginal_mass']<=0:zero+=1;continue
     models[mk(stage,seed)]['records'].append({'key':list(k),'training_flop':row['cards'],'category':row['category'],**t})
    teachers.append({'flop':row['cards'],'category':row['category'],'stage':stage,'seed':seed,'metrics':metrics,'zero_mass_own_types_excluded':zero,'positive_own_types':len(targets)-zero})
 geometry=feature.Neighbors([learning.CONFIG]);policies={(k,c['name']):learning.TargetTransfer(v['records'],c,geometry) for k,v in models.items() for c in protocol['candidates']};candidates=[{'config':c,'validation':[]} for c in protocol['candidates']];errors=[]
 for row in protocol['split']['validation']:
  m=exact.matrix(rank,row['cards']);uniform=uniform_strength(m)
  for stage in STAGES:
   g=game(lib,m,pi,stage,feature.books(flib,m,pi,stage,uniform))
   for seed in protocol['learning_initialization_seeds']:
    context={'flop':row['cards'],'category':row['category'],'stage':stage,'seed':seed}
    for c in candidates:
     p,metrics=apply_candidate(g,policies[(mk(stage,seed),c['config']['name'])],rlib,timings,context);c['validation'].append({**context,'metrics':metrics})
     if c['config']['family']=='probability':errors.append({**context,'target_error':prediction_error(g,p,policies[(mk(stage,seed),c['config']['name'])])})
 for c in candidates:c['summary']=aggregate(c['validation'])
 winner,eligible=choose(candidates)
 return {'schema':'pokerid-value-response-selection-v1','protocol_sha256':sha(PROTOCOL),'source_sha256':sources(),'frozen_preflop_policy_digest':digest,'previous_probability_selection_sha256':sha('docs/qa/factorial-generalization-20261104/selection.json'),'accessed_splits':['train','validation'],'selected_config':winner,'validation_stage_constraints_satisfied':eligible,'models':models,'teachers':teachers,'candidate_validation':candidates,'heldout_target_errors':errors,'sampling_error_bb':0,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN','formal_acceptance_complete':0}

def validate(selection,path):
 if selection['protocol_sha256']!=sha(PROTOCOL) or selection['source_sha256']!=sources() or selection['accessed_splits']!=['train','validation']:raise ValueError('selected identity changed')
 if selection['previous_probability_selection_sha256']!=sha('docs/qa/factorial-generalization-20261104/selection.json'):raise ValueError('previous probability control changed')
 lock=json.loads((ROOT/'selection-lock.json').read_text())
 if lock['selection_sha256']!=sha(path):raise ValueError('frozen selection bytes changed')

def final(root,protocol,selection,path,timings):
 check_protocol(protocol);validate(selection,path);rank,lib,flib,pi,digest=initialize(root);rlib=learning.build(root/'response')
 if digest!=selection['frozen_preflop_policy_digest']:raise ValueError('frozen preflop input changed')
 configs=[next(c for c in protocol['candidates'] if c['family']=='probability'),selection['selected_config']];geometry=feature.Neighbors([learning.CONFIG]);policies={(k,c['name']):learning.TargetTransfer(v['records'],c,geometry) for k,v in selection['models'].items() for c in configs};previous=json.loads(Path('docs/qa/factorial-generalization-20261104/selection.json').read_text());rows=[];errors=[]
 # Previous corpus has initialization17/29. Pair fixed controls31->17,43->29;
 # this is explicitly historical, not the matched-condition selection baseline.
 oldpol={}
 for s in STAGES:
  for se,oldse in zip(protocol['learning_initialization_seeds'],(17,29)):
   oldpol[mk(s,se)]=Transfer(previous['models'][modelkey(s,oldse,'range23',previous['selected_shared_method'])],previous['selected_shared_method'],True)
 for row in protocol['split']['final_test']:
  m=exact.matrix(rank,row['cards']);uniform=uniform_strength(m)
  for stage in STAGES:
   g=game(lib,m,pi,stage,feature.books(flib,m,pi,stage,uniform))
   for seed in protocol['learning_initialization_seeds']:
    context={'flop':row['cards'],'category':row['category'],'stage':stage,'seed':seed}
    for c in configs:
     p,metrics=apply_candidate(g,policies[(mk(stage,seed),c['name'])],rlib,timings,context);rows.append({**context,'method':c['name'],'metrics':metrics})
     if c['family']=='probability':errors.append({**context,'target_error':prediction_error(g,p,policies[(mk(stage,seed),c['name'])])})
    p=oldpol[mk(stage,seed)].materialize(g);rows.append({**context,'method':'previous_frozen_probability','metrics':base.evaluate(g,p),'historical_initialization_seed':17 if seed==31 else 29})
 names=[c['name'] for c in configs]+['previous_frozen_probability'];summaries={n:aggregate([r for r in rows if r['method']==n]) for n in names};flags=criteria(summaries[configs[1]['name']],summaries[configs[0]['name']],protocol)
 return {'schema':'pokerid-value-response-final-v1','protocol_sha256':sha(PROTOCOL),'selection_sha256':sha(path),'source_sha256':sources(),'selected_config':selection['selected_config'],'rows':rows,'summaries':summaries,'heldout_target_errors':errors,'criteria':flags,'all_criteria_pass':all(flags.values()),'global_model_updated':False,'selection_performed':False,'local_planning_inference_is_not_zero_shot':selection['selected_config']['family']=='response','sampling_error_bb':0,'numerical_guard_bb':1e-7,'equal_research_board_weights_are_real_chance':False,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN','formal_acceptance_complete':0,'original_cfr_connected':False,'normal_gto_published':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('select','final'),required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--selection',type=Path,default=ROOT/'selection.json');p.add_argument('--output',type=Path,required=True);p.add_argument('--timings',type=Path);a=p.parse_args()
 if a.output.exists():p.error('output already exists; use a fresh path for deterministic verification, never overwrite final evidence')
 protocol=json.loads(PROTOCOL.read_text());timings=[];start=time.perf_counter();out=select(a.build_dir,protocol,timings) if a.phase=='select' else final(a.build_dir,protocol,json.loads(a.selection.read_text()),a.selection,timings);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
 if a.timings:a.timings.write_text(json.dumps({'phase':a.phase,'total_seconds':time.perf_counter()-start,'rows':timings,'scope':'observed wall time, not deterministic or a population benchmark; shared geometry caches warm in declared candidate order'},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'phase':a.phase,'selected':out['selected_config'],'summaries':out.get('summaries'),'criteria':out.get('criteria')}))
