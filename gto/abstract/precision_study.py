"""Reuse immutable inputs; integrate, enumerate and compare without retraining."""
import argparse,ctypes as C,gzip,hashlib,json,math,time
from pathlib import Path
from gto.abstract.precision_archive import unpack
from gto.abstract.precision_runouts import build,exact_cells,rao_blackwell,refinement_targets
from gto.abstract.precision import evaluate,STAGES
from gto.abstract.model import tree


def summarize(models):
 return {mode:{stage:{'profile_max_radius_bb':max(r['profile']['radius_bb'] for r in c['hands'].values()),
   'action_max_radius_bb':max(a['radius_bb'] for r in c['hands'].values() for a in r['actions']),
   'exact_profiles':sum(r['profile']['radius_bb']==0 for r in c['hands'].values()),
   'exact_actions':sum(a['radius_bb']==0 for r in c['hands'].values() for a in r['actions'])}
  for stage,c in m['contexts'].items()} for mode,m in models.items()}

def run(inputs,output,reference_lib=None):
 packet=json.loads(Path(inputs).read_text());old,policies=unpack(packet);output=Path(output);output.mkdir(parents=True,exist_ok=False)
 baseline={mode:evaluate(p,old,mode,failure=.0025) for mode,p in policies.items()};lib=build(output/'build')
 from gto.abstract.continuation_exact import build as controller_build,refine
 exact=refine(exact_cells(lib,opponent_classes=refinement_targets(policies)),policies,controller_build(output/'controller-build'));(output/'exact-cells.json').write_text(json.dumps(exact,sort_keys=True)+'\n')
 print('PRECISION_EXACT '+json.dumps({k:exact[k] for k in ('concrete_matchups_enumerated','boards_per_matchup','seconds','targets')}),flush=True)
 rb=rao_blackwell(lib,exact,samples=old['samples_per_class_pair'],seed=old['seed'])
 with gzip.open(output/'rb-kernel.json.gz','wt') as f:json.dump(rb,f,sort_keys=True)
 manifest=json.loads((output/'build/precision-manifest.json').read_text())
 return assemble(inputs,output,packet,old,policies,exact,rb,manifest,baseline,reference_lib)

def assemble(inputs,output,packet,old,policies,exact,rb,manifest,baseline=None,reference_lib=None):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 if baseline is None:baseline={mode:evaluate(p,old,mode,failure=.0025) for mode,p in policies.items()}
 improved={mode:evaluate(p,rb,mode,failure=.0025) for mode,p in policies.items()}
 from gto.abstract.precision_game_bounds import evaluate as game_bounds
 bounds={mode:game_bounds(p,rb,mode) for mode,p in policies.items()}
 checked,diagnostics=verify_points(reference_lib,policies,rb,improved,output)
 for mode,b in bounds.items():
  if not math.isclose(b['nashconv_point_bb'],diagnostics[mode]['nashconv_on_refined_table_bb'],abs_tol=1e-10):raise ValueError('independent global best response differs')
 from gto.abstract.model import chance,classes
 _,mass=chance(classes());size=169*169
 variance_comparison=[]
 for plane in range(5):
  before=math.fsum(p*v for p,v in zip(mass,old["variance"][plane*size:(plane+1)*size]));after=math.fsum(p*v for p,v in zip(mass,rb["variance"][plane*size:(plane+1)*size]))
  variance_comparison.append({"plane":plane,"original_weighted_variance":before,"conditional_weighted_variance":after,"observed_ratio":after/before if before else None})
 result={'expected_controller_game_bounds':bounds,'variance_comparison':variance_comparison,'refined_table_diagnostics':diagnostics,'independent_native_action_ev_checks':checked,'schema':'pokerid-ev-precision-study-v1','confidence':.99,'source':manifest,
  'inputs_sha256':hashlib.sha256(Path(inputs).read_bytes()).hexdigest(),'fixed_policy_digests':{m:p['policy_digest'] for m,p in packet['policies'].items()},
  'validation_seed':old['seed'],'samples_per_class_pair':old['samples_per_class_pair'],'cfr_iterations_added':0,
  'baseline_summary':summarize(baseline),'improved_summary':summarize(improved),'models':improved,
  'exact_cells':{'concrete_matchups_enumerated':exact['concrete_matchups_enumerated'],'boards_per_matchup':exact['boards_per_matchup'],
    'exact_plane_entries':sum(exact['mask']),'exact_showdown_cells':sum(exact['mask'][:169*169]),'targets':exact['targets'],'class_records':len(exact['records']),'seconds':exact['seconds']},
  'controller_enumeration':{'class_pairs':len(exact.get('controller_records',[])),'concrete_matchups':exact.get('controller_concrete_matchups',0),'method':exact.get('controller_method'),'ablation':exact.get('controller_records',[])},
  'rb_seconds':rb['seconds'],'reference_solution_comparison':'UNPERFORMED','reference_difference':None,
  'real_game_approximation_error':None,'full_game_gto_verified':False,'formal_acceptance_complete':0,
  'scope':'99% simultaneous conditional fixed-policy model EV intervals; opponent/action integration exact in finite model, floating arithmetic; board/holes sampling remains outside exact cells'}
 (output/'evidence.json').write_text(json.dumps(result,sort_keys=True)+'\n')
 print('PRECISION_SUMMARY '+json.dumps({k:v for k,v in result.items() if k not in ('models','source')},sort_keys=True),flush=True)
 return result

