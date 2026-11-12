"""Preregistered public reached-range selection and immutable final evaluation."""
import argparse,hashlib,json,math
from pathlib import Path
from gto.abstract import flop_exact as exact,continuation_game as base
from gto.abstract import range_features as feature
from gto.abstract.range_game import game
from gto.abstract.generalization_features import uniform_strength,TransferPolicy
from gto.abstract.precision_archive import unpack
PROTOCOL=Path('docs/qa/range-generalization-20261101/protocol.json')
SOURCES=('range_study.py','range_features.py','range_game.py','reached_range.cc')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def identities():return {p:sha(Path(__file__).with_name(p)) for p in SOURCES}
def initialize(root):
 packet=json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text());_,p=unpack(packet)
 return exact.build(root/'rank'),base.build(root/'game'),feature.build(root/'features'),p['flop_controller'],packet['policies']['flop_controller']['policy_digest']
def mk(stage,seed):return stage+':'+str(seed)
def dump(p):return [{'key':list(k),'probabilities':list(v)} for k,v in sorted(p.table.items())]
def summary(rows):
 xs=[r['metrics']['restricted_nashconv_bb'] for r in rows];return {'mean_nashconv_bb':math.fsum(xs)/len(xs),'worst_nashconv_bb':max(xs),'evaluations':len(xs)}
def choose(candidates):
 uniform=[c for c in candidates if c['config']['family']=='uniform'];control=min(uniform,key=lambda c:c['summary']['mean_nashconv_bb']);ranges=[c for c in candidates if c['config']['family']=='range'];eligible=[c for c in ranges if c['summary']['worst_nashconv_bb']<=control['summary']['worst_nashconv_bb']];winner=min(eligible or ranges,key=lambda c:c['summary']['mean_nashconv_bb'])
 return control['config'],winner['config'],bool(eligible)

def select(root,protocol):
 if protocol!=json.loads(PROTOCOL.read_text()):raise ValueError('in-memory protocol differs from preregistration')
 rank,lib,flib,pi,digest=initialize(root);models={mk(s,seed):{'records':[],'stage':s,'seed':seed} for s in ('vs_3bet','vs_4bet') for seed in protocol['learning_initialization_seeds']};teacher=[];feature_audit=[]
 for row in protocol['split']['train']:
  m=exact.matrix(rank,row['cards']);uniform=uniform_strength(m)
  for stage in ('vs_3bet','vs_4bet'):
   book=feature.books(flib,m,pi,stage,uniform);g=game(lib,m,pi,stage,book);feature_audit.append({'split':'train','flop':row['cards'],'stage':stage,'public_history':book['public_history'],'seat_audits':book['audits']})
   for seed in protocol['learning_initialization_seeds']:
    p,metrics=base.solve(lib,g,protocol['teacher_iterations'],seed);rows=dump(p)
    for x in rows:x['training_flop']=row['cards']
    models[mk(stage,seed)]['records'].extend(rows);teacher.append({'flop':row['cards'],'stage':stage,'seed':seed,'types':[len(g['hkeys']),len(g['vkeys'])],'metrics':metrics})
 candidates=[{'config':c,'validation':[]} for c in protocol['candidates']];geometry=feature.Neighbors(protocol['candidates']);policies={(k,c['name']):feature.RangePolicy(m['records'],c,geometry) for k,m in models.items() for c in protocol['candidates']}
 for row in protocol['split']['validation']:
  m=exact.matrix(rank,row['cards']);uniform=uniform_strength(m)
  for stage in ('vs_3bet','vs_4bet'):
   book=feature.books(flib,m,pi,stage,uniform);g=game(lib,m,pi,stage,book);feature_audit.append({'split':'validation','flop':row['cards'],'stage':stage,'public_history':book['public_history'],'seat_audits':book['audits']})
   for seed in protocol['learning_initialization_seeds']:
    for c in candidates:
     p=policies[(mk(stage,seed),c['config']['name'])].materialize(g);c['validation'].append({'flop':row['cards'],'stage':stage,'seed':seed,'metrics':base.evaluate(g,p)})
 for c in candidates:c['summary']=summary(c['validation'])
 control,winner,eligible=choose(candidates)
 return {'schema':'pokerid-reached-range-selection-v1','protocol_sha256':sha(PROTOCOL),'source_sha256':identities(),'frozen_preflop_policy_digest':digest,'accessed_splits':['train','validation'],'final_test_evaluated':False,'selected_uniform':control,'selected_range':winner,'validation_worst_constraint_satisfied':eligible,'candidate_validation':candidates,'models':models,'teacher_metrics':teacher,'feature_audits':feature_audit,'equal_board_weights_are_real_chance':False,'external_gto_comparison':'NOT PERFORMED','formal_acceptance_complete':0}

