"""Independent preflop learning → conditional EV intervals → guarded research UI."""
import argparse,ctypes as C,itertools,json,math,random
from pathlib import Path
from gto.abstract import fullsupport as fs,call_study as cs,root_interval as ri,model
from gto.abstract.factorial_transfer import category
from gto.abstract.model import ints,doubles
from gto.abstract.range_study import sha
ROOT=Path('docs/qa/independent-preflop-20261105');P=ROOT/'protocol.json';DESIGN=ROOT/'design.json';TEACHER=ROOT/'teacher.json'

def sources():
 return {**cs.sources(),**{f:sha(Path(__file__).with_name(f)) for f in ('fullsupport.py','fullsupport_native.cc','independent_preflop.py','independent_evaluation.py')},'core.cc':sha(Path(__file__).with_name('core.cc')),'model.py':sha(Path(__file__).with_name('model.py'))}
def design(p):
 boards=[list(b) for b in itertools.combinations(range(52),3)];cats={}
 for b in boards:cats.setdefault(category(b),[]).append(b)
 rng=random.Random(p['teacher']['seed']);teacher=[{'category':c,'cards':rng.choice(v)} for c,v in sorted(cats.items()) for _ in range(p['teacher']['boards_each_texture'])];draws={}
 for phase in ('pilot','train','evaluation'):
  rng=random.Random(p['oracle'][phase]['seed']);draws[phase]=[rng.choice(boards) for _ in range(p['oracle'][phase]['draws'])]
 return {'protocol_sha256':sha(P),'source_sha256':sources(),'teacher':teacher,'draws':draws,'no_payoff_seen':True,'selection_performed':False}
def check():
 d=json.loads(DESIGN.read_text())
 if d['source_sha256']!=sources() or d['protocol_sha256']!=sha(P):raise ValueError('immutable independent game source changed')
 return d

def details(lib,policy,payoff):
 nodes=model.tree();n=169;ev=(C.c_double*(len(nodes)*3*n))();reach=(C.c_double*(len(nodes)*n))();metrics=(C.c_double*4)()
 status=lib.abstract_evaluate(n,len(nodes),ints([x['actor'] for x in nodes]),ints([len(x['actions']) for x in nodes]),ints([c for x in nodes for c in (x['children']+[-1]*3)[:3]]),doubles(model.chance(model.classes())[1]),doubles(payoff),doubles(policy),ev,reach,metrics)
 if status:raise ValueError('independent policy evaluation')
 return {'action_ev_chips':list(ev),'reach':list(reach),'profile_sb_ev_bb':metrics[0]/2,'br_sb_ev_bb':metrics[1]/2,'br_bb_min_sb_ev_bb':metrics[2]/2,'abstract_nashconv_bb':max(0.,metrics[3]/2)}