def export(result):
 models={}
 for mode,m in result['models'].items():
  contexts={}
  for stage,c in m['contexts'].items():
   contexts[stage]={'hands':{h:{'ev_bb':r['profile']['ev_bb'],'interval_bb':r['profile']['interval_bb'],
     'radius_bb':r['profile']['radius_bb'],'method':r['profile']['method'],
     'action_ev_bb':[a['ev_bb'] for a in r['actions']],'action_intervals_bb':[a['interval_bb'] for a in r['actions']],
     'action_exact':[a['radius_bb']==0 for a in r['actions']]}
      for h,r in c['hands'].items()},'actor':c['actor'],'actions':c['actions']}
  models[mode]={'contexts':contexts}
 return {'schema':'pokerid-research-conditional-ev-v1','models':models,'confidence':result['confidence'],
  'expected_controller_game_bounds':result['expected_controller_game_bounds'],'fixed_policy_digests':result['fixed_policy_digests'],'inputs_sha256':result['inputs_sha256'],
  'validation_seed':result['validation_seed'],'samples_per_class_pair':result['samples_per_class_pair'],
  'exact_cells':{k:v for k,v in result['exact_cells'].items() if k!='seconds'},'improved_summary':result['improved_summary'],
  'method_source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('continuation_exact.cc','continuation_exact.py','precision_game_bounds.py','precision.py','precision_archive.py','precision_runouts.py','precision_native.cc','precision_study.py')},
  'real_game_approximation_error':None,'reference_solution_comparison':'UNPERFORMED','reference_difference':None,'full_game_gto_verified':False}

def verify_points(reference_lib,policies,kernel,report,output):
 from gto.abstract.model import build as reference_build,load,ints,doubles,payoffs,classes,chance
 from gto.hand169 import CLASSES
 lib=load(reference_lib or reference_build(Path(output)/'reference-build'));nodes=tree();_,p=chance(classes());n=169;m=len(nodes);checked=0;diagnostics={}
 for mode,policy in policies.items():
  ev=(C.c_double*(m*3*n))();reach=(C.c_double*(m*n))();metrics=(C.c_double*4)()
  lib.abstract_evaluate(n,m,ints([x['actor'] for x in nodes]),ints([len(x['actions']) for x in nodes]),ints([c for x in nodes for c in (x['children']+[-1]*3)[:3]]),doubles(p),doubles(payoffs(kernel,mode,nodes)),doubles(policy),ev,reach,metrics)
  diagnostics[mode]={'profile_sb_ev_bb':metrics[0]/2,'nashconv_on_refined_table_bb':metrics[3]/2,'expected_game_convergence_verified':False}
  for v,node in enumerate(nodes):
   if node['actor']<0 or 'call' in node['history'] or node['raises']>=4:continue
   for h,label in enumerate(CLASSES):
    for a,value in enumerate(report[mode]['contexts'][STAGES[node['raises']]]['hands'][label]['actions']):
     if not math.isclose(value['ev_bb'],ev[(v*3+a)*n+h]/2,rel_tol=0,abs_tol=1e-10):raise ValueError('independent conditional EV aggregation differs')
     checked+=1
 return checked,diagnostics

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path);p.add_argument('--output',type=Path);p.add_argument('--reference-lib',type=Path);p.add_argument('--export-evidence',type=Path);p.add_argument('--export-output',type=Path);a=p.parse_args()
 if a.export_evidence:a.export_output.write_text(json.dumps(export(json.loads(a.export_evidence.read_text())),sort_keys=True,separators=(',',':'))+'\n')
 else:run(a.inputs,a.output,a.reference_lib)
