import json,random
import numpy as np
from gto.qualification.integrated_audit import make,layout,ROOT
from gto.qualification import integrated_br as br,public_chance_solver as pcs
q,_,r=make(17120101,True);nodes,obs=layout(r);rng=random.Random(17138101);boards=[rng.sample(range(52),5) for _ in range(2)];rows,proj=br.snapshot(q,nodes,obs,boards);lookup={};error=0.;example=None
for b,board in enumerate(boards):
 block=pcs.block(q.ranklib,board)
 for k,n in enumerate(nodes):
  if n['actor']<0:continue
  round=n['round'];codes=np.array(block['codes'])>>(3-round);group=block['public']>>(3-round)
  for h,c in enumerate(codes):
   key=(k,group,int(c));p=rows[b][k]['pi'][h]
   if key in lookup:
    d=float(np.max(abs(p-lookup[key])))
    if d>error:error=d;example=dict(node=k,round=round,code=int(c),old=lookup[key].tolist(),new=p.tolist())
   lookup[key]=p
out=dict(max_within_legacy_info_policy_difference=error,example=example,initial_new_abstract_BR=br.measure(q.ranklib,nodes,boards,rows),boards=boards);print(json.dumps(out));(ROOT/'mapping-audit.json').write_text(json.dumps(out,indent=2)+'\n')
