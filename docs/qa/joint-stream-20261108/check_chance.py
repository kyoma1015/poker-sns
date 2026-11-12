import json,math,time
from pathlib import Path
from gto.abstract import joint_stream_cache as c,model,fullsupport as fs,independent_preflop as ip
start=time.monotonic();mass=[0.]*(169*169);eq=[0.]*(169*169)
for row in c.population():
 obj,values=c.read('/workspace/joint-stream-cache',row);codes=obj['codes'];T=len(codes);weight=row['multiplicity']/22100
 for i,a in enumerate(codes):
  for j,b in enumerate(codes):
   k=(a//8)*169+b//8;x=(i*T+j)*2;mass[k]+=weight*values[x];eq[k]+=weight*values[x+1]
counts,expected=model.chance(model.classes());chance_error=max(abs(a-b) for a,b in zip(mass,expected));full=json.load(open('/workspace/suit-exact-full-results.json'));teacher=json.loads(ip.TEACHER.read_text());p=json.loads(ip.P.read_text());names=[(v,r['leaf_index']) for v in p['variants'] for r in teacher['ranges']];leaf=next(k for k,n in enumerate(model.tree()) if n['actor']<0 and n.get('matched') and n['value']==100);offset=names.index(('learned_small',leaf))*169*169;point=fs.unpack(full['oracle']['point']);error=max(abs((-50+100*e/m)-point[offset+k]) for k,(e,m) in enumerate(zip(eq,mass)))
out={'orbits':1755,'physical_flops':22100,'class_pair_cells':169*169,'maximum_joint_class_chance_error':chance_error,'maximum_allin_ev_vs_prior_independent_classpair_oracle_bb':error,'chance_total':math.fsum(mass),'unconditional_sb_equity':math.fsum(eq),'passed':chance_error<=1e-10 and error<=1e-8,'elapsed_seconds':time.monotonic()-start,'scope':'exact board/card-removal/allin numerical consistency;not externalGTO or model-omission validation'}
assert out['passed'];Path('/workspace/joint-stream-chance-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
