"""Pre-registered model-gap decomposition; no full-game GTO certification."""
import argparse,hashlib,json,math
from pathlib import Path
from gto.abstract import gap_models as gm,gap_calibration as calibration,gap_adapter as adapter
from gto.abstract import model,range_features as feature,flop_exact as exact,value_response as learning
from gto.abstract import factorial_game as oldgame
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.generalization_features import uniform_strength
from gto.abstract.range_study import initialize,sha,mk
ROOT=Path('docs/qa/model-gap-20261105');PROTOCOL=ROOT/'protocol.json';OLD=Path('docs/qa/value-response-20261104/selection.json');STAGES=('vs_3bet','vs_4bet');SOURCES=('gap_study.py','gap_models.py','gap_calibration.py','gap_adapter.py','gap_reference.cc')

def identities():return {p:sha(Path(__file__).with_name(p)) for p in SOURCES}
def protocol_check(p):
 if p!=json.loads(PROTOCOL.read_text()):raise ValueError('preregistered protocol mismatch')
def setup(root):
 rank,lib,flib,pi,digest=initialize(root);ref=gm.build(root/'reference');old=json.loads(OLD.read_text());geometry=feature.Neighbors([learning.CONFIG]);cfg={'family':'probability','name':'probability_knn9'};learners={k:learning.TargetTransfer(v['records'],cfg,geometry) for k,v in old['models'].items()};reaches={s:frozen_reach(s,pi,after_call=True) for s in STAGES}
 return rank,lib,flib,pi,digest,ref,learners,reaches

def chance_summary(c):
 from gto.abstract.factorial_transfer import category
 counts={};mass={}
 for b,p in zip(c['flops'],c['probabilities']):
  cat=category(b);counts[cat]=counts.get(cat,0)+1;mass[cat]=mass.get(cat,0.)+p
 nontrips=[k for k in counts if k!='trips'];tv=math.fsum(abs(p-(0 if category(b)=='trips' else 1/(len(nontrips)*counts[category(b)]))) for b,p in zip(c['flops'],c['probabilities']))/2
 return {'probability_sum':math.fsum(c['probabilities']),'physical_board_count':len(c['flops']),'category_counts':counts,'actual_category_probability':mass,'category_balanced_research_probability':{k:0 if k=='trips' else 1/len(nontrips) for k in counts},'total_variation_vs_category_balanced_distribution':tv,'total_variation_vs_uniform_physical_boards':math.fsum(abs(p-1/22100) for p in c['probabilities'])/2,'minimum_board_probability':min(c['probabilities']),'maximum_board_probability':max(c['probabilities']),'raw_preflop_reach_mass':c['raw_preflop_reach_mass'],'all22100_is_chance_normalization_not_unseen_policy_evaluation':True}

def cases(env,p,splits,chances,rank_rows,quality):
 rank,lib,flib,pi,digest,ref,learners,reaches=env;maps={s:{tuple(b):v for b,v in zip(chances[s]['flops'],chances[s]['probabilities'])} for s in STAGES}
 for split in splits:
  for row in p['split'][split]:
   m=exact.matrix(rank,row['cards']);uniform=uniform_strength(m);checks=gm.rank_checks(ref,m,p['reference_matchup_seed'],p['independent_rank_checks_per_board']);rank_rows.append({'split':split,'flop':row['cards'],'checks':checks})
   if any(c['mismatch'] for c in checks):raise ValueError('independent rank enumeration mismatch')
   for stage in STAGES:
    reach=reaches[stage];book=feature.books(flib,m,pi,stage,uniform);g=gm.make_game(lib,ref,m,reach,book,p['sensitivity_variants'][0]);preserved=oldgame.game(lib,m,pi,stage,book)
    if g['hkeys']!=preserved['hkeys'] or g['vkeys']!=preserved['vkeys']:raise ValueError('base signal partition differs')
    tensor_error=max(abs(a-b) for ra,rb in zip(g['tensor'],preserved['tensor']) for ca,cb in zip(ra,rb) for aa,ab in zip(ca,cb) for a,b in zip(aa,ab));probability=maps[stage][tuple(sorted(row['cards']))];direct=gm.direct_mass(ref,reach,row['cards']);moment=probability*chances[stage]['raw_preflop_reach_mass']*17296;chance_error=abs(direct-moment)
    if tensor_error>p['numerical_criteria']['base_model_consistency_bb'] or chance_error>p['numerical_criteria']['chance_direct_raw_mass_error']:raise ValueError('base model or board chance consistency failed')
    for seed in p['frozen_predictor_initialization_seeds']:
     learner=learners[mk(stage,seed)];prior=learner.materialize(g);reference=gm.reference(ref,m,g,prior);previous=learning.conditional_targets(g,prior);error=max(abs(a-b) for k,v in reference['targets'].items() if v['ev'] is not None for a,b in zip(v['ev'],previous[k]['conditional_arm_ev_bb']));mass_error=max(abs(v['mass']-previous[k]['own_marginal_mass']) for k,v in reference['targets'].items());metric=gm.evaluate(g,prior);metric_error=max(abs(reference['metrics'][k]-metric[k]) for k in reference['metrics'])
     if max(error,metric_error)>p['numerical_criteria']['conditional_reference_max_error_bb']:raise ValueError('independent cash-ledger reference mismatch')
     context={'split':split,'flop':row['cards'],'category':row['category'],'stage':stage,'seed':seed,'true_board_probability':probability};quality.append({**context,'conditional_arm_max_implementation_error_bb':error,'own_marginal_max_error':mass_error,'reference_profile_and_br_max_error_bb':metric_error,'base_tensor_max_error_bb':tensor_error,'chance_direct_raw_mass_error':chance_error});predictions={k:learner.predict(k,'conditional_arm_ev_bb') for k in g['hkeys']+g['vkeys']}
     yield context,m,book,g,prior,reference,predictions