def validate_lock(selection):
 if selection['protocol_sha256']!=sha(PROTOCOL) or selection['source_sha256']!=identities():raise ValueError('source/protocol differs from selected lock')
 if selection['accessed_splits']!=['train','validation'] or selection['final_test_evaluated']:raise ValueError('invalid selection isolation')

def evaluate_locked(root,protocol,selection,selection_path,splits):
 if protocol!=json.loads(PROTOCOL.read_text()):raise ValueError('in-memory protocol differs from preregistration')
 validate_lock(selection);rank,lib,flib,pi,digest=initialize(root)
 if digest!=selection['frozen_preflop_policy_digest']:raise ValueError('frozen preflop policy changed')
 if splits not in (('final_test',),('train','validation')):raise ValueError('explicit isolated evaluation phase required')
 configs=[selection['selected_range'],selection['selected_uniform']];geometry=feature.Neighbors(configs);policies={(k,c['name']):feature.RangePolicy(v['records'],c,geometry) for k,v in selection['models'].items() for c in configs};previous=json.loads(Path('docs/qa/generalization-20261101/selection.json').read_text());oldcache={k:TransferPolicy(v['records'],previous['selected_config']) for k,v in previous['models'].items()};out=[];audits=[]
 for split in splits:
  for row in protocol['split'][split]:
   m=exact.matrix(rank,row['cards']);uniform=uniform_strength(m)
   for stage in ('vs_3bet','vs_4bet'):
    book=feature.books(flib,m,pi,stage,uniform);g=game(lib,m,pi,stage,book);audits.append({'split':split,'flop':row['cards'],'stage':stage,'public_history':book['public_history'],'seat_audits':book['audits']})
    for seed in protocol['learning_initialization_seeds']:
     key=mk(stage,seed);p_range=policies[(key,configs[0]['name'])].materialize(g);p_uniform=policies[(key,configs[1]['name'])].materialize(g);models={'range':p_range,'uniform':p_uniform}
     if split=='final_test':models['previous_frozen_uniform_feature']=oldcache[key].materialize(g)
     for name,p in models.items():out.append({'split':split,'method':name,'flop':row['cards'],'category':row['category'],'stage':stage,'seed':seed,'metrics':base.evaluate(g,p),'fixed_opponents':base.fixed_opponents(g,p) if split=='final_test' else []})
 summaries={split:{name:summary([r for r in out if r['split']==split and r['method']==name]) for name in ('range','uniform',*(['previous_frozen_uniform_feature'] if split=='final_test' else []))} for split in splits}
 flags={}
 if splits==('final_test',):
  r,u=summaries['final_test']['range'],summaries['final_test']['uniform'];criteria=protocol['final_acceptance'];flags={'mean_reduction':r['mean_nashconv_bb']<=u['mean_nashconv_bb']*(1-criteria['mean_reduction_vs_uniform_at_least']),'worst_not_increased':r['worst_nashconv_bb']<=u['worst_nashconv_bb'],'absolute_maximum':r['worst_nashconv_bb']<=criteria['absolute_max_nashconv_bb']}
 return {'schema':'pokerid-reached-range-locked-evaluation-v1','protocol_sha256':sha(PROTOCOL),'selection_sha256':sha(selection_path),'source_sha256':identities(),'frozen_preflop_policy_digest':digest,'evaluated_splits':list(splits),'model_updated':False,'selection_performed':False,'selected_range':selection['selected_range'],'selected_uniform':selection['selected_uniform'],'rows':out,'summaries':summaries,'feature_audits':audits,'preregistered_criteria':flags,'all_criteria_pass':all(flags.values()) if flags else None,'sampling_error_bb':0,'numerical_guard_bb':1e-7,'equal_board_weights_are_real_chance':False,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error_bb':None,'formal_acceptance_complete':0,'original_cfr_connected':False,'normal_gto_published':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('select','final','audit'),required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--selection',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();protocol=json.loads(PROTOCOL.read_text())
 if a.phase=='select':r=select(a.build_dir,protocol)
 else:
  if not a.selection:p.error('frozen --selection required')
  r=evaluate_locked(a.build_dir,protocol,json.loads(a.selection.read_text()),a.selection,('final_test',) if a.phase=='final' else ('train','validation'))
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({'phase':a.phase,'range':r['selected_range'],'uniform':r['selected_uniform'],'summary':r.get('summaries',[(c['config']['name'],c['summary']) for c in r.get('candidate_validation',[])])}))
