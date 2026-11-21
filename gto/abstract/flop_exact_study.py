"""Exact-reference comparison, independent old-MC seeds and research learner."""
import argparse,hashlib,json,math,time
from pathlib import Path
from gto.abstract.flop_exact import build,matrix,evaluate
from gto.abstract.flop_conditional import evaluate as monte_carlo
from gto.abstract.precision_runouts import build as build_runouts
from gto.abstract.precision_archive import unpack
from gto.abstract.continuation_learning import experiment

def study(directory):
 packet=json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text());_,policies=unpack(packet);policy=policies['flop_controller'];previous=json.loads(Path('docs/qa/flop-conditional-20261031/results.json').read_text())
 lib=build(directory/'exact');fast=build_runouts(directory/'runouts');matrices={};times={}
 for f in ((48,21,3),(35,31,27)):
  matrices[f]=matrix(lib,f);times[str(f)]=matrices[f]['seconds']
 reports=[];mc_times=[];learning_times=[];exact_times=[]
 for index,prior in enumerate(previous['reports']):
  stage=prior['stage'];flop=tuple(prior['flop']);m=matrices[flop];start=time.perf_counter();r=evaluate(lib,m,policy,stage);exact_times.append(time.perf_counter()-start);r['previous_32draw']=prior['aggregate'];r['mc_seed_checks']=[]
  for seed in (81117,93133):
   start=time.perf_counter();result=monte_carlo(fast,policy,stage,flop,samples=32,seed=seed+index*10000019);mc_times.append(time.perf_counter()-start);interval=result['aggregate']['delta']['sampling_interval_bb'];truth=r['aggregate']['delta']
   r['mc_seed_checks'].append({'seed':result['seed'],'estimate_bb':result['aggregate']['delta']['ev_bb'],'error_vs_exact_bb':result['aggregate']['delta']['ev_bb']-truth,'interval_bb':interval,'exact_inside_interval':interval[0]<=truth<=interval[1]})
  start=time.perf_counter();r['learning']=[experiment(m,policy,stage,seed) for seed in (17,29)];learning_times.append(time.perf_counter()-start);reports.append(r)
 result={'schema':'pokerid-exact-flop-v1','condition':packet['condition'],'policy_digest':packet['policies']['flop_controller']['policy_digest'],'reports':reports,'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('flop_exact.py','flop_exact_matrix.cc','flop_exact_study.py','continuation_learning.py','precision_native.cc')},'formal_acceptance_complete':0,'sampling_error_bb':0,'model_approximation_error_bb':None,'external_gto_deviation_bb':None,'confidence_note':'exact reference has arithmetic guard, not MC confidence; independent MC checks are finite observations, not empirical proof of99% coverage'}
 return result,{'rank_matrix_wall_seconds':times,'exact_expectation_per_condition_seconds':exact_times,'old_mc32_per_condition_seconds':mc_times,'learning_per_condition_seconds':learning_times,'costs':'unique rank evaluations2*C(49,2)*C(47,2), unordered showdown comparisons2*635628*990 for both flops; reused for both stages','method_comparison':{'previous':'169-stratified hole sampling32 each + RB990 + common random old/new worlds; broad Hoeffding intervals','selective_enumeration':'not required after full rank caching; full hole enumeration is feasible','selected':'all holes/runouts with cached own ranks, shared worlds and seat exchange; no hole or runout sampling'}}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--benchmark',type=Path,required=True);a=p.parse_args();r,b=study(a.build_dir);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');a.benchmark.write_text(json.dumps(b,sort_keys=True,indent=2)+'\n')
 for x in r['reports']:print(x['stage'],x['flop'],x['aggregate'],x['mc_seed_checks'])