def train(root,cache,p,d):
 env=cs.setup(root/'env');coeff=ri.build(root/'coeff');native=fs.build(root/'oracle');lib=model.load(model.build(root/'preflop'));teacher=json.loads(TEACHER.read_text());
 if teacher['source_sha256']!=sources() or teacher['design_sha256']!=sha(DESIGN):raise ValueError('teacher identity changed')
 coefs={c:fs.coefficients(teacher,p,c,coeff) for c in sorted({r['category'] for r in d['teacher']})};first=next(iter(coefs.values()));names=first[3];bounds=[max(v[2][i] for v in coefs.values()) for i in range(len(names))];identity={'teacher_sha256':sha(TEACHER),'source_sha256':sources(),'frozen_preflop_digest':env[4]};delta=(1-p['oracle']['confidence_each_dataset'])/(len(names)*fs.S);zero=[0.]*(len(names)*fs.S)
 pilot=fs.oracle(env,native,coefs,d['draws']['pilot'],zero,bounds,cache,identity,delta);control=fs.unpack(pilot['point']);training=fs.oracle(env,native,coefs,d['draws']['train'],control,bounds,cache,identity,delta)
 if training['empty_intervals']:raise ValueError('training confidence interval failure; no redraw')
 # Freeze new preflop policies BEFORE opening independent evaluation draws.
 policies={};learning={};ranges={};train_br={};prob=model.chance(model.classes())[1]
 for variant in p['variants']:
  payoff=fs.payoff_planes(training,teacher,variant,names);curve=[]
  for it in p['preflop']['iterations']:
   result=model.solve(lib,payoff['point'],prob,model.tree(),iterations=it);curve.append({k:result[k] for k in ('iterations','profile_sb_ev_bb','abstract_nashconv_bb')})
  policies[variant]=result['strategy'];learning[variant]=curve;ranges[variant]=model.ranges(result,model.tree());train_br[variant]=ri.evaluate(lib,model.tree(),result['strategy'],prob,payoff['lower'],payoff['upper'],169)
 frozen_digest=fs.digest(policies);freeze={'policies':policies,'training_oracle_sha256':fs.digest(training),'source_sha256':sources(),'design_sha256':sha(DESIGN),'evaluation_accessed':False,'policy_digest':frozen_digest};(cache/'preflop-before-evaluation.json').write_text(json.dumps(freeze,sort_keys=True,separators=(',',':'))+'\n')
 evaluation=fs.oracle(env,native,coefs,d['draws']['evaluation'],control,bounds,cache,identity,delta)
 if evaluation['empty_intervals']:raise ValueError('evaluation confidence interval failure; no redraw')
 output={};stage_names=('rfi','vs_open','vs_3bet','vs_4bet')
 for variant in p['variants']:
  payoff=fs.payoff_planes(evaluation,teacher,variant,names);ev=details(lib,policies[variant],payoff['point']);low=details(lib,policies[variant],payoff['lower']);high=details(lib,policies[variant],payoff['upper']);evaluated=model.ranges({**ev,'strategy':policies[variant]},model.tree());contexts={}
  for stage in stage_names:
   context=evaluated[stage];node=next(i for i,n in enumerate(model.tree()) if n['actor']==context['actor'] and n.get('history')==context['history']);hands={}
   for h,label in enumerate(model.CLASSES):
    row=context['hands'][label];intervals=[]
    for a in range(len(context['actions'])):
     index=(node*3+a)*169+h;ab=(low['action_ev_chips'][index]/2,high['action_ev_chips'][index]/2);intervals.append([min(ab),max(ab)])
    interval=[math.fsum(f*b[0] for f,b in zip(row['frequencies'],intervals)),math.fsum(f*b[1] for f,b in zip(row['frequencies'],intervals))];hands[label]={**row,'action_ev_intervals_bb':intervals,'model_ev_interval_bb':interval}
   contexts[stage]={**context,'hands':hands}
  root=ri.evaluate(lib,model.tree(),policies[variant],prob,payoff['lower'],payoff['upper'],169)
  for key,value in root.items():
   if isinstance(value,list):root[key]=[x/2 for x in value]
  output[variant]={'contexts':contexts,'learning':learning[variant],'sample_game_nashconv_bb':learning[variant][-1]['abstract_nashconv_bb'],'evaluation_sample_nashconv_bb':ev['abstract_nashconv_bb'],'root_expected_game_bounds_bb':root,'policy_digest':fs.digest(policies[variant]),'continuation_profile_digest':fs.digest(teacher['profiles'][variant]),'game_scope':'169-class preflop game with FIXED learned coarse flop policies;later streets checkthrough','full_game_gto_verified':False}
 from gto.abstract.independent_evaluation import measure
 fixed_policy_validation=measure(native,policies,env[3],names,bounds,d['draws']['evaluation'],control,cache,identity)
 if frozen_digest!=fs.digest(policies):raise ValueError('evaluation altered learned policy')
 comparisons={}
 variants=list(output)
 for stage in stage_names:
  a,b=[output[v]['contexts'][stage]['hands'] for v in variants];comparisons[stage]={'mean_hand_frequency_TV':math.fsum(sum(abs(x-y) for x,y in zip(a[h]['frequencies'],b[h]['frequencies']))/2 for h in model.CLASSES)/169,'maximum_action_ev_difference_bb':max(abs(x-y) for h in model.CLASSES for x,y in zip(a[h]['action_ev_bb'],b[h]['action_ev_bb'])),'interpretation':'different size-abstraction sensitivity,not external GTO deviation'}
 quality={'all169x4_rows_each_variant':all(len(m['contexts'][s]['hands'])==169 for m in output.values() for s in stage_names),'sample_game_convergence':all(m['sample_game_nashconv_bb']<=.01 for m in output.values()),'expected_game_root_NC_upper_at_most0_1':all(m['root_expected_game_bounds_bb']['preflop_nashconv_interval'][1]<=.1 for m in output.values()),'external_gto_verified':False,'real_game_approximation_verified':False}
 return {'schema':'pokerid-independent-preflop-research-v1','protocol_sha256':sha(P),'source_sha256':sources(),'teacher_sha256':sha(TEACHER),'condition':{'players':2,'stack_bb':50,'blinds_bb':[.5,1],'ante_bb':0,'rake_pct':0,'raise_to_bb':[2.5,9,21,50],'formats':['mtt_chipEV','ring_zero_rake'],'formal_profile':False},'models':output,'training_oracle':training,'evaluation_oracle':evaluation,'oracle_plane_names':names,'pilot_samples':len(d['draws']['pilot']),'independent_evaluation':True,'fixed_policy_validation':fixed_policy_validation,'policy_frozen_before_evaluation_digest':frozen_digest,'size_sensitivity':comparisons,'quality':quality,'full_game_gto_verified':False,'formal_acceptance_complete':0,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN','ordinary_catalog_admission':'REJECTED_RESEARCH_ONLY'}


def ui_export(result):
 return {k:v for k,v in result.items() if k not in ('training_oracle','evaluation_oracle','source_sha256')}|{'oracle_summary':{kind:{k:result[kind][k] for k in ('samples','unique_physical_flops','exact_board_fraction','counterfactual_estimator_support','physical_point_clips','empty_intervals')} for kind in ('training_oracle','evaluation_oracle')},'confidence_simultaneous_both_oracles':.99}

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--phase',choices=('design','teacher','train','export'),required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--build-dir',type=Path);a.add_argument('--cache-dir',type=Path);a.add_argument('--input',type=Path);v=a.parse_args();p=json.loads(P.read_text())
 if v.output.exists():a.error('fresh output required; no post-final overwrite')
 if v.phase=='design':out=design(p)
 elif v.phase=='export':out=ui_export(json.loads(v.input.read_text()))
 else:
  d=check()
  if not v.build_dir:a.error('build directory required')
  if v.phase=='teacher':out=fs.teacher(cs.setup(v.build_dir),p,d['teacher']);out['source_sha256']=sources();out['design_sha256']=sha(DESIGN)
  else:
   if not v.cache_dir:a.error('cache directory required')
   out=train(v.build_dir,v.cache_dir,p,d)
 v.output.parent.mkdir(parents=True,exist_ok=True);v.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({'phase':v.phase,'quality':out.get('quality')}))
