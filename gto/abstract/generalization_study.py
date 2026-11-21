"""Pre-registered train/validation selection, then separately locked final test.

Selected board mixtures are equal-weight RESEARCH distributions,not real chance.
Final phase cannot fit/solve/reselect a policy. Fixed frozen preflop arrays remain
unchanged. All policies share rich signals,4arms,and exact evaluation chance.
"""
import argparse,hashlib,json,math
from pathlib import Path
from gto.abstract import flop_exact as exact
from gto.abstract import continuation_game as base
from gto.abstract.generalization_game import game
from gto.abstract.generalization_features import uniform_strength,TransferPolicy
from gto.abstract.continuation_learning import FrozenContinuation
from gto.abstract.precision_archive import unpack
PROTOCOL=Path('docs/qa/generalization-20261101/protocol.json')
SOURCES=('generalization_study.py','generalization_features.py','generalization_game.py')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def identities():return {p:sha(Path(__file__).with_name(p)) for p in SOURCES}
def dump(p):return [{'key':list(k),'probabilities':list(v)} for k,v in sorted(p.table.items())]
def load(rows):return FrozenContinuation({tuple(r['key']):tuple(r['probabilities']) for r in rows})
def initialize(root):
 packet=json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text());_,p=unpack(packet)
 return exact.build(root/'rank'),base.build(root/'game'),p['flop_controller'],packet['policies']['flop_controller']['policy_digest']
def model_key(stage,seed):return stage+':'+str(seed)
def values(rows):
 vals=[x['metrics']['restricted_nashconv_bb'] for x in rows]
 return {'mean_nashconv_bb':math.fsum(vals)/len(vals),'worst_nashconv_bb':max(vals),'contexts':len(vals)}
def material(model,config,g):return TransferPolicy(model['records'],config,load(model['coarse'])).materialize(g)

def choose_candidate(candidates):
 index=min(range(len(candidates)),key=lambda i:(candidates[i]['summary']['mean_nashconv_bb'],i))
 return candidates[index]['config']

def select(root,protocol):
 rank,lib,pi,digest=initialize(root);models={};coarse={s:[] for s in ('vs_3bet','vs_4bet')};teachers=[]
 for s in coarse:
  for seed in protocol['learning_initialization_seeds']:models[model_key(s,seed)]={'stage':s,'seed':seed,'records':[]}
 for item in protocol['split']['train']:
  m=exact.matrix(rank,item['cards']);strength=uniform_strength(m)
  for stage in coarse:
   g=game(lib,m,pi,stage,strength);coarse[stage].append(base.game(lib,m,pi,stage))
   for seed in protocol['learning_initialization_seeds']:
    p,metrics=base.solve(lib,g,protocol['teacher_iterations'],seed);rows=dump(p)
    for row in rows:row['training_flop']=item['cards']
    models[model_key(stage,seed)]['records'].extend(rows);teachers.append({'flop':item['cards'],'stage':stage,'seed':seed,'types':[len(g['hkeys']),len(g['vkeys'])],'metrics':metrics})
 legacy=json.loads(Path('docs/qa/continuation-quality-20261031/results.json').read_text())
 for stage in coarse:
  cg=base.combine(coarse[stage]);old=next(x for x in legacy['rows'] if x['stage']==stage)
  for seed in protocol['learning_initialization_seeds']:
   model=models[model_key(stage,seed)];p,met=base.solve(lib,cg,protocol['coarse_iterations'],seed);model['coarse']=dump(p);model['coarse_training']=met;model['legacy']=next(x['frozen_policy'] for x in old['runs'] if x['initialization_seed']==seed)
 candidates=[{'config':c,'validation':[]} for c in protocol['candidates']]
 # Only train and validation cards are accessed in this phase. Final never built.
 transfer={(model_key(s,seed),c['name']):TransferPolicy(models[model_key(s,seed)]['records'],c,load(models[model_key(s,seed)]['coarse'])) for s in coarse for seed in protocol['learning_initialization_seeds'] for c in protocol['candidates']}
 for item in protocol['split']['validation']:
  m=exact.matrix(rank,item['cards']);strength=uniform_strength(m)
  for stage in coarse:
   g=game(lib,m,pi,stage,strength)
   for seed in protocol['learning_initialization_seeds']:
    for c in candidates:
     p=transfer[(model_key(stage,seed),c['config']['name'])].materialize(g);c['validation'].append({'flop':item['cards'],'stage':stage,'seed':seed,'metrics':base.evaluate(g,p)})
 for c in candidates:c['summary']=values(c['validation'])
 selected=choose_candidate(candidates)
 return {'schema':'pokerid-generalization-selection-v1','protocol_sha256':sha(PROTOCOL),'source_sha256':identities(),'frozen_preflop_policy_digest':digest,'accessed_board_splits':['train','validation'],'final_test_evaluated':False,'selected_config':selected,'candidate_validation':candidates,'teachers':teachers,'models':models,'equal_board_weights_are_real_chance':False,'external_gto_comparison':'NOT PERFORMED','formal_acceptance_complete':0}

