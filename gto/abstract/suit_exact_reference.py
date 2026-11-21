"""Reuse lawful-reference comparator; matching inputs NEVER grant GTO admission."""
import argparse,json
from pathlib import Path
from gto.abstract import suit_exact as s,reference_compare as ref
from gto.abstract.range_study import sha

def candidate(data,variant):
 c=data['condition'];expected={'players':2,'stack_bb':50,'blinds_bb':[.5,1],'ante_bb':0,'rake_pct':0,'raise_to_bb':[2.5,9,21,50],'formal_profile':False}
 if any(c.get(k)!=v for k,v in expected.items()) or data.get('source_sha256')!=s.sources():raise ValueError('candidate provenance/conditions differ; no inferred matching')
 m=data['models'][variant]
 return {'condition':ref.target_condition(),'ev_basis':'net_bb_before_blinds','policy_digest':m['policy_digest'],'contexts':m['contexts']}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--input',type=Path,required=True);a.add_argument('--reference',type=Path);a.add_argument('--output',type=Path,required=True);v=a.parse_args()
 if v.output.exists():a.error('fresh output required')
 data=json.loads(v.input.read_text());reports={}
 for name in data['models']:
  ours=candidate(data,name);reports[name]=ref.compare(ours,json.loads(v.reference.read_text())) if v.reference else ref.missing_report()
 result={'models':reports,'reference_acquired':v.reference is not None,'candidate_policy_digests':{k:m['policy_digest'] for k,m in data['models'].items()},'oracle_point_sha256':data['oracle']['point']['sha256'],'ordinary_gto_admission':False,'external_reference_accuracy_verified':False};v.output.write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n');print('PASS reference provenance/condition adapter; acquisition and trust remain separate')
