"""New-only true-chance coverage and conservative preflop-only response audit."""
import argparse,json,math,itertools
from pathlib import Path
from gto.abstract import call_study as cs,call_reach as cr,root_interval as ri,street_tree as st,chance_coverage as cache,flop_exact as exact,model
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.range_study import sha
ROOT=Path('docs/qa/root-br-20261105');P=ROOT/'protocol.json';D=ROOT/'design.json';OLD=cs.ROOT

def canonical(b):return min(tuple(sorted(c//4*4+q[c%4] for c in b)) for q in itertools.permutations(range(4)))
def sources():return {**cs.sources(),**{f:sha(Path(__file__).with_name(f)) for f in ('root_interval.py','root_interval.cc','root_br_study.py')}}
def inputs():return {str(p):sha(p) for p in (OLD/'chance.json',OLD/'design.json',OLD/'population-results.json',cs.OLD/'population-results.json')}
def select_events(p):
 old=json.loads((OLD/'population-results.json').read_text());design=json.loads((OLD/'design.json').read_text());chances=json.loads((OLD/'chance.json').read_text())['stages'];fresh={canonical(r['cards']) for r in p['response']['fresh_audit']};candidates=[];selected=[];seen={}
 for stage,r in sorted(design['ranges'].items()):
  v=old['stages'][stage];observed={tuple(row['flop']) for rows in v['sample_rows'].values() for row in rows};observed.update(tuple(row['flop']) for row in v['priority_rows']);seen[stage]=observed
  pool=[{'stage':stage,'flop':b,'board_probability':prob,'score_bb':100*r['conditional_mass']*prob} for b,prob in zip(chances[stage]['flops'],chances[stage]['probabilities']) if tuple(b) not in observed and canonical(b) not in fresh];pool.sort(key=lambda x:(-x['score_bb'],x['stage'],x['flop']));minimum=p['coverage']['minimum_new_events_each_prefix'];selected.extend(pool[:minimum]);candidates.extend(pool[minimum:])
 candidates.sort(key=lambda x:(-x['score_bb'],x['stage'],x['flop']));selected.extend(candidates[:p['coverage']['new_events']-len(selected)]);selected.sort(key=lambda x:(x['stage'],x['flop']));assert len(selected)==p['coverage']['new_events'];assert len({(x['stage'],tuple(x['flop'])) for x in selected})==len(selected)
 return {'protocol_sha256':sha(P),'source_sha256':sources(),'input_sha256':inputs(),'selected_events':selected,'ranges':design['ranges'],'predicted_conservative_width_gain_bb':math.fsum(x['score_bb'] for x in selected),'no_new_ev_accessed':True}
def check():
 d=json.loads(D.read_text())
 if d['protocol_sha256']!=sha(P) or d['source_sha256']!=sources() or d['input_sha256']!=inputs():raise ValueError('immutable source/design/input mismatch')
 return d

def responses(root,p,d):
 env=cs.setup(root);rows=[];spec=json.loads(cs.P.read_text());cases=[{**r,'kind':'known_diagnostic'} for r in p['response']['diagnostic_known_cases']]+[{'stage':s,'flop':r['cards'],'kind':'fresh_audit'} for r in p['response']['fresh_audit'] for s in p['response']['stages']]
 for case in cases:
  r=frozen_reach(case['stage'],env[3],after_call=True);r=cr.extract(env[3],r['history']+['call'],case['stage']);m=exact.matrix(env[0],case['flop']);g=cs.prepared(env,m,r,spec);trace=ri.respond_until(env[-1],g,p['response']['iteration_checkpoints'],p['response']['threshold_nashconv_bb'])
  if 'old512_nashconv_bb' in case and abs(trace[0]['restricted_nashconv_bb']-case['old512_nashconv_bb'])>1e-8:raise ValueError('same-game512 baseline mismatch')
  rows.append({**case,'trace':trace,'passed':trace[-1]['restricted_nashconv_bb']<=.1,'minimum_registered_checkpoint':trace[-1]['iterations'] if trace[-1]['restricted_nashconv_bb']<=.1 else None});print(json.dumps({'response':case['kind'],'stage':case['stage'],'flop':case['flop'],'iterations':trace[-1]['iterations'],'nashconv_bb':trace[-1]['restricted_nashconv_bb']}),flush=True)
 return {'protocol_sha256':sha(P),'design_sha256':sha(D),'source_sha256':sources(),'rows':rows,'known_diagnostic_pass':all(x['passed'] for x in rows if x['kind']=='known_diagnostic'),'fresh_audit_pass':all(x['passed'] for x in rows if x['kind']=='fresh_audit'),'no_final_tuning':True,'frozen_policy_updated':False,'scope':'same restricted full_multi; responses not used to change fixed512 root target'}

def expand(root,folder,p,d):
 env=cs.setup(root);coeff=ri.build(root/'coeff');preflop=model.load(model.build(root/'preflop'));oldpop=json.loads((OLD/'population-results.json').read_text());spec=json.loads(cs.P.read_text());stages={s:{'known_sb_bb':[0.]*(169*169),'class_board_probability':[0.]*(169*169)} for s in d['ranges']};newrows={s:[] for s in stages};maxerr=0.
 for index,event in enumerate(d['selected_events']):
  s=event['stage'];r=d['ranges'][s];ident={'design_sha256':sha(D),'source_sha256':sources(),'stage':s,'flop':event['flop'],'iterations':512};path=folder/(cache.digest(ident)+'.json');row=cache.cache_load(path,ident)
  if row is None:
   m=exact.matrix(env[0],event['flop']);g=cs.prepared(env,m,r,spec);policy,metric=st.trajectory(env[-1],g,st.uniform(g),[512])[0];known,mass,error=ri.class_partial(env[1],coeff,m,g,policy,r['hero_actor'],r['hero_reach'],r['villain_reach'],metric['profile_hero_ev_bb']);row={**cache.sample_row(metric,r['post_call_pot_bb']),'flop':event['flop'],'board_probability':event['board_probability'],'stage':s,'known_sb_bb':known,'class_board_probability':mass,'class_scalar_error_bb':error};cache.cache_write(path,ident,row)
  for name in ('known_sb_bb','class_board_probability'):
   accum=stages[s][name]
   for i,value in enumerate(row[name]):accum[i]+=value
  maxerr=max(maxerr,row['class_scalar_error_bb']);newrows[s].append({k:v for k,v in row.items() if k not in ('known_sb_bb','class_board_probability')})
  if (index+1)%32==0:print(json.dumps({'new_events_complete':index+1,'total':len(d['selected_events'])}),flush=True)
 merged={};newonly={}
 for s in stages:
  previous=oldpop['stages'][s];rows=[x for values in previous['sample_rows'].values() for x in values]+previous['priority_rows'];merged[s]={'sample_interval':previous['sample_interval'],'deterministic':cs.deterministic(rows+newrows[s])};newonly[s]={'sample_interval':{'uniform512_profile_ev_interval_bb':[-50,50]},'deterministic':cs.deterministic(newrows[s])}
 combined=cs.root_accounting(env[3],merged,spec,json.loads((OLD/'design.json').read_text()));manual=cs.root_accounting(env[3],newonly,spec,json.loads((OLD/'design.json').read_text()));kernel=ri.root_bounds(preflop,env[3],[(d['ranges'][s],stages[s]) for s in stages]);previous_root=oldpop['root'];fold=kernel['profile_sb_ev_interval'];expected=manual['root_sb_conservative50_deterministic_interval_bb'];oldstreet=json.loads((cs.OLD/'population-results.json').read_text())
 # Manual NEW-ONLY tensor audit must treat previous two CALL leaves unknown too.
 for s,data in oldstreet['stages'].items():
  r=frozen_reach(s,env[3],after_call=True);old_det=cs.deterministic(data['draw_rows'])['conservative50_profile_interval_bb'];lo,hi=old_det
  if r['hero_actor']==1:lo,hi=-hi,-lo
  expected[0]+=r['conditional_mass']*(-50-lo);expected[1]+=r['conditional_mass']*(50-hi)
 error=max(abs(a-b) for a,b in zip(fold,expected))
 if error>1e-8:raise ValueError('NEW-only native root tensor and manual scalar accounting mismatch')
 before=previous_root['root_sb_conservative50_deterministic_interval_bb'];after=combined['root_sb_conservative50_deterministic_interval_bb'];criteria={'root_coverage_increases':combined['computed_root_board_probability']>previous_root['computed_root_board_probability'],'deterministic_width_decreases':after[1]-after[0]<before[1]-before[0],'class_scalar_ev_consistency':maxerr<=1e-8,'root_native_manual_consistency':error<=1e-8};used={tuple(b) for b in p['response']['excluded_previous_suit_orbits']};used.update(canonical(r['cards']) for r in p['response']['fresh_audit']);used.update(canonical(e['flop']) for e in d['selected_events'])
 return {'protocol_sha256':sha(P),'design_sha256':sha(D),'source_sha256':sources(),'new_rows':newrows,'class_pair_kernels':stages,'new_only_preflop_br_bounds':kernel,'combined_fixed512_root':combined,'previous_root':previous_root,'new_only_native_manual_error_bb':error,'maximum_class_scalar_ev_error_bb':maxerr,'criteria':criteria,'next_unseen_excluded_orbits':[list(b) for b in sorted(used)],'next_unseen_excluded_orbit_count':len(used),'formal_acceptance_complete':0,'real_game_approximation_error':'UNKNOWN','external_gto_comparison':'NOT PERFORMED','root_statistical_sampling_not_updated':True}

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--phase',choices=('design','responses','expand'),required=True);a.add_argument('--build-dir',type=Path);a.add_argument('--cache-dir',type=Path);a.add_argument('--output',type=Path,required=True);v=a.parse_args();p=json.loads(P.read_text())
 if v.output.exists():a.error('fresh output required; never overwrite final evidence')
 if v.phase=='design':out=select_events(p)
 else:
  d=check()
  if not v.build_dir or v.phase=='expand' and not v.cache_dir:a.error('build/cache directory required')
  out=responses(v.build_dir,p,d) if v.phase=='responses' else expand(v.build_dir,v.cache_dir,p,d)
 v.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({'phase':v.phase,'criteria':out.get('criteria')}))
