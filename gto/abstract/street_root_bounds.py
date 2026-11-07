"""Readonly partial root EV set: two population profiles, all other CALLs unknown.

Conditional board coverage must not be called full preflop reach coverage.
No original policy, payoff file or solver state is mutated.
"""
import math
from gto.abstract import model
from gto.abstract.frozen_flop_reach import frozen_reach


def root_bounds(policy,population):
 nodes=model.tree();n=169;_,chance=model.chance(model.classes());reaches={s:frozen_reach(s,policy,after_call=True) for s in ('vs_3bet','vs_4bet')};known={}
 for stage,r in reaches.items():
  parent=nodes[r['node_index']];leaf=parent['children'][parent['actions'].index('call')]
  if leaf in known:raise ValueError('conditional CALL leaves must be disjoint')
  known[leaf]=(stage,r)
 exact_fold=0.;unknown_mass=0.;conditional_mass=0.;root_coverage=0.;lo=0.;hi=0.;details={};total=0.
 def visit(k,r0,r1):
  nonlocal exact_fold,unknown_mass,conditional_mass,root_coverage,lo,hi,total
  node=nodes[k]
  if node['actor']>=0:
   for a,c in enumerate(node['children']):
    weights=policy[(k*3+a)*n:(k*3+a+1)*n];visit(c,[x*y for x,y in zip(r0,weights)] if node['actor']==0 else r0,[x*y for x,y in zip(r1,weights)] if node['actor']==1 else r1)
   return
  mass=math.fsum(chance[i*n+j]*r0[i]*r1[j] for i in range(n) for j in range(n));total+=mass
  if not node['matched']:exact_fold+=mass*node['value']/2;return
  if k not in known:unknown_mass+=mass;return
  stage,r=known[k]
  if not math.isclose(mass,r['conditional_mass'],rel_tol=0,abs_tol=1e-12):raise ValueError('prefix mass mismatch')
  v=population['stages'][stage]['checkpoints'][-1]
  if v['empty_intersection_failure']:raise ValueError('no valid population confidence interval')
  low,high=v['uniform512_profile_ev_interval_bb']
  if r['hero_actor']==1:low,high=-high,-low
  conditional_mass+=mass;root_coverage+=mass*v['evaluated_board_probability'];lo+=mass*low;hi+=mass*high;details[stage]={'call_leaf_probability':mass,'root_sb_contribution_interval_bb':[mass*low,mass*high],'evaluated_root_board_probability':mass*v['evaluated_board_probability']}
 visit(0,[1.]*n,[1.]*n)
 if not math.isclose(total,1,abs_tol=1e-12):raise ValueError('root probability conservation failed')
 return {'root_sb_ev_interval_bb':[exact_fold+lo-50*unknown_mass,exact_fold+hi+50*unknown_mass],'exact_fold_terminal_root_contribution_bb':exact_fold,'two_profile_call_probability':conditional_mass,'other_call_probability_unknown':unknown_mass,'other_call_ev_contribution_bounds_bb':[-50*unknown_mass,50*unknown_mass],'computed_root_board_probability':root_coverage,'conditional_prefixes':details,'confidence':population['family_confidence'],'scope':'fixed frozen preflop actions; new uniform512 restricted continuations at two CALL leaves; all other CALL continuations unconstrained within50BB. NOT original frozen full payoff or GTO.','real_game_approximation_error':'UNKNOWN','policy_updated':False}

if __name__=='__main__':
 import argparse,json
 from pathlib import Path
 from gto.abstract.range_study import initialize
 p=argparse.ArgumentParser();p.add_argument('--population',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True);a=p.parse_args()
 if a.output.exists():p.error('fresh output required')
 _,_,_,policy,_=initialize(a.build_dir);out=root_bounds(policy,json.loads(a.population.read_text()));a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