def select(root,p,chance_path):
 protocol_check(p);env=setup(root);reaches=env[-1];chances={s:gm.board_chance(env[5],reaches[s]) for s in STAGES};summaries={s:chance_summary(c) for s,c in chances.items()}
 for s in STAGES:
  if abs(summaries[s]['probability_sum']-1)>p['numerical_criteria']['all_board_probability_sum_error']:raise ValueError('all board chance does not sum to1')
  expected=reaches[s]['conditional_mass']*1624350
  if not math.isclose(expected,chances[s]['raw_preflop_reach_mass'],rel_tol=1e-12,abs_tol=1e-9):raise ValueError('preflop class/concrete reach differs')
 chance_path.write_text(json.dumps({'schema':'pokerid-exact-board-chance-v1','stages':chances,'summaries':summaries,'frozen_preflop_policy_digest':env[4],'external_gto_comparison':'NOT PERFORMED'},sort_keys=True,separators=(',',':'))+'\n')
 rank_rows=[];quality=[];training=[]
 for ctx,m,book,g,prior,reference,predictions in cases(env,p,('train',),chances,rank_rows,quality):training.append({'stage':ctx['stage'],'reference':{'targets':reference['targets']},'predictions':predictions})
 coefficients=calibration.fit(training);del training;candidates=[{'method':name,'validation':[]} for name in p['calibration_candidates']]
 for ctx,m,book,g,prior,reference,predictions in cases(env,p,('validation',),chances,rank_rows,quality):
  for c in candidates:c['validation'].append({**ctx,'errors':calibration.errors(g,reference,predictions,ctx['stage'],c['method'],coefficients)})
 for c in candidates:c['summary']=calibration.summary(c['validation'])
 winner=calibration.choose(candidates)
 return {'schema':'pokerid-model-gap-selection-v1','protocol_sha256':sha(PROTOCOL),'source_sha256':identities(),'frozen_preflop_policy_digest':env[4],'frozen_predictor_sha256':sha(OLD),'accessed_splits':['train','validation'],'selected_calibration':winner,'coefficients':coefficients,'candidate_validation':candidates,'independent_rank_checks':rank_rows,'implementation_checks':quality,'chance_summaries':summaries,'external_gto_comparison':'NOT PERFORMED','formal_acceptance_complete':0}

def validate(selection,path):
 if selection['protocol_sha256']!=sha(PROTOCOL) or selection['source_sha256']!=identities() or selection['frozen_predictor_sha256']!=sha(OLD) or selection['accessed_splits']!=['train','validation']:raise ValueError('frozen source/data identity changed')
 lock=json.loads((ROOT/'selection-lock.json').read_text())
 if lock['selection_sha256']!=sha(path) or lock['board_chance_sha256']!=sha(ROOT/'board-chance.json'):raise ValueError('selected calibration or chance bytes changed')

def policy_distance(baseg,p,g,q):
 nh,nv=len(baseg['hkeys']),len(baseg['vkeys']);hm=[math.fsum(baseg['chance_mass'][i*nv+j] for j in range(nv)) for i in range(nh)];vm=[math.fsum(baseg['chance_mass'][i*nv+j] for i in range(nh)) for j in range(nv)];inverse={v:k for k,v in g['base_key_map'].items()};total=0.
 for k,mass in zip(baseg['hkeys']+baseg['vkeys'],hm+vm):
  a=(*p.table[k],*([0.]*(g['actions']-4)));b=q.table[inverse[k]];total+=mass*math.fsum(abs(x-y) for x,y in zip(a,b))/2
 return total

