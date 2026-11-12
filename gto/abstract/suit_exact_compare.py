"""Hold previous policies and continuation game fixed while removing oracle noise."""
import argparse,json,math
from pathlib import Path
from gto.abstract import suit_exact as s,fullsupport as fs,independent_preflop as old,model,root_interval as ri
from gto.abstract.suit_exact_br import evaluate
from gto.abstract.range_study import sha

def compare(full,root):
 baseline=json.loads((s.ROOT/'sampled-policy-baseline.json').read_text());prior=json.loads((old.ROOT/'results.json').read_text());protocol=json.loads((s.ROOT/'comparison-protocol.json').read_text());assert fs.digest(baseline['policies'])==protocol['baseline_digest']==prior['policy_frozen_before_evaluation_digest'];assert full['teacher_sha256']==prior['teacher_sha256'];lib=model.load(model.build(root));teacher=json.loads(old.TEACHER.read_text());names=[(name,r['leaf_index']) for name in json.loads(old.P.read_text())['variants'] for r in teacher['ranges']];prob=model.chance(model.classes())[1];out={}
 for name,pi in baseline['policies'].items():
  payoff=fs.payoff_planes(full['oracle'],teacher,name,names);native=old.details(lib,pi,payoff['point']);independent=evaluate(model.tree(),pi,prob,payoff['point']);error=max(abs(native[k]-independent[k]) for k in independent)
  if error>1e-9:raise ValueError('baseline independent BR mismatch')
  interval=ri.evaluate(lib,model.tree(),pi,prob,payoff['lower'],payoff['upper'],169)
  for k,v in interval.items():
   if isinstance(v,list):interval[k]=[x/2 for x in v]
  oldbounds=prior['models'][name]['root_expected_game_bounds_bb'];out[name]={'same_policy_digest':fs.digest(pi),'previous_MC_expected_game_bounds_bb':oldbounds,'enumerated_same_policy_bounds_bb':interval,'enumerated_same_policy_point':independent,'maximum_native_python_difference_bb':error,'new_exact_trained_policy_nashconv_bb':full['models'][name]['root_expected_game_bounds_bb']['preflop_nashconv_interval'],'interpretation':'MCvsenumerated comparison holds policy and continuation MODEL fixed; new-training effect reported separately;NOT externalGTO validation'}
 sensitivity={}
 variants=list(full['models'])
 for stage in ('rfi','vs_open','vs_3bet','vs_4bet'):
  a,b=[full['models'][name]['contexts'][stage]['hands'] for name in variants]
  sensitivity[stage]={'mean_hand_frequency_TV':math.fsum(math.fsum(abs(x-y) for x,y in zip(a[h]['frequencies'],b[h]['frequencies']))/2 for h in model.CLASSES)/169,'max_action_ev_difference_bb':max(abs(x-y) for h in model.CLASSES for x,y in zip(a[h]['action_ev_bb'],b[h]['action_ev_bb'])),'interpretation':'two fixed size-model sensitivity,NOT error against externalGTO'}
 return {'size_sensitivity':sensitivity,'baseline_digest':protocol['baseline_digest'],'teacher_sha256':sha(old.TEACHER),'comparison_protocol_sha256':sha(s.ROOT/'comparison-protocol.json'),'models':out,'selection_performed':False,'real_game_approximation_error':'UNKNOWN','external_gto_comparison':'NOT PERFORMED'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True);v=p.parse_args()
 if v.output.exists():p.error('fresh output required')
 result=compare(json.loads(v.input.read_text()),v.build_dir);v.output.write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n');print('PASS same-policy noise and independent BR comparison')
