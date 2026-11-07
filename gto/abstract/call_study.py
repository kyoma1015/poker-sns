"""Preregistered high-reach continuations; all results remain research-only."""
import argparse,json,math,random
from pathlib import Path
from gto.abstract import call_reach as reach,street_tree as st,chance_coverage as cov,gap_models as gm,flop_exact as exact
from gto.abstract import street_study as old
from gto.abstract.range_study import initialize,sha
from gto.abstract.factorial_transfer import category
ROOT=Path('docs/qa/call-coverage-20261105');OLD=Path('docs/qa/street-coverage-20261105');P=ROOT/'protocol.json';DESIGN=ROOT/'design.json';CHANCE=ROOT/'chance.json'

def sources():
 return {**old.sources(),**{f:sha(Path(__file__).with_name(f)) for f in ('call_reach.py','call_study.py')}}
def setup(root):
 rank,aggregate,flib,pi,digest=initialize(root/'base');return rank,aggregate,flib,pi,digest,gm.build(root/'reference'),st.build(root/'street')
def summarize(rows):
 return {'contexts':len(rows),'mean_nashconv_bb':math.fsum(r['metrics']['restricted_nashconv_bb'] for r in rows)/len(rows),'worst_nashconv_bb':max(r['metrics']['restricted_nashconv_bb'] for r in rows)}
def prepared(env,m,r,p):
 _,aggregate,flib,_,_,ref,_=env;b=reach.book(flib,m,r);g=gm.make_game(aggregate,ref,m,r,b,{'name':'base','arms':4,'bet_fraction':.5,'stack_scale':1,'range':'actual'});tree=st.tree(r['post_call_pot_bb'],r['remaining_stack_bb'],r['hero_actor'],p['bet_fractions']);return st.prepare(aggregate,m,g,tree)
def allocation(weights,total):
 counts={k:1 for k in weights};remaining=total-len(weights);raw={k:remaining*w for k,w in weights.items()}
 for k,x in raw.items():counts[k]+=int(x)
 for k in sorted(weights,key=lambda k:(-(raw[k]-int(raw[k])),k))[:total-sum(counts.values())]:counts[k]+=1
 return counts

def select_priority(rows,count):
 return sorted(rows,key=lambda x:(-x[0],x[1],x[2]))[:count]

def design(root,p,chance_output=CHANCE):
 env=setup(root);pi=env[3];ref=env[5];chances={};ranges={};configs={};priority=[]
 for i,(stage,history) in enumerate(sorted(p['prefixes'].items())):
  r=reach.extract(pi,history,stage);ranges[stage]=r;c=gm.board_chance(ref,r);c['conditional_history']=r['history'];chances[stage]=c;groups={}
  for b,prob in zip(c['flops'],c['probabilities']):groups.setdefault(category(b),[]).append((b,prob));priority.append((r['conditional_mass']*prob*100,stage,b,prob))
  weights={k:math.fsum(prob for _,prob in values) for k,values in sorted(groups.items())};counts=allocation(weights,p['population']['draws_per_prefix']);rng=random.Random(p['population']['seed']+i*p['population']['stage_seed_offset']);draws={k:rng.choices([b for b,_ in groups[k]],weights=[prob for _,prob in groups[k]],k=counts[k]) for k in sorted(groups)};configs[stage]={'stratum_probability':weights,'counts':counts,'draws':draws}
 selected=select_priority(priority,p['population']['priority_count_total']);d={'protocol_sha256':sha(P),'source_sha256':sources(),'frozen_policy_digest':env[4],'allocations':configs,'priority':[{'stage':s,'flop':b,'board_probability':prob,'root_weighted_width_gain_bb':gain} for gain,s,b,prob in selected],'ranges':ranges,'old_population_sha256':sha(OLD/'population-results.json'),'old_root_sha256':sha(OLD/'root-bounds.json'),'no_board_ev_accessed':True,'chance_file_sha256':None};chance_output.write_text(json.dumps({'stages':chances},sort_keys=True,separators=(',',':'))+'\n');d['chance_file_sha256']=sha(chance_output);return d

