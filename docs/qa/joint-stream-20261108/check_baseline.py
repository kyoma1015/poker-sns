import json,math
from pathlib import Path
from gto.abstract import model,fullsupport as fs,independent_preflop as ip
r=json.load(open('/workspace/joint-stream-run/frozen-evaluation.json'));old=json.load(open('/workspace/suit-exact-full-results.json'));teacher=json.loads(ip.TEACHER.read_text());p=json.loads(ip.P.read_text());names=[(v,x['leaf_index']) for v in p['variants'] for x in teacher['ranges']];lib=model.load(model.build(Path('/workspace/joint-stream-independent-native')));pay=fs.payoff_planes(old['oracle'],teacher,'learned_small',names);pi=old['complete_preflop_policies']['learned_small'];e=ip.details(lib,pi,pay['point']);ns=model.tree();errors=[]
for row in r['preflop_layout']:
 k=next(i for i,n in enumerate(ns) if n['actor']>=0 and n['history']==row['history']);assert ns[k]['actions']==row['actions'];n=len(row['actions'])
 for h in range(169):
  for a in range(n):errors.append(abs(r['preflop_action_ev_bb'][row['base']+h*n+a]-e['action_ev_chips'][(k*3+a)*169+h]/2))
proof={'scope':'frozen identical profile/all1755orbits: streamed joint conditional chance vs independently saved full class-pair continuation oracle/core evaluation','action_ev_comparisons':len(errors),'max_action_ev_error_bb':max(errors),'profile_sb_ev_error_bb':abs(r['partial_sb_ev_bb']-e['profile_sb_ev_bb']),'preflop_only_nashconv_bb':e['abstract_nashconv_bb'],'joint_fine_information_nashconv_bb':r['restricted_nashconv_interval_bb'],'passed':max(errors)<=1e-8,'external_GTO':False}
assert proof['passed'];Path('/workspace/joint-stream-baseline-independent.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
