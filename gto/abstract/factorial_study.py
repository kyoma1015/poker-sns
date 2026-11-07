"""Pre-registered matched-teacher factor study; final cannot fit or select."""
import argparse,json,math
from pathlib import Path
from gto.abstract import continuation_game as base,flop_exact as exact,range_features as feature
from gto.abstract.factorial_game import game,reindex,project,structure_key,mix,information_floor
from gto.abstract.factorial_transfer import Transfer
from gto.abstract.range_study import initialize,mk,sha,summary
from gto.abstract.generalization_features import uniform_strength
ROOT=Path('docs/qa/factorial-generalization-20261104');PROTOCOL=ROOT/'protocol.json'
CELLS=('uniform20','range23','projected_uniform20');STAGES=('vs_3bet','vs_4bet')
SOURCES=('factorial_game.py','factorial_transfer.py','factorial_study.py')

def identities():return {p:sha(Path(__file__).with_name(p)) for p in SOURCES}
def modelkey(stage,seed,cell,method):return ':'.join((stage,str(seed),cell,method))
def dump(p,flop,cat):return [{'key':list(k),'probabilities':list(v),'training_flop':list(flop),'category':cat} for k,v in sorted(p.table.items())]
def choose(candidates,methods):
 rows=[]
 for method in methods:
  u=next(c['summary'] for c in candidates if c['method']==method and c['cell']=='uniform20');r=next(c['summary'] for c in candidates if c['method']==method and c['cell']=='range23')
  rows.append((method,(u['mean_nashconv_bb']+r['mean_nashconv_bb'])/2,r['worst_nashconv_bb']<=u['worst_nashconv_bb']))
 eligible=[r for r in rows if r[2]]
 return min(eligible or rows,key=lambda r:r[1])[0],bool(eligible)
def check_protocol(protocol):
 if protocol!=json.loads(PROTOCOL.read_text()):raise ValueError('preregistration mismatch')
def select(root,protocol):
 check_protocol(protocol);rank,lib,flib,pi,digest=initialize(root);models={modelkey(s,se,c,me):[] for s in STAGES for se in protocol['learning_initialization_seeds'] for c in CELLS for me in protocol['methods']};teacher=[];groups={}
 def store(g,tag,flop,cat,method):
  for seed in protocol['learning_initialization_seeds']:
   rich,rm=base.solve(lib,g,protocol['teacher_iterations'],seed);coarse=reindex(g,lambda k:k[:20]);uniform,um=base.solve(lib,coarse,protocol['teacher_iterations'],seed);projected=project(g,rich,lambda k:k[:20]);ps={'range23':rich,'uniform20':uniform,'projected_uniform20':projected}
   for cell,p in ps.items():models[modelkey(tag,seed,cell,method)].extend(dump(p,flop,cat))
   teacher.append({'stage':tag,'flop':list(flop),'category':cat,'method':method,'seed':seed,'range':rm,'uniform':um,'projected_uniform_evaluated_in_uniform_game':base.evaluate(coarse,projected)})
 for row in protocol['split']['train']:
  m=exact.matrix(rank,row['cards']);uniform=uniform_strength(m)
  for stage in STAGES:
   book=feature.books(flib,m,pi,stage,uniform);g=game(lib,m,pi,stage,book);store(g,stage,row['cards'],row['category'],'global_knn9')
   # Reuse exactly the same per-board teachers for the interpolation factor.
   for seed in protocol['learning_initialization_seeds']:
    for cell in CELLS:
     src=models[modelkey(stage,seed,cell,'global_knn9')];models[modelkey(stage,seed,cell,'board_interpolation3x5')].extend([x for x in src if x['training_flop']==row['cards']])
   groups.setdefault((stage,row['category']),[]).append(reindex(g,structure_key))
 for (stage,cat),gs in groups.items():
  # Public category is visible. Public ranks are deliberately abstracted away.
  store(mix(gs),stage,[0,0,0],cat,'structure_expert_knn9')
 candidates=[{'method':me,'cell':c,'validation':[]} for me in protocol['methods'] for c in CELLS];geometry={};policies={k:Transfer(v,k.split(':')[-1],k.split(':')[-2]=='range23',geometry) for k,v in models.items()}
 for row in protocol['split']['validation']:
  m=exact.matrix(rank,row['cards']);uniform=uniform_strength(m)
  for stage in STAGES:
   g=game(lib,m,pi,stage,feature.books(flib,m,pi,stage,uniform))
   for seed in protocol['learning_initialization_seeds']:
    for c in candidates:
     p=policies[modelkey(stage,seed,c['cell'],c['method'])].materialize(g);c['validation'].append({'flop':row['cards'],'category':row['category'],'stage':stage,'seed':seed,'metrics':base.evaluate(g,p)})
 for c in candidates:c['summary']=summary(c['validation'])
 winner,eligible=choose(candidates,protocol['methods'])
 return {'protocol_sha256':sha(PROTOCOL),'source_sha256':identities(),'frozen_preflop_policy_digest':digest,'accessed_splits':['train','validation'],'selected_shared_method':winner,'validation_worst_constraint_satisfied':eligible,'candidate_validation':candidates,'models':models,'teacher_metrics':teacher,'sampling_error_bb':0,'equal_board_weights_are_real_chance':False}

