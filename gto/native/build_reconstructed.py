"""Reconstruct a PINNED experimental environment, never claim original G11.

Download only verified public source artifacts, build untouched copied sources
in separate directories, then import/test each variant in a separate process.
Only explicit --work-root scratch paths are written; old checkpoints are unused.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import urllib.request
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'handoff/gto'
PINS = {
    'pybind11-2.13.6-py3-none-any.whl': ('https://files.pythonhosted.org/packages/13/2f/0f24b288e2ce56f51c920137620b4434a38fd80583dbbe24fc2a1656c388/pybind11-2.13.6-py3-none-any.whl', '237c41e29157b962835d356b370ededd57594a26d5894a795960f0047cb5caf5'),
    'abseil-20240116.2.tar.gz': ('https://codeload.github.com/abseil/abseil-cpp/tar.gz/refs/tags/20240116.2', '733726b8c3a6d39a4120d7e45ea8b41a434cdacde401cba500f14236c49b39dc'),
}
SOURCES = {
    'g12_next': (31431, '57a03f3cc6fafb0bbf5d1f333b18188b35720a69693519b5e955a8656507c09a'),
    'g12_p1_cache': (34044, '3ae79dfef498306b87bfc536be919d8a54b58313b8f9647b86793d7840e1d90a'),
    'g12_p1_packed': (32084, 'f3b31a0703d130372e84b53ee7b05ab37b7a40fcf3856f6be5b45b7dfedfdb0b'),
}
AUXILIARY = {
    'g11_rules_embed.h': (10159, '870b64c0253be86ef139d0c2437d202d9d4f10097e871dd8bde526402dd49353'),
    'pokerid_rules.py': (10318, '456225cf675a1b8ecf9ac7b16b7e3b6185900fe3dea75fe8f1687ad12354ea5a'),
    'g12_p1_packed_live_backend.py': (7749, '9d166dfbd0d9da199585de631788e03636c295f595d568451239f0c0e652da52'),
}
FLAGS = ['-O2', '-std=c++20', '-fno-fast-math', '-ffp-contract=off', '-fPIC', '-shared']


def decode(name):
    raw = zlib.decompress(base64.b64decode((SOURCE / 'compressed' / (name + '.zlib.b64')).read_text('ascii').strip(), validate=True))
    if name in AUXILIARY:
        size, digest = AUXILIARY[name]
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest: raise ValueError('auxiliary source mismatch: ' + name)
    return raw


def build(work, compiler):
    work = work.resolve()
    if work == ROOT or work.is_relative_to(ROOT):
        raise ValueError('work-root must be outside repository to protect source artifacts')
    # Fresh root avoids overwriting another build, dependency archive or checkpoint.
    work.mkdir(parents=True, exist_ok=False)
    deps = work / 'dependencies'; deps.mkdir()
    for name, (url, digest) in PINS.items():
        path = deps / name
        with urllib.request.urlopen(url, timeout=60) as response: path.write_bytes(response.read())
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('dependency SHA mismatch: ' + name)
    with zipfile.ZipFile(deps / 'pybind11-2.13.6-py3-none-any.whl') as archive:
        if any(Path(name).is_absolute() or '..' in Path(name).parts for name in archive.namelist()):
            raise ValueError('unsafe wheel member')
        archive.extractall(deps / 'pybind11')
    with tarfile.open(deps / 'abseil-20240116.2.tar.gz') as archive:
        archive.extractall(deps, filter='data')
    abseil = deps / 'abseil-cpp-20240116.2'
    compiler_info = subprocess.check_output([compiler, '--version'], text=True).splitlines()[0]
    manifest = {'environment': 'RECONSTRUCTED, NOT original G11 vendor/ABI validation',
                'pins': {name: {'url': url, 'sha256': digest} for name, (url, digest) in PINS.items()},
                'compiler': compiler_info, 'flags': FLAGS, 'python': sys.version,
                'abi': sysconfig.get_config_var('SOABI'), 'platform': platform.platform(), 'variants': {}}
    (work / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    for variant, (size, digest) in SOURCES.items():
        out = work / variant; out.mkdir()
        raw = decode(variant + '_solver_disk.cc')
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest: raise ValueError('source mismatch')
        (out / 'g12_solver_disk.cc').write_bytes(raw)
        for name in ('g11_native_state.h', 'g12_numeric.h'):
            shutil.copyfile(SOURCE / 'g12_next' / name, out / name)
        (out / 'g11_rules_embed.h').write_bytes(decode('g11_rules_embed.h'))
        (out / 'pokerid_rules.py').write_bytes(decode('pokerid_rules.py'))
        patched = out / 'patched'; (patched / 'open_spiel').mkdir(parents=True)
        (patched / 'open_spiel/abseil-cpp').symlink_to(abseil, target_is_directory=True)
        cmd = [compiler] + FLAGS + [str(out / 'g12_solver_disk.cc'), str(abseil / 'absl/random/discrete_distribution.cc'),
              '-I' + str(deps / 'pybind11/pybind11/include'), '-I' + str(patched), '-I' + str(abseil),
              '-I' + sysconfig.get_paths()['include'], '-o', str(out / ('pokerid_g12' + sysconfig.get_config_var('EXT_SUFFIX')))]
        if sys.platform == 'darwin': cmd += ['-undefined', 'dynamic_lookup']
        result = subprocess.run(cmd, capture_output=True, text=True)
        (out / 'build.log').write_text(result.stdout + result.stderr)
        state = {'source_sha256': digest, 'source_bytes': size, 'build_command': cmd, 'build_returncode': result.returncode}
        manifest['variants'][variant] = state
        if result.returncode == 0:
            backend = out / 'backend.py'
            if variant == 'g12_next': shutil.copyfile(SOURCE / 'g12_next/g12_p1_live_backend.py', backend)
            else: backend.write_bytes(decode('g12_p1_packed_live_backend.py'))
            smoke = subprocess.run([sys.executable, '-B', str(ROOT / 'gto/native/smoke.py'), '--module-dir', str(out), '--backend', str(backend)], capture_output=True, text=True)
            (out / 'smoke.log').write_text(smoke.stdout + smoke.stderr)
            state['smoke_returncode'] = smoke.returncode
            if smoke.returncode == 0: state['smoke'] = json.loads(smoke.stdout)
        (work / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        print(json.dumps({'variant': variant, 'build_returncode': state['build_returncode'],
              'smoke_returncode': state.get('smoke_returncode'), 'checkpoint_sha256': state.get('smoke', {}).get('checkpoint_sha256'),
              'native_poker_cases': state.get('smoke', {}).get('native_poker_matrix', {}).get('case_count')}), flush=True)
    if not all(v['build_returncode'] == 0 and v.get('smoke_returncode') == 0 for v in manifest['variants'].values()):
        raise RuntimeError('native build/smoke failure; inspect manifest/logs')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--work-root', required=True, type=Path)
    parser.add_argument('--compiler', default='c++')
    args = parser.parse_args()
    build(args.work_root, args.compiler)