def load_design():
 d=json.loads(DESIGN.read_text())
 if d['protocol_sha256']!=sha(P) or d['source_sha256']!=sources() or d['chance_file_sha256']!=sha(CHANCE) or d['old_population_sha256']!=sha(OLD/'population-results.json') or d['old_root_sha256']!=sha(OLD/'root-bounds.json'):raise ValueError('locked design/source/base changed')
 return d

def cohort(root,p,d):
 env=setup(root);lib=env[-1];rows=[];chance=json.loads(CHANCE.read_text())['stages'];maps={s:{tuple(b):v for b,v in zip(c['flops'],c['probabilities'])} for s,c in chance.items()};audit=[]
 for split,boards in ((s,p['split'][s]) for s in ('train','validation','final_test')):
  for br in boards:
   m=exact.matrix(env[0],br['cards'])
   for stage,r in sorted(d['ranges'].items()):
    g=prepared(env,m,r,p);raw=gm.direct_mass(env[5],r,m['flop']);expected=maps[stage][tuple(m['flop'])]*chance[stage]['raw_preflop_reach_mass']*17296;error=abs(raw-expected)
    if error>1e-7:raise ValueError('independent board-chance mass mismatch')
    audit.append(error)
    for policy,metric in st.trajectory(lib,g,st.uniform(g),p['iterations']):rows.append({'split':split,'stage':stage,'flop':br['cards'],'category':br['category'],'metrics':metric,'legal_bet_amounts_bb':g['tree']['bet_amounts'],'private_type_counts':[g['h'],g['v']]})
 final=[r for r in rows if r['split']=='final_test'];summary={str(t):summarize([r for r in final if r['metrics']['iterations']==t]) for t in p['iterations']};criteria={'2048worst_at_most_0_1':summary['2048']['worst_nashconv_bb']<=.1,'2048mean_at_most_0_05':summary['2048']['mean_nashconv_bb']<=.05,'2048nonincrease_vs512':all(b['metrics']['restricted_nashconv_bb']<=a['metrics']['restricted_nashconv_bb']+1e-7 for a,b in zip(final[::2],final[1::2]))}
 return {'protocol_sha256':sha(P),'design_sha256':sha(DESIGN),'source_sha256':sources(),'rows':rows,'final_summaries':summary,'final_by_stage':{s:{str(t):summarize([r for r in final if r['stage']==s and r['metrics']['iterations']==t]) for t in p['iterations']} for s in d['ranges']},'criteria':criteria,'maximum_board_chance_mass_error':max(audit),'candidate_selection_performed':False,'formal_acceptance_complete':0,'real_game_approximation_error':'UNKNOWN','external_gto_comparison':'NOT PERFORMED'}

def profile_interval(strata,weights,pot,bound,tail):
 # Reuse the proven concentration/multiplicity code, scaling ONLY profile EV.
 scaled={k:[{**r,'profile_hero_ev_bb':r['profile_hero_ev_bb']*50/bound} for r in rows] for k,rows in strata.items()};out=cov.interval(scaled,weights,pot,tail);factor=bound/50
 for key in ('profile_ev_estimate_bb','profile_sampling_radius_bb'):out[key]*=factor
 for key in ('uniform512_profile_ev_interval_bb','statistical_profile_interval_bb','uncomputed_profile_ev_contribution_bounds_bb'):out[key]=[v*factor for v in out[key]]
 out['uniform512_profile_ev_interval_bb']=[out['uniform512_profile_ev_interval_bb'][0]-1e-7,out['uniform512_profile_ev_interval_bb'][1]+1e-7];out['registered_game_profile_absolute_bound_bb']=bound
 return out

def deterministic(rows):
 unique={tuple(r['flop']):r for r in rows};mass=math.fsum(r['board_probability'] for r in unique.values());known=math.fsum(r['board_probability']*r['profile_hero_ev_bb'] for r in unique.values());return {'evaluated_board_probability':mass,'unique_physical_boards':len(unique),'known_profile_ev_contribution_bb':known,'conservative50_profile_interval_bb':[known-50*(1-mass)-1e-7,known+50*(1-mass)+1e-7],'uncomputed_contribution_bounds_bb':[-50*(1-mass),50*(1-mass)]}

