"""Exact finite board population for FIXED suit-invariant continuation models."""
import argparse,ctypes as C,itertools,json,math,subprocess
from pathlib import Path
from gto.abstract import fullsupport as fs,independent_preflop as old,call_study as cs,root_interval as ri,model
from gto.abstract.factorial_transfer import category
from gto.abstract.model import doubles
from gto.abstract.range_study import sha
ROOT=Path('docs/qa/suit-exact-preflop-20261106');P=ROOT/'protocol.json';DESIGN=ROOT/'design.json'
PERM=tuple(itertools.permutations(range(4)))
def canonical(b):return min(tuple(sorted(c//4*4+p[c%4] for c in b)) for p in PERM)
def sources():return {**old.sources(),**{f:sha(Path(__file__).with_name(f)) for f in ('suit_exact.py','suit_exact_native.cc','suit_exact_br.py')}}
def design():
 orbits={}
 for f in itertools.combinations(range(52),3):
  c=canonical(f);orbits[c]=orbits.get(c,0)+1
 prior=json.loads(old.DESIGN.read_text());known={}
 for f in sorted({tuple(f) for draws in prior['draws'].values() for f in draws}):known.setdefault(canonical(f),f)
 return {'protocol_sha256':sha(P),'source_sha256':sources(),'teacher_sha256':sha(old.TEACHER),'prior_design_sha256':sha(old.DESIGN),'orbits':[{'canonical':c,'representative':known.get(c,c),'multiplicity':n} for c,n in sorted(orbits.items())],'selection_uses_payoffs':False,'new_unseen_test':False}
def build(path):
 path.mkdir(parents=True,exist_ok=True);dest=path/'suit-exact.so';subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(Path(__file__).with_name('suit_exact_native.cc')),'-o',str(dest)],check=True);lib=C.CDLL(str(dest.resolve()));lib.accumulate.argtypes=[C.c_int,C.c_int,model.DP,model.DP,C.POINTER(C.c_longdouble),C.POINTER(C.c_longdouble)];lib.accumulate.restype=C.c_int;return lib

def enumerate_oracle(root,cache,p,d):
 env=cs.setup(root/'environment');native=fs.build(root/'oracle');coeff=ri.build(root/'coefficient');teacher=json.loads(old.TEACHER.read_text());coefs={c:fs.coefficients(teacher,json.loads(old.P.read_text()),c,coeff) for c in sorted({r['category'] for r in json.loads(old.DESIGN.read_text())['teacher']})};names=next(iter(coefs.values()))[3];bounds=[max(co[i][j] for co in coefs.values()) for i,j in [(2,k) for k in range(len(names))]];identity={'teacher_sha256':sha(old.TEACHER),'source_sha256':old.sources(),'frozen_preflop_digest':env[4]}
 # Exact invariance check uses each public texture, not hidden-card strategies.
 audits=[]
 for cat in coefs:
  f=next(r['canonical'] for r in d['orbits'] if category(r['canonical'])==cat);other=sorted(c//4*4+(c%4+1)%4 for c in f);a,ma=fs.evaluate_flop(native,env[0],f,coefs[cat]);b,mb=fs.evaluate_flop(native,env[0],other,coefs[cat]);err=max(abs(x-y) for x,y in zip(a,b));masserr=max(abs(x-y) for x,y in zip(ma,mb));audits.append({'category':cat,'flop':f,'permuted':other,'max_class_payoff_error_bb':err,'max_mass_error':masserr})
  if err>p['validation']['suit_payoff_tolerance_bb_per_board'] or masserr>1e-15:raise ValueError('suit invariance failed; do not use orbit reduction')
 cache.mkdir(parents=True,exist_ok=True);sums=(C.c_longdouble*(len(names)*fs.S))();mass=(C.c_longdouble*fs.S)();acc=build(root/'accumulate')
 for k,row in enumerate(d['orbits']):
  f=row['representative'];path=cache/(fs.digest({'identity':identity,'flop':f})+'.json')
  if path.exists():
   cached=json.loads(path.read_text())
   if cached['identity']!=identity or cached['flop']!=f:raise ValueError('cached identity mismatch')
   y=fs.unpack(cached['payoff']);m=fs.unpack(cached['mass'])
  else:
   y,m=fs.evaluate_flop(native,env[0],f,coefs[category(f)]);temp=path.with_suffix('.suit-tmp');temp.write_text(json.dumps({'identity':identity,'flop':f,'payoff':fs.pack(y),'mass':fs.pack(m)},sort_keys=True,separators=(',',':'))+'\n');temp.replace(path)
  if acc.accumulate(len(names),row['multiplicity'],doubles(y),doubles(m),sums,mass):raise ValueError('exact chance sum failed')
  if (k+1)%32==0:print(json.dumps({'orbits_done':k+1,'total':len(d['orbits'])}),flush=True)
 point=list(sums);mass_error=max(abs(x-1) for x in mass)
 if mass_error>p['validation']['all169square_mass_tolerance']:raise ValueError('card removal probability not conserved')
 if any(abs(v)>bounds[k//fs.S]+1e-8 for k,v in enumerate(point)):raise ValueError('physical payoff support')
 symmetry=max(abs(point[k*fs.S+h*169+h]) for k,(_,leaf) in enumerate(names) if model.tree()[leaf]['value']==100 for h in range(169))
 if symmetry>p['validation']['allin_diagonal_tolerance_bb']:raise ValueError('allin seat-swap identity')
 guard=p['validation']['numeric_guard_bb'];low=[max(-bounds[k//fs.S],v-guard) for k,v in enumerate(point)];high=[min(bounds[k//fs.S],v+guard) for k,v in enumerate(point)]
 for k,(_,leaf) in enumerate(names):
  if model.tree()[leaf]['value']==100:
   for h in range(169):i=k*fs.S+h*169+h;point[i]=low[i]=high[i]=0.
 return env,teacher,names,{'point':fs.pack(point),'lower':fs.pack(low),'upper':fs.pack(high),'samples':len(d['orbits']),'unique_physical_flops':len(d['orbits']),'represented_physical_flops':sum(r['multiplicity'] for r in d['orbits']),'exact_board_fraction':1.,'counterfactual_estimator_support':'all169²x9leaves;finiteboardpopulation enumerated via proven suit symmetry','physical_point_clips':0,'empty_intervals':0,'model_bounds_bb':bounds,'numeric_guard_bb':guard,'sampling_error_bb':0.,'numeric_guard_is_formal_rounding_proof':False,'suit_audits':audits,'max_class_chance_sum_error':mass_error,'max_allin_diagonal_error_bb':symmetry}

def run(root,cache,p,d):
 env,teacher,names,oracle=enumerate_oracle(root,cache,p,d);lib=model.load(model.build(root/'preflop'));prob=model.chance(model.classes())[1];variants=json.loads(old.P.read_text())['variants'];out={};allpolicies={}
 for variant in variants:
  pay=fs.payoff_planes(oracle,teacher,variant,names);curve=[]
  for it in p['learning']['iterations']:
   result=model.solve(lib,pay['point'],prob,model.tree(),iterations=it);curve.append({k:result[k] for k in ('iterations','profile_sb_ev_bb','abstract_nashconv_bb')})
  pi=result['strategy'];allpolicies[variant]=pi;ev=old.details(lib,pi,pay['point']);lo=old.details(lib,pi,pay['lower']);hi=old.details(lib,pi,pay['upper']);contexts=model.ranges({**ev,'strategy':pi},model.tree());wanted={}
  for stage in ('rfi','vs_open','vs_3bet','vs_4bet'):
   context=contexts[stage];node=next(i for i,n in enumerate(model.tree()) if n['actor']==context['actor'] and n.get('history')==context['history']);hands={}
   for h,label in enumerate(model.CLASSES):
    row=context['hands'][label];intervals=[sorted([lo['action_ev_chips'][(node*3+a)*169+h]/2,hi['action_ev_chips'][(node*3+a)*169+h]/2]) for a in range(len(context['actions']))];hands[label]={**row,'action_ev_intervals_bb':intervals,'model_ev_interval_bb':[math.fsum(f*x[side] for f,x in zip(row['frequencies'],intervals)) for side in (0,1)]}
   wanted[stage]={**context,'hands':hands}
  from gto.abstract.suit_exact_br import evaluate as independent_br
  independent=independent_br(model.tree(),pi,prob,pay['point']);br_error=max(abs(independent[k]-ev[k]) for k in independent)
  if br_error>p['validation']['independent_br_tolerance_bb']:raise ValueError('independent private BR disagreement')
  bounds=ri.evaluate(lib,model.tree(),pi,prob,pay['lower'],pay['upper'],169)
  for k,v in bounds.items():
   if isinstance(v,list):bounds[k]=[x/2 for x in v]
  # Frozen original preflop strategy is evaluated in SAME new fixed continuation.
  frozen_ev=old.details(lib,env[3],pay['point']);frozen_bounds=ri.evaluate(lib,model.tree(),env[3],prob,pay['lower'],pay['upper'],169)
  for k,v in frozen_bounds.items():
   if isinstance(v,list):frozen_bounds[k]=[x/2 for x in v]
  out[variant]={'contexts':wanted,'learning':curve,'sample_game_nashconv_bb':ev['abstract_nashconv_bb'],'evaluation_sample_nashconv_bb':ev['abstract_nashconv_bb'],'root_expected_game_bounds_bb':bounds,'policy_digest':fs.digest(pi),'continuation_profile_digest':fs.digest(teacher['profiles'][variant]),'game_scope':'finiteclass preflop tree,exact board expectation of FIXED coarse learned flop policies;not fullNLHE','full_game_gto_verified':False,'independent_python_br':independent,'maximum_native_python_br_difference_bb':br_error,'frozen_preflop_same_model_evaluation':{'point':{k:v for k,v in frozen_ev.items() if k not in ('action_ev_chips','reach')},'bounds_bb':frozen_bounds}}
 summary={k:{f:oracle[f] for f in ('samples','unique_physical_flops','represented_physical_flops','exact_board_fraction','counterfactual_estimator_support','physical_point_clips','empty_intervals')} for k in ('training_oracle','evaluation_oracle')}
 full={'schema':'pokerid-independent-preflop-research-v2','models':out,'condition':{'players':2,'stack_bb':50,'blinds_bb':[.5,1],'ante_bb':0,'rake_pct':0,'raise_to_bb':[2.5,9,21,50],'formats':['mtt_chipEV','ring_zero_rake'],'formal_profile':False},'uncertainty_kind':'enumerated_population_with_empirical_rounding_guard','confidence_simultaneous_both_oracles':None,'numeric_guard_bb':oracle['numeric_guard_bb'],'numeric_guard_is_formal_rounding_proof':False,'oracle_summary':summary,'quality':{'all169x4_rows_each_variant':True,'sample_game_convergence':all(m['sample_game_nashconv_bb']<=.01 for m in out.values()),'expected_game_root_NC_upper_at_most0_1':all(m['root_expected_game_bounds_bb']['preflop_nashconv_interval'][1]<=.1 for m in out.values()),'external_gto_verified':False,'real_game_approximation_verified':False},'protocol_sha256':sha(P),'design_sha256':sha(DESIGN),'source_sha256':sources(),'teacher_sha256':sha(old.TEACHER),'full_game_gto_verified':False,'formal_acceptance_complete':0,'external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN','ordinary_catalog_admission':'REJECTED_RESEARCH_ONLY','oracle':oracle,'complete_preflop_policies':allpolicies}
 return full

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--phase',choices=('design','run','export'),required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--build-dir',type=Path);a.add_argument('--cache-dir',type=Path);a.add_argument('--input',type=Path);v=a.parse_args();p=json.loads(P.read_text())
 if v.output.exists():a.error('fresh output required')
 if v.phase=='design':out=design()
 elif v.phase=='export':out={k:x for k,x in json.loads(v.input.read_text()).items() if k not in ('source_sha256','oracle','complete_preflop_policies')}
 else:
  d=json.loads(DESIGN.read_text())
  if d['source_sha256']!=sources() or d['protocol_sha256']!=sha(P) or d['teacher_sha256']!=sha(old.TEACHER):raise ValueError('immutable exact integration design changed')
  if len(d['orbits'])!=1755 or sum(r['multiplicity'] for r in d['orbits'])!=22100:raise ValueError('complete orbit partition required')
  out=run(v.build_dir,v.cache_dir,p,d)
 v.output.parent.mkdir(parents=True,exist_ok=True);v.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({'phase':v.phase,'quality':out.get('quality')}))
