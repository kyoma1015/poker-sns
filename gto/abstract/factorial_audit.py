"""Readonly error attribution AFTER model freeze; no training or selection."""
import argparse,json,math
from pathlib import Path
from gto.abstract import factorial_study as fs,continuation_game as base,flop_exact as exact,range_features as feature
from gto.abstract.factorial_game import game
from gto.abstract.factorial_transfer import Transfer,category
from gto.abstract.generalization_features import uniform_strength


def deviations(g,policy):
 p,q=base.strategies(g,policy);a=g['tensor'];nh,nv=len(p),len(q);rows=[]
 for side in ('hero','villain'):
  keys=g['hkeys'] if side=='hero' else g['vkeys'];probs=p if side=='hero' else q
  for i,k in enumerate(keys):
   if side=='hero':
    mass=math.fsum(g['chance_mass'][i*nv+j] for j in range(nv));ev=[math.fsum(a[i][j][x][y]*q[j][y] for j in range(nv) for y in range(4)) for x in range(4)]
   else:
    mass=math.fsum(g['chance_mass'][j*nv+i] for j in range(nh));ev=[-math.fsum(a[j][i][x][y]*p[j][x] for j in range(nh) for x in range(4)) for y in range(4)]
   value=math.fsum(v*w for v,w in zip(ev,probs[i]));gain=max(ev)-value
   rows.append({'side':side,'own_signal':list(k),'own_marginal_mass':mass,'complete_plan_probabilities':list(probs[i]),'conditional_arm_ev_bb':[v/mass for v in ev] if mass>0 else None,'joint_deviation_gain_bb':max(0.,gain),'best_response_arm':max(range(4),key=lambda j:ev[j])})
 return {'total_deviation_bb':math.fsum(r['joint_deviation_gain_bb'] for r in rows),'largest_own_type_contributions':sorted(rows,key=lambda r:r['joint_deviation_gain_bb'],reverse=True)[:12]}


def audit(root):
 selection=json.loads((fs.ROOT/'selection.json').read_text());fs.validate(selection);final=json.loads((fs.ROOT/'final-results.json').read_text());protocol=json.loads(fs.PROTOCOL.read_text());rank,lib,flib,pi,_=fs.initialize(root);me=selection['selected_shared_method'];geo={};policies={(s,se,c):Transfer(selection['models'][fs.modelkey(s,se,c,me)],me,c=='range23',geo) for s in fs.STAGES for se in protocol['learning_initialization_seeds'] for c in ('uniform20','range23')};old=json.loads(Path('docs/qa/range-generalization-20261101/selection.json').read_text());og=feature.Neighbors([old['selected_range']]);oldp={k:feature.RangePolicy(v['records'],old['selected_range'],og) for k,v in old['models'].items()};worst=max((r for r in final['rows'] if r['cell']=='range23'),key=lambda r:r['metrics']['restricted_nashconv_bb']);cases=[('known_anchor',[27,44,45]),('posthoc_error_diagnostic_not_new_unseen',worst['flop'])];out=[]
 for role,flop in cases:
  m=exact.matrix(rank,flop);uniform=uniform_strength(m)
  for s in fs.STAGES:
   g=game(lib,m,pi,s,feature.books(flib,m,pi,s,uniform))
   for se in protocol['learning_initialization_seeds']:
    ps={c:policies[(s,se,c)].materialize(g) for c in ('uniform20','range23')};ps['previous_frozen_range']=oldp[fs.mk(s,se)].materialize(g)
    for c,p in ps.items():
     metrics=base.evaluate(g,p);d=deviations(g,p)
     if not math.isclose(d['total_deviation_bb'],metrics['restricted_nashconv_bb'],abs_tol=1e-12):raise ValueError('deviation attribution failed conservation')
     out.append({'role':role,'flop':flop,'category':category(flop),'stage':s,'seed':se,'cell':c,'metrics':metrics,'attribution':d})
 return {'rows':out,'selection_sha256':fs.sha(fs.ROOT/'selection.json'),'audit_source_sha256':fs.sha(__file__),'candidate_updated':False,'posthoc_error_analysis_used_for_selection':False,'sampling_error_bb':0,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=audit(a.build_dir);a.output.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({'rows':len(r['rows']),'candidate_updated':False}))