def root_accounting(pi,new_stages,p,d):
 old_data=json.loads((OLD/'population-results.json').read_text());previous=json.loads((OLD/'root-bounds.json').read_text()) # no old learning or EV replay
 from gto.abstract.frozen_flop_reach import frozen_reach
 ranges={s:frozen_reach(s,pi,after_call=True) for s in ('vs_3bet','vs_4bet')};ranges.update(d['ranges']);leaves=reach.leaf_ledger(pi);fold=math.fsum(x['probability']*x['fold_sb_payoff_bb'] for x in leaves if not x['matched']);known_mass=0.;lo=fold;hi=fold;detlo=fold;dethi=fold;beforelo=fold;beforehi=fold;coverage=0.;details={}
 for stage,r in ranges.items():
  new=stage in new_stages;data=new_stages[stage] if new else old_data['stages'][stage];det=data['deterministic'] if new else deterministic(data['draw_rows']);stat=data['sample_interval']['uniform512_profile_ev_interval_bb'] if new else data['checkpoints'][-1]['uniform512_profile_ev_interval_bb'];mass=r['conditional_mass'];low,high=stat;dl,du=det['conservative50_profile_interval_bb']
  if r['hero_actor']==1:low,high=-high,-low;dl,du=-du,-dl
  known_mass+=mass;coverage+=mass*det['evaluated_board_probability'];lo+=mass*low;hi+=mass*high;detlo+=mass*dl;dethi+=mass*du
  if new:beforelo-=50*mass;beforehi+=50*mass
  else:beforelo+=mass*dl;beforehi+=mass*du
  details[stage]={'call_probability':mass,'hero_actor':r['hero_actor'],'evaluated_board_probability':det['evaluated_board_probability'],'root_evaluated_board_probability':mass*det['evaluated_board_probability'],'root_statistical_sb_contribution_interval_bb':[mass*low,mass*high]}
 matched=math.fsum(x['probability'] for x in leaves if x['matched']);unknown=matched-known_mass
 if unknown< -1e-12:raise ValueError('CALL leaves double counted')
 unknown=max(0.,unknown);out={'root_sb_statistical_interval_bb':[lo-50*unknown,hi+50*unknown],'root_sb_conservative50_deterministic_interval_bb':[detlo-50*unknown,dethi+50*unknown],'before_new_computation_deterministic_interval_bb':[beforelo-50*unknown,beforehi+50*unknown],'previous_root_statistical_interval_bb':previous['root_sb_ev_interval_bb'],'previous_root_confidence':previous['confidence'],'root_confidence':p['joint_root_confidence'],'computed_root_board_probability':coverage,'previous_computed_root_board_probability':previous['computed_root_board_probability'],'call_prefix_probability_evaluated':known_mass,'other_call_probability_unknown':unknown,'exact_fold_root_sb_contribution_bb':fold,'prefix_details':details,'scope':'fixed preflop actions, five research continuation profiles, remaining CALLs±50BB; NOT original full frozen payoff or GTO','real_game_approximation_error':'UNKNOWN','external_gto_comparison':'NOT PERFORMED'};return out

