"""Compile a new oracle against an already hash-pinned reconstructed runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sysconfig
from gto.native.build_reconstructed import FLAGS,AUXILIARY


def build(runtime):
    runtime=Path(runtime).resolve();manifest=json.loads((runtime/'manifest.json').read_text())
    if any(v.get('build_returncode')!=0 or v.get('smoke_returncode')!=0 for v in manifest['variants'].values()):
        raise ValueError('all pinned native builds/smokes must pass first')
    source=Path(__file__).with_name('onebb_sampler.cc')
    rules=runtime/'g12_next/g11_rules_embed.h'
    if hashlib.sha256(rules.read_bytes()).hexdigest()!=AUXILIARY['g11_rules_embed.h'][1]:
        raise ValueError('preserved native rules hash mismatch')
    state=runtime/'g12_next/g11_native_state.h'
    original=Path(__file__).resolve().parents[2]/'handoff/gto/g12_next/g11_native_state.h'
    if state.read_bytes()!=original.read_bytes():raise ValueError('preserved native state header differs')
    out=runtime/'onebb';out.mkdir(exist_ok=False)
    binary=out/('pokerid_onebb'+sysconfig.get_config_var('EXT_SUFFIX'))
    command=['c++',*FLAGS,str(source),'-I'+str(runtime/'dependencies/pybind11/pybind11/include'),
             '-I'+str(runtime/'g12_next'),'-I'+sysconfig.get_paths()['include'],'-o',str(binary)]
    subprocess.run(command,check=True)
    metadata={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'rules_sha256':hashlib.sha256(rules.read_bytes()).hexdigest(),
        'native_state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),
        'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
        'command':command,'compiler':subprocess.check_output(['c++','--version'],text=True).splitlines()[0]}
    (out/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--runtime',type=Path,required=True)
    print(json.dumps(build(parser.parse_args().runtime),indent=2))