def final_test(root,protocol,selection,selection_path):
 if selection['protocol_sha256']!=sha(PROTOCOL) or selection['source_sha256']!=identities():raise ValueError('protocol/source changed after selection lock')
 if selection['final_test_evaluated'] or selection['accessed_board_splits']!=['train','validation']:raise ValueError('invalid selection provenance')
 rank,lib,pi,digest=initialize(root)
 if digest!=selection['frozen_preflop_policy_digest']:raise ValueError('frozen policy changed')
 selected=selection['selected_config'];rows=[]
 # NO solve(),fit(),or validation-based reselection in final phase.
 for item in protocol['split']['final_test']:
  m=exact.matrix(rank,item['cards']);strength=uniform_strength(m)
  for stage in ('vs_3bet','vs_4bet'):
   g=game(lib,m,pi,stage,strength)
   for seed in protocol['learning_initialization_seeds']:
    model=selection['models'][model_key(stage,seed)]
    policies={'selected':material(model,selected,g),'retrained_coarse':material(model,{'kind':'coarse'},g),'previous_frozen':FrozenContinuation({k:load(model['legacy']).table.get(k[:6],(.25,)*4) for k in g['hkeys']+g['vkeys']})}
    for name,p in policies.items():rows.append({'method':name,'category':item['category'],'flop':item['cards'],'stage':stage,'seed':seed,'metrics':base.evaluate(g,p),'fixed_opponent_responses':base.fixed_opponents(g,p),'rich_type_counts':[len(g['hkeys']),len(g['vkeys'])]})
 summaries={name:values([x for x in rows if x['method']==name]) for name in ('selected','retrained_coarse','previous_frozen')};s,b=summaries['selected'],summaries['retrained_coarse'];criteria=protocol['final_acceptance'];flags={'relative_mean_reduction':s['mean_nashconv_bb']<=b['mean_nashconv_bb']*(1-criteria['mean_reduction_vs_retrained_coarse_at_least']),'worst_not_increased':s['worst_nashconv_bb']<=b['worst_nashconv_bb'],'absolute_maximum':s['worst_nashconv_bb']<=criteria['absolute_max_nashconv_bb']}
 return {'schema':'pokerid-generalization-final-v1','protocol_sha256':sha(PROTOCOL),'selection_file_sha256':sha(selection_path),'source_sha256':identities(),'frozen_preflop_policy_digest':digest,'selected_config':selected,'final_test_used_for_selection':False,'rows':rows,'summaries':summaries,'predeclared_acceptance':flags,'all_predeclared_criteria_pass':all(flags.values()),'sampling_error_bb':0,'numerical_guard_bb':1e-7,'equal_board_weights_are_real_chance':False,'scope':'6predeclared unseen boards only; exact common rich-signal4arm game; not fullNLHE exploitability','external_gto_comparison':'NOT PERFORMED','model_approximation_error_bb':None,'formal_acceptance_complete':0,'frozen_cfr_connected':False,'normal_gto_published':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('select','final'),required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--selection',type=Path);a=p.parse_args();protocol=json.loads(PROTOCOL.read_text())
 if a.phase=='select':r=select(a.build_dir,protocol)
 else:
  if not a.selection:p.error('--selection frozen file required')
  r=final_test(a.build_dir,protocol,json.loads(a.selection.read_text()),a.selection)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({'phase':a.phase,'selected':r['selected_config'],'summary':r.get('summaries',[(x['config']['name'],x['summary']) for x in r.get('candidate_validation',[])])}))
