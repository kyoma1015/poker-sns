"""Research-only summary export; cannot create a verified range/certificate."""
import argparse,json
from pathlib import Path

def export(result):
 if result['schema']!='pokerid-continuation-audit-results-v1' or result['normal_gto_admission'] is not False or result['formal_acceptance']!=0:raise ValueError('research-only audit required')
 out={k:v for k,v in result.items() if k not in ('profiles','source_sha256')};traces=[c for x in result['configs'].values() for m in x['models'].values() for c in m['training'] if c['trace']];out['coarse_training_validation']={'count':len(traces),'below_research0_1BB':sum(c['trace'][-1]['restricted_nashconv_bb']<=.1 for c in traces),'not_global_GTO_proof':True};out['counterfactual_preflop_oracle']=False;out['posterior_conditioned_on_call']=True;out['constructed_root_continuation_gains']={}
 for variant in ('learned_small','learned_large'):
  name='fixed_'+variant.split('_')[-1];seats={str(s):sum(result['configs'][variant+'|'+stage]['models'][name]['by_seat'][str(s)]['board_class_flags']['gain_root_bb'] for stage in ('vs_3bet','vs_4bet')) for s in (0,1)};out['constructed_root_continuation_gains'][variant]={'by_seat_bb':seats,'sum_bb':sum(seats.values()),'scope':'feasible own/private/public flop responses at2disjointCALLbranches with preflop unchanged;lower bound on profile deviation in containing game,NOT GTO upperbound'}
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);v=p.parse_args()
 if v.output.exists():p.error('fresh output required')
 v.output.write_text(json.dumps(export(json.loads(v.input.read_text())),sort_keys=True,separators=(',',':'))+'\n');print('PASS research-only continuation audit export')
