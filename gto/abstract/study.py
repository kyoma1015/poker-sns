"""Finite reproducible abstraction comparison; no formal/full-game certificate."""
import argparse,gzip,hashlib,json,math,time
from pathlib import Path
from gto.abstract.model import build,load,kernel,classes,chance,tree,payoffs,solve,ranges,heldout,CONDITION

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def experiment(output,*,samples=256,iterations=4000,seeds=(1701,2901),validation_seed=700017):
 if len(seeds)!=2 or len(set(seeds))!=2 or any(type(s) is not int or not 0<=s<2**31 for s in seeds):raise ValueError('two distinct independent payoff seeds required')
 if type(validation_seed) is not int or validation_seed in seeds or not 0<=validation_seed<2**31:raise ValueError('fresh independent validation seed required')
 output=Path(output);output.mkdir(parents=True,exist_ok=False);lib=load(build(output/'build'));nodes=tree();counts,p=chance(classes());runs=[];kernels=[];policies={}
 for seed in seeds:
  k=kernel(lib,samples=samples,seed=seed);kernels.append(k);print('ABSTRACT_KERNEL '+json.dumps({'seed':seed,'seconds':k['seconds'],'samples':samples}),flush=True)
  with gzip.open(output/f'kernel-{seed}.json.gz','wt') as cache:json.dump(k,cache,sort_keys=True)
  for mode in ('checkdown','flop_controller'):
   leaf=payoffs(k,mode,nodes);observations=[]
   for t in sorted(set((min(100,iterations),iterations))):
    r=solve(lib,leaf,p,nodes,iterations=t);observations.append({key:r[key] for key in ('iterations','seconds','profile_sb_ev_bb','abstract_nashconv_bb')})
   replay=solve(lib,leaf,p,nodes,iterations=iterations)
   for field in ('strategy','action_ev_chips','reach','profile_sb_ev_bb','abstract_nashconv_bb'):
    if replay[field]!=r[field]:raise ValueError('same-input deterministic CFR replay differs')
   policies[(seed,mode)]=r['strategy']
   (output/f'policy-{seed}-{mode}.json').write_text(json.dumps({'condition':CONDITION,'tree':nodes,'strategy':r['strategy'],'kernel_digest':digest(k['mean'])},sort_keys=True)+'\n')
   rs=ranges(r,nodes)
   radius=k['simultaneous_kernel_radius_chips']/2
   for context in rs.values():
    for row in context['hands'].values():row['model_ev_interval_bb']=[max(-50.,row['ev_bb']-radius),min(50.,row['ev_bb']+radius)]
   policy_digest=digest(r['strategy']);payoff_digest=digest(k['mean'])
   run={'seed':seed,'mode':mode,'samples_per_class_pair':samples,'iterations':iterations,'learning':observations,
    'profile_sb_ev_bb':r['profile_sb_ev_bb'],'abstract_nashconv_bb':r['abstract_nashconv_bb'],
    'abstract_exploitability_bb':r['abstract_nashconv_bb']/2,'br_sb_ev_bb':r['br_sb_ev_bb'],'br_bb_min_sb_ev_bb':r['br_bb_min_sb_ev_bb'],
    'policy_digest':policy_digest,'payoff_digest':payoff_digest,'same_input_replay':True,'ranges':rs,
    'simultaneous_payoff_error_bound_bb':k['simultaneous_kernel_radius_chips']/2,
    'expected_abstract_game_nashconv_upper_bb':min(100.,r['abstract_nashconv_bb']+k['simultaneous_kernel_radius_chips']),
    'real_game_approximation_error_bb':None,'full_game_gto_verified':False,'reference_solution_comparison':'UNPERFORMED: no trusted matching HU50BB reference supplied',
    'model_scope':'finite preflop action/class abstraction with fixed continuation controllers; not postflop equilibrium'}
   runs.append(run);print('ABSTRACT_LEARNING '+json.dumps({key:run[key] for key in ('seed','mode','learning','abstract_nashconv_bb')}),flush=True)
 validation_kernel=kernel(lib,samples=samples,seed=validation_seed)
 with gzip.open(output/f'kernel-{validation_seed}.json.gz','wt') as cache:json.dump(validation_kernel,cache,sort_keys=True)
 validation=[{'mode':mode,**heldout(lib,policies[(seeds[0],mode)],validation_kernel,mode,nodes,p)} for mode in ('checkdown','flop_controller')]
 comparisons=[]
 for mode in ('checkdown','flop_controller'):
  a,b=[r for r in runs if r['mode']==mode][:2]
  for stage in ('rfi','vs_open','vs_3bet','vs_4bet'):
   x,y=a['ranges'][stage],b['ranges'][stage]
   freq=max(abs(u-v) for label in x['hands'] for u,v in zip(x['hands'][label]['frequencies'],y['hands'][label]['frequencies']))
   ev=max(abs(x['hands'][label]['ev_bb']-y['hands'][label]['ev_bb']) for label in x['hands'])
   comparisons.append({'mode':mode,'stage':stage,'max_frequency_difference':freq,'max_model_ev_difference_bb':ev,'interpretation':'independent payoff-seed sensitivity, not an error bound against real poker'})
 sensitivity=[]
 for seed in seeds:
  a,b=[r for r in runs if r['seed']==seed]
  sensitivity.append({'seed':seed,'profile_ev_difference_bb':b['profile_sb_ev_bb']-a['profile_sb_ev_bb'],
   'interpretation':'controller-model sensitivity; policies differ; not a unilateral improvement'})
 manifest=json.loads((output/'build/manifest.json').read_text())
 result={'schema':'pokerid-preflop-abstract-study-v1','condition':CONDITION,'source':manifest,
  'validation_seed':validation_seed,'exact_joint_deals':sum(counts),'joint_mass_digest':digest(counts),'seeds':list(seeds),'runs':runs,
  'fixed_policy_independent_validation':validation,'independent_seed_comparison':comparisons,'continuation_model_sensitivity':sensitivity,
  'formal_acceptance_complete':0,'full_game_gto_verified':False,'ui_admission':'RESEARCH_ONLY_NOT_FORMAL_GTO',
  'unmodeled':'omitted bet sizes; class aggregation beyond exact blockers; optimized postflop strategies; later-street betting; formal stack/sizing specifications'}
 (output/'evidence.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 summary={k:v for k,v in result.items() if k not in ('runs','source')};summary['runs']=[{k:v for k,v in r.items() if k!='ranges'} for r in runs]
 print('ABSTRACT_SUMMARY '+json.dumps(summary,sort_keys=True),flush=True);return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--samples',type=int,default=256);p.add_argument('--iterations',type=int,default=4000)
 a=p.parse_args();experiment(a.output,samples=a.samples,iterations=a.iterations)
