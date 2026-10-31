"""Separate source-pinned proposal experiment; never overwrite preserved solvers."""
import hashlib,json,subprocess,sysconfig
from pathlib import Path
from gto.native.build_reconstructed import decode,SOURCES,FLAGS,AUXILIARY


def build(runtime):
    runtime=Path(runtime).resolve();manifest=json.loads((runtime/'manifest.json').read_text())
    if any(v.get('build_returncode')!=0 or v.get('smoke_returncode')!=0 for v in manifest['variants'].values()):
        raise ValueError('three preserved native builds required')
    source=decode('g12_next_solver_disk.cc')
    if hashlib.sha256(source).hexdigest()!=SOURCES['g12_next'][1]:raise ValueError('source pin mismatch')
    source=source.decode().replace('#include <vector>','#include <algorithm>\n#include <vector>',1);needle='auto sampling=current;for(auto& d:sampling)d=epsilon/sampling.size()+(1-epsilon)*d;'
    if source.count(needle)!=2 or source.count('PYBIND11_MODULE(pokerid_g12,m){')!=1:raise ValueError('unexpected native patch anchors')
    first,second=source.index(needle),source.rindex(needle)
    replacement=('std::vector<int64_t> proposal_actions;for(uint64_t a=0;a<copy.n;++a)proposal_actions.push_back(action(stored,a));'
        'int proposal_raises=0;for(auto row:s.engine.history)if(row[2]!=0&&row[2]!=1)++proposal_raises;'
        'auto sampling=ordinary_proposal(current,epsilon,proposal_actions,s.engine.round,proposal_raises);')
    source=source[:second]+replacement+source[second+len(needle):]
    header=Path(__file__).with_name('targeted_sampling.h').read_text()
    source=source.replace('namespace pokerid11 {','namespace pokerid11 {\n'+header,1)
    source=source.replace('PYBIND11_MODULE(pokerid_g12,m){','PYBIND11_MODULE(pokerid_targeted,m){\nm.def("targeted_sampling", &pokerid11::ordinary_proposal);',1)
    out=runtime/'targeted';out.mkdir(exist_ok=False);path=out/'solver.cc';path.write_text(source)
    rules=decode('pokerid_rules.py')
    if hashlib.sha256(rules).hexdigest()!=AUXILIARY['pokerid_rules.py'][1]:raise ValueError('rules adapter pin differs')
    (out/'pokerid_rules.py').write_bytes(rules)
    deps=runtime/'dependencies';abseil=deps/'abseil-cpp-20240116.2';original=runtime/'g12_next'
    command=['c++',*FLAGS,str(path),str(abseil/'absl/random/discrete_distribution.cc'),
        '-I'+str(original),'-I'+str(deps/'pybind11/pybind11/include'),'-I'+str(original/'patched'),
        '-I'+str(abseil),'-I'+sysconfig.get_paths()['include'],'-o',str(out/('pokerid_targeted'+sysconfig.get_config_var('EXT_SUFFIX')))]
    subprocess.run(command,check=True)
    metadata={'schema':'pokerid-targeted-proposal-v1','original_sha256':SOURCES['g12_next'][1],
        'patched_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'proposal':'preflop90% targeted2.5/9/21BB plus10%all-legal uniform; postflop original uniform proposal',
        'game_actions_pruned':False,'unbiased_importance_equations_changed':False,'command':command}
    # Source-specific contract must never load an original-sampler checkpoint.
    metadata['contract']='g12-targeted-v1:'+metadata['patched_sha256']
    (out/'manifest.json').write_text(json.dumps(metadata,sort_keys=True,indent=2)+'\n')
    return metadata

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True)
    print(json.dumps(build(p.parse_args().runtime),sort_keys=True))
