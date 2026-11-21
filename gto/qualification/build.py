"""Thin full-native replay module, original State/rules unchanged; no solver training."""
import argparse,hashlib,importlib.util,json,subprocess,sys,sysconfig,urllib.request,zipfile
from pathlib import Path
from gto.native.build_reconstructed import decode,PINS,ROOT

SOURCE=r'''
#include "g11_native_state.h"
using namespace pokerid11state;
PYBIND11_MODULE(_qualification_native,m){
 py::class_<State>(m,"NativeState")
 .def(py::init([](py::object game){return State(std::make_shared<Spec>(game));}))
 .def("audit",&State::audit).def("apply_action",&State::apply)
 .def("legal_actions",&State::legal_actions).def("current_player",&State::actor)
 .def("is_terminal",&State::terminal).def("is_chance_node",&State::chance)
 .def("returns",&State::returns);
 m.def("rank7",[](const V& cards){return rank7(cards);});
}
'''
def build(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    name='pybind11-2.13.6-py3-none-any.whl';url,pin=PINS[name];wheel=root/name
    if not wheel.exists():
        with urllib.request.urlopen(url,timeout=30) as response:wheel.write_bytes(response.read())
    if hashlib.sha256(wheel.read_bytes()).hexdigest()!=pin:raise ValueError('pinned pybind wheel differs')
    with zipfile.ZipFile(wheel) as archive:
        for item in archive.infolist():
            p=Path(item.filename)
            if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe wheel path')
        archive.extractall(root/'headers')
    (root/'g11_rules_embed.h').write_bytes(decode('g11_rules_embed.h'))
    (root/'g11_native_state.h').write_bytes((ROOT/'handoff/gto/g12_next/g11_native_state.h').read_bytes())
    (root/'pokerid_rules.py').write_bytes(decode('pokerid_rules.py'))
    (root/'replay.cc').write_text(SOURCE)
    output=root/('_qualification_native'+sysconfig.get_config_var('EXT_SUFFIX'))
    command=['c++','-O2','-std=c++20','-fno-fast-math','-ffp-contract=off','-shared','-fPIC',
             str(root/'replay.cc'),'-I'+str(root),'-I'+str(root/'headers/pybind11/include'),
             '-I'+sysconfig.get_path('include'),'-o',str(output)]
    subprocess.run(command,check=True)
    (root/'build.json').write_text(json.dumps({'command':command,'wheel_sha256':pin,'native_binary_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'rules_sha256':hashlib.sha256((root/'g11_rules_embed.h').read_bytes()).hexdigest(),'state_sha256':hashlib.sha256((root/'g11_native_state.h').read_bytes()).hexdigest()},indent=2)+'\n')
    return output

def load(root):
    root=Path(root)
    for name,path in (('pokerid_rules',root/'pokerid_rules.py'),('_qualification_native',next(root.glob('_qualification_native*.so')))):
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return sys.modules['pokerid_rules'],sys.modules['_qualification_native']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);a=p.parse_args();print(build(a.directory))
