"""Separate full-support hole proposal; verified explicit checkpoint migration."""
import hashlib,json,subprocess,sysconfig
from pathlib import Path
from gto.native.build_reconstructed import FLAGS,AUXILIARY,decode
TARGETED_SHA='0d6ff8fc174ceded46abba723f8df848e1721354d294e98deeb66b5f133f1a3f'

def patched_source(source):
    if hashlib.sha256(source.encode()).hexdigest()!=TARGETED_SHA:raise ValueError('targeted source pin differs')
    needle='if(chance){stage=tick();auto c=s.chances();'
    if source.count(needle)!=1:raise ValueError('native chance anchor differs')
    hook=('if(chance){stage=tick();if(s.dealt==0&&updater==1&&s.engine.n==2){'
      'const std::vector<std::vector<int64_t>> targets{{20,6},{26,10},{39,15},{43,8}};'
      'auto target=targets[iteration%targets.size()];auto world=focused_hole_draw(rng,52,target);'
      'auto pq=focused_hole_probabilities(52,world,target);for(auto card:world)s.apply(card);'
      'timing(1,stage);double child=native_episode(s,updater,mine,multiply(opp,pq.first),multiply(reach,pq.second),depth+4);'
      'return ratio(child,pq.first,pq.second);}auto c=s.chances();')
    source=source.replace(needle,hook)
    source=source.replace('namespace pokerid11 {','namespace pokerid11 {\n'+Path(__file__).with_name('focused_holes.h').read_text(),1)
    module='PYBIND11_MODULE(pokerid_targeted,m){'
    if source.count(module)!=1:raise ValueError('focused module anchor differs')
    return source.replace(module,'PYBIND11_MODULE(pokerid_focused,m){\n'
        'm.def("focused_hole_probabilities", &pokerid11::focused_hole_probabilities);\n'
        'm.def("focused_hole_draws", [](int seed,int n,std::vector<int64_t> target,int count){'
        'if(count<1||count>100000)throw std::runtime_error("focused draw budget");'
        'std::mt19937 rng(seed);std::vector<std::vector<int64_t>> out;'
        'for(int i=0;i<count;++i)out.push_back(pokerid11::focused_hole_draw(rng,n,target));return out;});',1)

def build(runtime):
    runtime=Path(runtime).resolve();parent=json.loads((runtime/'targeted/manifest.json').read_text())
    if parent['patched_sha256']!=TARGETED_SHA:raise ValueError('targeted manifest differs')
    source=patched_source((runtime/'targeted/solver.cc').read_text())
    out=runtime/'focused';out.mkdir(exist_ok=False);path=out/'solver.cc';path.write_text(source)
    rules=decode('pokerid_rules.py')
    if hashlib.sha256(rules).hexdigest()!=AUXILIARY['pokerid_rules.py'][1]:raise ValueError('rules pin differs')
    (out/'pokerid_rules.py').write_bytes(rules)
    deps=runtime/'dependencies';original=runtime/'g12_next';abseil=deps/'abseil-cpp-20240116.2'
    command=['c++',*FLAGS,str(path),str(abseil/'absl/random/discrete_distribution.cc'),
      '-I'+str(original),'-I'+str(deps/'pybind11/pybind11/include'),'-I'+str(original/'patched'),
      '-I'+str(abseil),'-I'+sysconfig.get_paths()['include'],'-o',str(out/('pokerid_focused'+sysconfig.get_config_var('EXT_SUFFIX')))]
    subprocess.run(command,check=True)
    metadata={'schema':'pokerid-focused-holes-v1','parent_source_sha256':TARGETED_SHA,
      'patched_sha256':hashlib.sha256(source.encode()).hexdigest(),'command':command,
      'proposal':'BB updater joint4hole90% rotating explicit missing pair +10% uniform full deck',
      'chance_importance':'p/q in returned value, true p in opponent reach and actual q in sampling reach',
      'native_game_actions_changed':False,'target_pairs':[[20,6],[26,10],[39,15],[43,8]]}
    metadata['contract']='pokerid-focused-holes-v1:'+metadata['patched_sha256']
    (out/'manifest.json').write_text(json.dumps(metadata,sort_keys=True,indent=2)+'\n');return metadata
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True)
 print(json.dumps(build(p.parse_args().runtime),sort_keys=True))
