"""Restricted-game exact BR/convergence and predeclared unseen-board research."""
import argparse,hashlib,json,math
from pathlib import Path
from gto.abstract.flop_exact import build as rank_build,matrix
from gto.abstract.continuation_game import build,game,combine,solve,evaluate,fixed_opponents,research_leaf
from gto.abstract.continuation_learning import FrozenContinuation,ARMS
from gto.abstract.precision_archive import unpack
from gto.abstract.frozen_flop_reach import frozen_reach
from dataclasses import asdict
TRAIN=((48,21,3),(35,31,27))
HELDOUT=((44,25,2),(40,41,7),(36,32,29),(20,12,4))
SCHEDULE=(1,10,100,1000,10000,100000)

def dump_policy(policy):return [{'key':list(k),'probabilities':list(v)} for k,v in sorted(policy.table.items())]

def leaf_audit(lib,m,preflop,stage,p,g):
 leaf=research_leaf(lib,m,preflop,stage,p);r=frozen_reach(stage,preflop,after_call=True);terms=[];masses=[]
 for i in range(169):
  for j in range(169):
   w=leaf['compatible_hole_counts'][i*169+j]*r['hero_reach'][i]*r['villain_reach'][j];masses.append(w);terms.append(w*leaf['hero_net_bb_by_class_pair'][i*169+j])
 point=math.fsum(terms)/math.fsum(masses);profile=evaluate(g,p)['profile_hero_ev_bb']
 if not math.isclose(point,profile,rel_tol=0,abs_tol=1e-8):raise ValueError('research leaf/chance reconciliation failed')
 return {'leaf_sha256':hashlib.sha256(json.dumps(leaf,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'class_pair_coverage':sum(c>0 for c in leaf['compatible_hole_counts']),'weighted_hero_ev_bb':point,'exact_type_game_hero_ev_bb':profile,'sb_chip_sign_and_order':'SB rows/BB columns; hero BB transposed and negated;2chips/BB','scope':leaf['scope'],'frozen_cfr_updated':False}

def study(directory):
 packet=json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text());_,pis=unpack(packet);pi=pis['flop_controller'];ranklib=rank_build(directory/'rank');lib=build(directory/'type');matrices={f:matrix(ranklib,f) for f in TRAIN+HELDOUT};previous=json.loads(Path('docs/qa/exact-flop-20261031/results.json').read_text());rows=[]
 for stage in ('vs_3bet','vs_4bet'):
  gs={f:game(lib,m,pi,stage) for f,m in matrices.items()};training=combine([gs[f] for f in TRAIN]);legacy=[]
  for old in previous['reports']:
   if old['stage']!=stage:continue
   for run in old['learning']:
    p=FrozenContinuation({tuple(x['observation_key']):tuple(x['arm_probabilities']) for x in run['policy']});legacy.append({'original_flop':old['flop'],'original_seed':run['training_seed'],'same_joint_game_evaluation':evaluate(training,p)})
  runs=[]
  for seed in (17,29):
   curve=[]
   for n in SCHEDULE:p,metrics=solve(lib,training,n,seed);curve.append(metrics)
   heldout=[]
   for f in HELDOUT:
    g=gs[f];ev=evaluate(g,p);bh,bv=len(g['hkeys']),len(g['vkeys']);mass=g['chance_mass'];hmiss=math.fsum(mass[i*bv+j] for i in range(bh) for j in range(bv) if g['hkeys'][i] not in p.table);vmiss=math.fsum(mass[i*bv+j] for i in range(bh) for j in range(bv) if g['vkeys'][j] not in p.table)
    heldout.append({'flop':list(f),'metrics':ev,'hero_unseen_type_mass':hmiss,'villain_unseen_type_mass':vmiss,'fallback':'uniform plans for unknown own type, never fit on heldout','research_leaf':leaf_audit(lib,matrices[f],pi,stage,p,g)})
   runs.append({'initialization_seed':seed,'training_curve':curve,'frozen_policy':dump_policy(p),'fixed_opponent_responses':fixed_opponents(training,p),'heldout_flops':heldout,'training_leaf_audits':[leaf_audit(lib,matrices[f],pi,stage,p,gs[f]) for f in TRAIN]})
  rows.append({'stage':stage,'training_type_counts':[len(training['hkeys']),len(training['vkeys'])],'legacy_sample_learner_on_same_joint_game':legacy,'runs':runs})
 sources=('continuation_game.py','continuation_game.cc','continuation_quality.py','continuation_learning.py','flop_exact.py','flop_exact_matrix.cc')
 return {'schema':'pokerid-restricted-continuation-quality-v1','condition':packet['condition'],'frozen_preflop_policy_digest':packet['policies']['flop_controller']['policy_digest'],'arms':[asdict(x) for x in ARMS],'training_flops':[list(f) for f in TRAIN],'heldout_flops':[list(f) for f in HELDOUT],'research_training_board_weights':[.5,.5],'weights_are_real_flop_chance':False,'target_restricted_training_nashconv_bb':.01,'target_is_formal_gto_acceptance':False,'rows':rows,'sampling_error_bb':0,'numerical_guard_bb':1e-7,'real_game_model_approximation_error_bb':None,'external_gto_deviation_bb':None,'formal_acceptance_complete':0,'full_game_gto_verified':False,'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in sources},'scope':'exact Bayesian4arm signal game; whole-plan mixtures; own signal only; heldout boards never used for training or selection; restricted NashConv/2 is NOT NLHE exploitability; leaf hook research-only,no frozen CFR updates'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=study(a.build_dir);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
 for row in r['rows']:
  for run in row['runs']:print(row['stage'],run['initialization_seed'],[(x['iterations'],x['restricted_nashconv_bb']) for x in run['training_curve']],[(x['flop'],x['metrics']['restricted_nashconv_bb']) for x in run['heldout_flops']])
