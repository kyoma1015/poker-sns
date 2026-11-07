"""Source-pinned separate generic-solver exact-action control experiment.

Original three modules and targeted sampler bytes remain immutable. This hook
only initializes a declared exact action baseline before the existing unbiased
sample correction. Sampling probabilities, regret/average equations unchanged.
"""
import hashlib,json,subprocess,sysconfig
from pathlib import Path
from gto.native.build_reconstructed import decode,SOURCES,FLAGS,AUXILIARY


def patched_source():
    raw=decode('g12_next_solver_disk.cc')
    if hashlib.sha256(raw).hexdigest()!=SOURCES['g12_next'][1]:raise ValueError('original solver pin differs')
    source=raw.decode()
    action='int64_t sampled_action=action(stored,ix);++stored.visits;++stored.counts[sampled_action];s.attr("apply_action")(sampled_action);'
    if source.count(action)!=1:raise ValueError('generic action hook anchor differs')
    hook=('std::map<int64_t,double> exact_controls;'
          'if(use_baseline&&py::hasattr(s,"exact_action_values"))'
          'exact_controls=s.attr("exact_action_values")().cast<std::map<int64_t,double>>();')
    source=source.replace(action,hook+action)
    baseline='if(use_baseline){for(auto it=x.baselines.lower_bound(offset);it!=x.baselines.end()&&it->first<offset+x.n;++it)estimates[it->first-offset]=it->second;}'
    if source.count(baseline)!=2:raise ValueError('baseline reconstruction anchor differs')
    override=('if(use_baseline){for(uint64_t a=0;a<x.n;++a){auto known=exact_controls.find(action(x,a));'
              'if(known!=exact_controls.end()){finite(known->second);estimates[a]=known->second;}}}')
    source=source.replace(baseline,baseline+override,1)
    module='PYBIND11_MODULE(pokerid_g12,m){'
    if source.count(module)!=1:raise ValueError('module anchor differs')
    return source.replace(module,'PYBIND11_MODULE(pokerid_response,m){',1)


def build(runtime):
    runtime=Path(runtime).resolve();manifest=json.loads((runtime/'manifest.json').read_text())
    if any(v.get('build_returncode')!=0 or v.get('smoke_returncode')!=0 for v in manifest['variants'].values()):
        raise ValueError('three preserved builds required')
    source=patched_source();out=runtime/'response-controls';out.mkdir(exist_ok=False)
    path=out/'solver.cc';path.write_text(source)
    rules=decode('pokerid_rules.py')
    if hashlib.sha256(rules).hexdigest()!=AUXILIARY['pokerid_rules.py'][1]:raise ValueError('rules adapter pin differs')
    (out/'pokerid_rules.py').write_bytes(rules)
    deps=runtime/'dependencies';abseil=deps/'abseil-cpp-20240116.2';original=runtime/'g12_next'
    command=['c++',*FLAGS,str(path),str(abseil/'absl/random/discrete_distribution.cc'),
        '-I'+str(original),'-I'+str(deps/'pybind11/pybind11/include'),'-I'+str(original/'patched'),
        '-I'+str(abseil),'-I'+sysconfig.get_paths()['include'],'-o',str(out/('pokerid_response'+sysconfig.get_config_var('EXT_SUFFIX')))]
    subprocess.run(command,check=True)
    metadata={'schema':'pokerid-exact-action-controls-v1','original_sha256':SOURCES['g12_next'][1],
        'patched_sha256':hashlib.sha256(source.encode()).hexdigest(),'command':command,
        'sampling_and_regret_equations_changed':False,'full_game_actions_pruned':False,
        'scope':'generic single-updater exact fold baseline; no native fast-path change'}
    metadata['contract']='pokerid-response-controls-v1:'+metadata['patched_sha256']
    (out/'manifest.json').write_text(json.dumps(metadata,sort_keys=True,indent=2)+'\n')
    return metadata

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--runtime',type=Path,required=True)
    print(json.dumps(build(parser.parse_args().runtime),sort_keys=True))