def final(root,p,selection,path):
 protocol_check(p);validate(selection,path);env=setup(root);rank,lib,flib,pi,digest,ref,learners,reaches=env
 if digest!=selection['frozen_preflop_policy_digest']:raise ValueError('frozen preflop policy changed')
 chance=json.loads((ROOT/'board-chance.json').read_text());chances=chance['stages'];quality=[];rank_rows=[];methods=list(dict.fromkeys(('raw',selection['selected_calibration'])));calrows=[];sens=[];leaf_checks=[];partial={(s,se):[0.]*(169*169) for s in STAGES for se in p['frozen_predictor_initialization_seeds']};board_profiles={(s,se):[] for s in STAGES for se in p['frozen_predictor_initialization_seeds']};fullcounts,_=model.chance(model.classes());old_response=learning.build(root/'preserved-response')
 for ctx,m,book,g,prior,reference,predictions in cases(env,p,('final_test',),chances,rank_rows,quality):
  for method in methods:calrows.append({**ctx,'method':method,'errors':calibration.errors(g,reference,predictions,ctx['stage'],method,selection['coefficients'])})
  baseline,baseline_metric=gm.solve(ref,g,prior,p['response_iterations']);preserved_policy,preserved_metric=learning.respond(old_response,g,prior,p['response_iterations']);policy_error=max(abs(a-b) for k,v in baseline.table.items() for a,b in zip(v,preserved_policy.table[k]));nc_error=abs(baseline_metric['restricted_nashconv_bb']-preserved_metric['restricted_nashconv_bb'])
  if max(policy_error,nc_error)>p['numerical_criteria']['base_model_consistency_bb']:raise ValueError('generic/preserved response differs')
  expanded=gm.make_game(lib,ref,m,reaches[ctx['stage']],book,p['sensitivity_variants'][1]);baseline_in_expanded=gm.evaluate(expanded,gm.lift(baseline,expanded));response_reference=gm.reference(ref,m,g,baseline);leaf_error=adapter.leaf_check(lib,ref,m,g,baseline,response_reference);reference_metric_error=max(abs(response_reference['metrics'][k]-baseline_metric[k]) for k in response_reference['metrics'])
  if max(leaf_error,reference_metric_error)>p['numerical_criteria']['readonly_leaf_root_max_error_bb']:raise ValueError('readonly leaf/profile oracle differs')
  leaf_checks.append({**ctx,'class_leaf_max_error_bb':leaf_error,'reference_response_metric_max_error_bb':reference_metric_error,'generic_vs_preserved_probability_max_error':policy_error,'generic_vs_preserved_nashconv_error_bb':nc_error,'class_pairs_with_legal_combos':sum(c>0 for c in response_reference['compatible_class_pair_counts'])});adapter.add_partial(partial[(ctx['stage'],ctx['seed'])],response_reference,fullcounts);board_profiles[(ctx['stage'],ctx['seed'])].append({**ctx,'profile_hero_ev_bb':baseline_metric['profile_hero_ev_bb'],'restricted_nashconv_bb':baseline_metric['restricted_nashconv_bb']})
  for variant in p['sensitivity_variants']:
   vg=g if variant['name']=='base' else expanded if variant['name']=='add_check_fold' else gm.make_game(lib,ref,m,reaches[ctx['stage']],book,variant);frozen=gm.evaluate(vg,gm.lift(baseline,vg));vp,metrics=(baseline,baseline_metric) if variant['name']=='base' else gm.solve(ref,vg,gm.lift(prior,vg),p['response_iterations']);common=None
   if variant['name'] in ('base','add_check_fold','uniform_range'):
    inv={v:k for k,v in vg['base_key_map'].items()};table={k:(*vp.table[inv[k]],*([0.]*(5-vg['actions']))) for k in expanded['hkeys']+expanded['vkeys']};common=gm.evaluate(expanded,gm.FrozenContinuation(table))
   sens.append({**ctx,'variant':variant,'frozen_base_policy_metrics':frozen,'reoptimized_metrics':metrics,'same_physics_expanded5_reference':common,'base4_policy_in_expanded5_nashconv_bb':baseline_in_expanded['restricted_nashconv_bb'],'profile_ev_shift_from_base_bb':metrics['profile_hero_ev_bb']-baseline_metric['profile_hero_ev_bb'],'own_chance_weighted_probability_l1_shift':policy_distance(g,baseline,vg,vp),'raises_available':vg['raises_available'],'model_sensitivity_is_real_game_error_bound':False})
 attribution_lib=model.load(model.build(root/'readonly-preflop'));coverage=[]
 for (stage,seed),rows in board_profiles.items():
  mass=math.fsum(x['true_board_probability'] for x in rows);raw=math.fsum(x['true_board_probability']*x['profile_hero_ev_bb'] for x in rows);equal=math.fsum(x['profile_hero_ev_bb'] for x in rows)/len(rows);weighted=raw/mass;rootcheck=adapter.root_attribution(attribution_lib,pi,reaches[stage],partial[(stage,seed)],raw)
  if rootcheck['absolute_error_bb']>p['numerical_criteria']['readonly_leaf_root_max_error_bb']:raise ValueError('readonly preflop root contribution mismatch')
  coverage.append({'stage':stage,'seed':seed,'selected_physical_boards':len(rows),'total_physical_boards':22100,'true_probability_coverage':mass,'missing_probability_mass':1-mass,'equal_selected_board_ev_bb':equal,'true_chance_conditioned_on_selected_ev_bb':weighted,'conditional_selected_ev_difference_bb':weighted-equal,'selected_raw_ev_contribution_bb':raw,'uncomputed_ev_contribution_absolute_bound_bb':50*(1-mass),'full_continuation_ev_interval_bb':[raw-50*(1-mass),raw+50*(1-mass)],'restricted_nashconv_equal_selected_bb':math.fsum(x['restricted_nashconv_bb'] for x in rows)/len(rows),'restricted_nashconv_true_chance_conditioned_on_selected_bb':math.fsum(x['true_board_probability']*x['restricted_nashconv_bb'] for x in rows)/mass,'tv_selected_true_vs_equal':math.fsum(abs(x['true_board_probability']/mass-1/len(rows)) for x in rows)/2,'full_ev_coverage_complete':mass>=p['full_ev_coverage_required'],'readonly_root_attribution':rootcheck,'not_a_full_preflop_ev':True})
 summaries={method:calibration.summary([r for r in calrows if r['method']==method]) for method in methods};selected=summaries[selection['selected_calibration']];raw=summaries['raw'];criteria={'mean_mae_20percent_reduction':selected['overall']['mean_action_mae_bb']<=raw['overall']['mean_action_mae_bb']*.8,'maximum_error_nonincrease':selected['overall']['maximum_action_error_bb']<=raw['overall']['maximum_action_error_bb']+1e-9,'stagewise_mae_nonincrease':all(selected['by_stage'][s]['mean_action_mae_bb']<=raw['by_stage'][s]['mean_action_mae_bb']+1e-9 for s in STAGES),'stagewise_greedy_loss_nonincrease':all(selected['by_stage'][s]['mean_one_sided_greedy_regret_loss_bb']<=raw['by_stage'][s]['mean_one_sided_greedy_regret_loss_bb']+1e-9 for s in STAGES)}
 return {'schema':'pokerid-model-gap-final-v1','protocol_sha256':sha(PROTOCOL),'selection_sha256':sha(path),'source_sha256':identities(),'selected_calibration':selection['selected_calibration'],'calibration_rows':calrows,'calibration_summaries':summaries,'calibration_criteria':criteria,'sensitivity_rows':sens,'coverage_and_readonly_attribution':coverage,'implementation_checks':quality,'independent_rank_checks':rank_rows,'leaf_checks':leaf_checks,'chance_summaries':chance['summaries'],'global_model_updated':False,'selection_performed':False,'sampling_error_fixed_model_bb':0,'numerical_guard_bb':1e-7,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN','formal_acceptance_complete':0,'original_cfr_modified':False,'normal_gto_published':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('select','final'),required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--selection',type=Path,default=ROOT/'selection.json');p.add_argument('--chance-output',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():p.error('use fresh output path; never overwrite original final evidence')
 protocol=json.loads(PROTOCOL.read_text())
 if a.phase=='select':
  if not a.chance_output:p.error('--chance-output required for all-board normalization')
  if a.chance_output.exists():p.error('chance output exists')
  out=select(a.build_dir,protocol,a.chance_output)
 else:out=final(a.build_dir,protocol,json.loads(a.selection.read_text()),a.selection)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({'phase':a.phase,'selected':out['selected_calibration'],'summaries':out.get('calibration_summaries'),'criteria':out.get('calibration_criteria')}))
