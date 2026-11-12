"""Descriptive external-reference comparison, NEVER a GTO admission gate.

No interpolation of stack/sizing/rake, no action padding, no invented EVs.
Condition agreement and reference quality are separate. Even exact input matches
and small distances do not establish exploitability or real-game accuracy.
"""
import argparse,hashlib,json,math
from pathlib import Path
from gto.hand169 import CLASSES
from gto.abstract.model import tree
from gto.abstract.precision import STAGES


def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def target_condition():
 return {'game':'NLHE','players':2,'stacks_bb':[50.,50.],'blinds_bb':[.5,1.],
  'antes_bb':[0.,0.],'rake_rate':0.,'rake_cap_bb':0.,'utility':'chipEV','equilibrium_concept':'Nash',
  'preflop_tree_sha256':digest(tree())}


def condition_differences(condition):
 def invalid(x):
  return type(x) is bool or (isinstance(x,float) and not math.isfinite(x)) or (isinstance(x,list) and any(invalid(v) for v in x))
 differences=[]
 for key,expected in target_condition().items():
  actual=condition.get(key)
  if actual is None:differences.append({'field':key,'status':'UNKNOWN','expected':expected})
  elif invalid(actual) or actual!=expected:differences.append({'field':key,'status':'DIFFERENT','expected':expected,'actual':actual})
 return differences


def validate_context(context):
 actions=context['actions'];hands=context['hands']
 if not actions or len(set(actions))!=len(actions) or any(not isinstance(a,str) for a in actions):raise ValueError('unique labelled actions required')
 if context['actor'] not in (0,1) or type(context['actor']) is bool:raise ValueError('explicit actor required')
 if set(hands)-set(CLASSES):raise ValueError('unknown hand class')
 for row in hands.values():
  f=row['frequencies']
  if len(f)!=len(actions) or any(type(x) not in (int,float) or not math.isfinite(x) or not 0<=x<=1 for x in f) or not math.isclose(math.fsum(f),1.,rel_tol=0,abs_tol=1e-10):raise ValueError('complete normalized frequencies required')
  for key in ('ev_bb','reach_mass'):
   x=row.get(key)
   if x is not None and (type(x) not in (int,float) or not math.isfinite(x) or (key=='reach_mass' and x<0)):raise ValueError('finite explicit EV/reach required')
  if 'action_ev_bb' in row:
   ev=row['action_ev_bb']
   if len(ev)!=len(actions) or any(type(x) not in (int,float) or not math.isfinite(x) for x in ev):raise ValueError('finite action EV vector required')
   if row.get('ev_bb') is not None and not math.isclose(math.fsum(p*q for p,q in zip(f,ev)),row['ev_bb'],rel_tol=0,abs_tol=1e-8):raise ValueError('profile EV differs from weighted action EV')