def population(root,cache,p,d):
 if not (ROOT/'cohort-results.json').exists():raise ValueError('cohort must precede population; no population-driven selection')
 env=setup(root);pi=env[3];chances=json.loads(CHANCE.read_text())['stages'];maps={s:{tuple(b):prob for b,prob in zip(c['flops'],c['probabilities'])} for s,c in chances.items()};stages={};used=[]
 for stage,r in sorted(d['ranges'].items()):
  cfg=d['allocations'][stage];strata={k:[] for k in cfg['draws']};allrows=[]
  def evaluate(flop):
   ident={'design_sha256':sha(DESIGN),'source_sha256':sources(),'stage':stage,'flop':flop,'iterations':512};path=cache/(cov.digest(ident)+'.json');row=cov.cache_load(path,ident)
   if row is None:
    m=exact.matrix(env[0],flop);game=prepared(env,m,r,p);metric=st.trajectory(env[-1],game,st.uniform(game),[512])[0][1];row={**cov.sample_row(metric,r['post_call_pot_bb']),'flop':flop,'board_probability':maps[stage][tuple(flop)],'stage':stage,'stratum':category(flop)};cov.cache_write(path,ident,row)
   used.append(flop);return row
  for cat,draws in cfg['draws'].items():
   for flop in draws:strata[cat].append(evaluate(flop))
  for rows in strata.values():allrows.extend(rows)
  priority=[evaluate(row['flop']) for row in d['priority'] if row['stage']==stage];allrows+=priority;t=st.tree(r['post_call_pot_bb'],r['remaining_stack_bb'],r['hero_actor'],p['bet_fractions']);bound=max(max(abs(n['c0']),abs(n['c0']+n['c1'])) for n in t['nodes'] if n['actor']<0);interval=profile_interval(strata,cfg['stratum_probability'],r['post_call_pot_bb'],bound,p['population']['one_sided_tail_probability']);det=deterministic(allrows)
  if interval['empty_intersection_failure']:raise ValueError('empty confidence interval, no redraw')
  vals=[x['local_nashconv_bb'] for rows in strata.values() for x in rows];stages[stage]={'sample_interval':interval,'deterministic':det,'sample_rows':strata,'priority_rows':priority,'population512_nashconv':{'mean_bb':math.fsum(vals)/len(vals),'worst_bb':max(vals),'below0_1_count':sum(x<.1 for x in vals),'count':len(vals)},'legal_bet_amounts_bb':t['bet_amounts']};print(json.dumps({'stage':stage,'coverage':det['evaluated_board_probability'],'profile_interval':interval['uniform512_profile_ev_interval_bb'],'deterministic_interval':det['conservative50_profile_interval_bb']}),flush=True)
 root_result=root_accounting(pi,stages,p,d);before=root_result['before_new_computation_deterministic_interval_bb'];after=root_result['root_sb_conservative50_deterministic_interval_bb'];stat=root_result['root_sb_statistical_interval_bb'];prev=root_result['previous_root_statistical_interval_bb'];criteria={'deterministic_width_decreases':after[1]-after[0]<before[1]-before[0],'statistical_width_less_than_previous_half':stat[1]-stat[0]<(prev[1]-prev[0])/2,'root_board_probability_increases':root_result['computed_root_board_probability']>root_result['previous_computed_root_board_probability']}
 import itertools
 canon=lambda b:min(tuple(sorted(c//4*4+q[c%4] for c in b)) for q in itertools.permutations(range(4)))
 excluded={tuple(b) for b in p['excluded_previous_orbits']};excluded.update(canon(r['cards']) for rows in p['split'].values() for r in rows);excluded.update(canon(b) for b in used)
 return {'protocol_sha256':sha(P),'design_sha256':sha(DESIGN),'source_sha256':sources(),'stages':stages,'root':root_result,'criteria':criteria,'family_confidence':.99,'next_unseen_excluded_orbits':[list(b) for b in sorted(excluded)],'next_unseen_excluded_orbit_count':len(excluded),'formal_acceptance_complete':0,'real_game_approximation_error':'UNKNOWN','external_gto_comparison':'NOT PERFORMED'}

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--phase',choices=('design','cohort','population'),required=True);a.add_argument('--build-dir',type=Path,required=True);a.add_argument('--cache-dir',type=Path);a.add_argument('--chance-output',type=Path,default=CHANCE);a.add_argument('--output',type=Path,required=True);args=a.parse_args();p=json.loads(P.read_text())
 if args.output.exists():a.error('fresh output required; original final data is immutable')
 if args.phase=='design':out=design(args.build_dir,p,args.chance_output)
 else:
  d=load_design()
  if args.phase=='population' and args.cache_dir is None:a.error('--cache-dir required')
  out=cohort(args.build_dir,p,d) if args.phase=='cohort' else population(args.build_dir,args.cache_dir,p,d)
 args.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({'phase':args.phase,'criteria':out.get('criteria')}))
