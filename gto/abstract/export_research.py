"""Export inspected abstract-model results to a separate opt-in research UI."""
import hashlib,json,math
from pathlib import Path
from gto.hand169 import CLASSES

def export(evidence):
 if evidence['full_game_gto_verified'] or evidence['formal_acceptance_complete']!=0:raise ValueError('abstract results cannot promote formal GTO')
 comparisons=[]
 for comparison in evidence['independent_seed_comparison']:
  mode= comparison['mode'];stage=comparison['stage']
  a,b=[r['ranges'][stage]['hands'] for r in evidence['runs'] if r['mode']==mode][:2]
  total=sum((a[h]['reach_mass']+b[h]['reach_mass'])/2 for h in a)
  weighted=sum((a[h]['reach_mass']+b[h]['reach_mass'])/2*sum(abs(x-y) for x,y in zip(a[h]['frequencies'],b[h]['frequencies']))/2 for h in a)/total
  comparisons.append({**comparison,'reach_weighted_total_variation':weighted})
 selected=[r for r in evidence['runs'] if r['seed']==evidence['seeds'][0]]
 models={}
 for run in selected:
  if not 0<=run['abstract_nashconv_bb']<=.01 or not run['same_input_replay']:raise ValueError('abstract model convergence/replay gate not satisfied')
  contexts={stage:run['ranges'][stage] for stage in ('rfi','vs_open','vs_3bet','vs_4bet')}
  for context in contexts.values():
   if set(context['hands'])!=set(CLASSES) or context['coverage']!=169:raise ValueError('research class coverage differs')
   for row in context['hands'].values():
    if not math.isclose(sum(row['frequencies']),1,abs_tol=1e-10) or any(not math.isfinite(x) or x<0 for x in row['frequencies']):raise ValueError('invalid research strategy')
    if any(not math.isfinite(x) for x in [row['ev_bb'],*row['action_ev_bb'],*row['model_ev_interval_bb']]):raise ValueError('invalid research EV')
  models[run['mode']]={'abstract_nashconv_bb':run['abstract_nashconv_bb'],'policy_digest':run['policy_digest'],
    'profile_sb_ev_bb':run['profile_sb_ev_bb'],'model_payoff_error_bound_bb':run['simultaneous_payoff_error_bound_bb'],
    'heldout':next(x for x in evidence['fixed_policy_independent_validation'] if x['mode']==run['mode']),
    'contexts':contexts}
 result={'schema':'pokerid-research-preflop-abstraction-v1','full_game_gto_verified':False,
  'condition':evidence['condition'],'training_seed':evidence['seeds'][0],
  'method_source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('model.py','study.py','export_research.py')},
  'source_sha256':evidence['source']['source_sha256'],'rank_source_sha256':evidence['source']['rank_source_sha256'],
  'samples_per_class_pair':selected[0]['samples_per_class_pair'],'iterations':selected[0]['iterations'],
  'reference_solution_comparison':'UNPERFORMED','real_game_error_bound_bb':None,'models':models,
  'independent_seed_comparison':comparisons,'continuation_model_sensitivity':evidence['continuation_model_sensitivity']}
 return result

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();a.output.write_text(json.dumps(export(json.loads(a.evidence.read_text())),sort_keys=True,separators=(',',':'))+'\n')