def validate(selection):
 if selection['protocol_sha256']!=sha(PROTOCOL) or selection['source_sha256']!=identities() or selection['accessed_splits']!=['train','validation']:raise ValueError('selection identity or phase mismatch')
def final(root,protocol,selection,path):
 check_protocol(protocol);validate(selection);lock=json.loads((ROOT/'selection-lock.json').read_text())
 if sha(path)!=lock['selection_sha256']:raise ValueError('selection bytes changed after lock')
 rank,lib,flib,pi,digest=initialize(root)
 if digest!=selection['frozen_preflop_policy_digest']:raise ValueError('frozen preflop policy changed')
 me=selection['selected_shared_method'];geometry={};policies={(s,se,c):Transfer(selection['models'][modelkey(s,se,c,me)],me,c=='range23',geometry) for s in STAGES for se in protocol['learning_initialization_seeds'] for c in CELLS};old=json.loads(Path('docs/qa/range-generalization-20261101/selection.json').read_text());og=feature.Neighbors([old['selected_range']]);oldpol={k:feature.RangePolicy(v['records'],old['selected_range'],og) for k,v in old['models'].items()};rows=[]
 for row in protocol['split']['final_test']:
  m=exact.matrix(rank,row['cards']);uniform=uniform_strength(m)
  for s in STAGES:
   g=game(lib,m,pi,s,feature.books(flib,m,pi,s,uniform))
   for se in protocol['learning_initialization_seeds']:
    ps={c:policies[(s,se,c)].materialize(g) for c in CELLS};ps['previous_frozen_range']=oldpol[mk(s,se)].materialize(g)
    for c,p in ps.items():rows.append({'flop':row['cards'],'category':row['category'],'stage':s,'seed':se,'cell':c,'metrics':base.evaluate(g,p)})
 summaries={c:summary([r for r in rows if r['cell']==c]) for c in (*CELLS,'previous_frozen_range')};r,u=summaries['range23'],summaries['uniform20'];criteria={'mean_reduction':r['mean_nashconv_bb']<=.8*u['mean_nashconv_bb'],'worst_not_increased':r['worst_nashconv_bb']<=u['worst_nashconv_bb'],'absolute_maximum':r['worst_nashconv_bb']<=.1}
 return {'protocol_sha256':sha(PROTOCOL),'selection_sha256':sha(path),'source_sha256':identities(),'selected_shared_method':me,'rows':rows,'summaries':summaries,'criteria':criteria,'all_criteria_pass':all(criteria.values()),'model_updated':False,'selection_performed':False,'sampling_error_bb':0,'numerical_guard_bb':1e-7,'equal_board_weights_are_real_chance':False,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN','formal_acceptance_complete':0,'original_cfr_connected':False}

def diagnose(root,protocol,selection):
 check_protocol(protocol);validate(selection)
 if not (ROOT/'final-results.json').exists():raise ValueError('diagnostics only AFTER locked final evaluation')
 rank,lib,flib,pi,_=initialize(root);cases=[(split,next(r['cards'] for r in protocol['split'][split] if r['category']=='paired_rainbow_high')) for split in ('validation','final_test')]+[('known_anchor',[27,44,45])];rows=[]
 for split,flop in cases:
  m=exact.matrix(rank,flop);uniform=uniform_strength(m)
  for stage in STAGES:
   book=feature.books(flib,m,pi,stage,uniform);g=game(lib,m,pi,stage,book);_,oracle=base.solve(lib,g,protocol['diagnostic_iterations'],17)
   for coarse,rich in protocol['diagnostic_reference_pairs']:
    rc=game(lib,m,pi,stage,book,rich,coarse);cr=game(lib,m,pi,stage,book,coarse,rich);bounds=information_floor(lib,rc,cr,protocol['diagnostic_iterations'],17);rows.append({'split':split,'flop':flop,'stage':stage,'coarse_information':coarse,'rich_reference':rich,'coarse_range_game_oracle':oracle,'bounds':bounds})
 return {'rows':rows,'diagnostic_only':True,'candidate_updated':False,'oracle_not_a_transfer_policy':True,'sampling_error_bb':0,'numerical_guard_bb':1e-7,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN','formal_acceptance_complete':0}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('select','final','diagnose'),required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--selection',type=Path,default=ROOT/'selection.json');p.add_argument('--output',type=Path,required=True);a=p.parse_args();protocol=json.loads(PROTOCOL.read_text())
 if a.phase=='select':out=select(a.build_dir,protocol)
 else:
  sel=json.loads(a.selection.read_text());out=final(a.build_dir,protocol,sel,a.selection) if a.phase=='final' else diagnose(a.build_dir,protocol,sel)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({'phase':a.phase,'method':out.get('selected_shared_method'),'summaries':out.get('summaries'),'rows':len(out.get('rows',[]))}))
