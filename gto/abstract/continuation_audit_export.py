"""Research-only summary export; cannot create a verified range/certificate."""
import argparse,json
from pathlib import Path

def export(result):
 if result['schema']!='pokerid-continuation-audit-results-v1' or result['normal_gto_admission'] is not False or result['formal_acceptance']!=0:raise ValueError('research-only audit required')
 out={k:v for k,v in result.items() if k not in ('profiles','source_sha256')};traces=[c for x in result['configs'].values() for m in x['models'].values() for c in m['training'] if c['trace']];out['coarse_training_validation']={'count':len(traces),'below_research0_1BB':sum(c['trace'][-1]['restricted_nashconv_bb']<=.1 for c in traces),'not_global_GTO_proof':True};return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);v=p.parse_args()
 if v.output.exists():p.error('fresh output required')
 v.output.write_text(json.dumps(export(json.loads(v.input.read_text())),sort_keys=True,separators=(',',':'))+'\n');print('PASS research-only continuation audit export')