def compare(ours,reference):
 if condition_differences(ours.get('condition',{})):raise ValueError('candidate must match pinned target condition')
 if ours.get('ev_basis')!='net_bb_before_blinds':raise ValueError('candidate EV basis differs')
 if reference.get('schema')!='pokerid-external-preflop-reference-v1':raise ValueError('reference schema required')
 source=reference.get('source',{})
 if not source.get('url','').startswith('https://') or not source.get('solver') or not source.get('retrieved_at') or not source.get('usage_permission'):raise ValueError('traceable lawful provenance required')
 if reference.get('ev_basis')!='net_bb_before_blinds':raise ValueError('EV basis must be explicitly normalized before comparison')
 differences=condition_differences(reference.get('condition',{}));contexts={};total_frequency=total_ev=0
 for stage in STAGES:
  a=ours['contexts'][stage];b=reference.get('contexts',{}).get(stage)
  validate_context(a)
  if b is None:contexts[stage]={'status':'MISSING','frequency_rows':0,'ev_rows':0};continue
  validate_context(b)
  if a['actor']!=b['actor'] or a['history']!=b.get('history') or set(a['actions'])!=set(b['actions']):
   contexts[stage]={'status':'INCOMPATIBLE_HISTORY_ACTOR_OR_ACTIONS','frequency_rows':0,'ev_rows':0};continue
  order=[b['actions'].index(x) for x in a['actions']];rows={}
  for h in CLASSES:
   if h not in a['hands'] or h not in b['hands']:continue
   x=a['hands'][h];y=b['hands'][h];delta=[x['frequencies'][i]-y['frequencies'][j] for i,j in enumerate(order)]
   ev=x['ev_bb']-y['ev_bb'] if x.get('ev_bb') is not None and y.get('ev_bb') is not None else None
   q=[x['action_ev_bb'][i]-y['action_ev_bb'][j] for i,j in enumerate(order)] if 'action_ev_bb' in x and 'action_ev_bb' in y else None
   rows[h]={'partition':'audit_holdout' if int(hashlib.sha256(('pokerid-reference-split-v1:'+stage+':'+h).encode()).hexdigest(),16)%5==0 else 'calibration','frequency_difference':delta,'total_variation':math.fsum(map(abs,delta))/2,'ev_difference_bb':ev,'action_ev_difference_bb':q,'reference_reach_mass':y.get('reach_mass')}
  combo=lambda h:6 if len(h)==2 else 4 if h.endswith('s') else 12
  mass=math.fsum(combo(h) for h in rows);reach_complete=all(r['reference_reach_mass'] is not None for r in rows.values())
  reach=math.fsum(r['reference_reach_mass'] for r in rows.values()) if reach_complete else 0
  evs=[r['ev_difference_bb'] for r in rows.values() if r['ev_difference_bb'] is not None]
  contexts[stage]={'status':'COMPARED_DESCRIPTIVELY','frequency_rows':len(rows),'ev_rows':len(evs),'hands':rows,
   'combo_weighted_tv':math.fsum(combo(h)*r['total_variation'] for h,r in rows.items())/mass if mass else None,
   'reference_reach_weighted_tv':math.fsum(r['reference_reach_mass']*r['total_variation'] for r in rows.values())/reach if reach else None,
   'partition_tv':{part:math.fsum(combo(h)*r['total_variation'] for h,r in rows.items() if r['partition']==part)/math.fsum(combo(h) for h,r in rows.items() if r['partition']==part) if any(r['partition']==part for r in rows.values()) else None for part in ('audit_holdout','calibration')},
   'max_frequency_difference':max((abs(d) for r in rows.values() for d in r['frequency_difference']),default=None),
   'max_abs_ev_difference_bb':max(map(abs,evs),default=None)}
  total_frequency+=len(rows);total_ev+=len(evs)
 return {'schema':'pokerid-reference-comparison-v1','status':'INPUT_MATCH_DESCRIPTIVE_ONLY' if not differences else 'REFERENCE_ONLY_CONDITION_MISMATCH',
  'condition_differences':differences,'source':source,'reference_sha256':digest(reference),'candidate_sha256':digest(ours),
  'frequency_rows':total_frequency,'ev_rows':total_ev,'expected_rows':4*169,'contexts':contexts,
  'reference_accuracy_verified':False,'real_game_approximation_error':None,'full_game_gto_verified':False,
  'scope':'Distances between strategy profiles; EV differences are descriptive, NOT deviation gains. Input match is not external solver accuracy validation. Missing EVs are not zero. Deterministic predeclared hand/history partitions are descriptive holdouts, not independent-sample confidence intervals; freeze model before auditing holdout.'}


def candidate(mode,root=Path('.')):
 old=json.loads((root/'src/gto/abstractResearchData.json').read_text())['models'][mode]
 new=json.loads((root/'src/gto/precisionResearchData.json').read_text())['models'][mode]
 contexts={}
 for stage,c in old['contexts'].items():
  contexts[stage]={**c,'hands':{h:{**r,'ev_bb':new['contexts'][stage]['hands'][h]['ev_bb'],
   'action_ev_bb':new['contexts'][stage]['hands'][h]['action_ev_bb']} for h,r in c['hands'].items()}}
 return {'condition':target_condition(),'ev_basis':'net_bb_before_blinds','policy_digest':old['policy_digest'],'contexts':contexts}


def missing_report():
 return {'schema':'pokerid-reference-comparison-v1','status':'UNPERFORMED','reason':'No lawfully available trusted condition-matched169-hand reference artifact acquired',
  'frequency_rows':0,'ev_rows':0,'expected_rows':4*169,'reference_difference':None,'real_game_approximation_error':None,'full_game_gto_verified':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--reference',type=Path);p.add_argument('--mode',choices=('checkdown','flop_controller'),default='flop_controller');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 report=compare(candidate(a.mode),json.loads(a.reference.read_text())) if a.reference else missing_report()
 a.output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ('status','frequency_rows','ev_rows','full_game_gto_verified')}))
