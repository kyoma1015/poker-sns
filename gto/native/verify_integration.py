"""Install-free isolated bridge verification, not G11 ABI or strategy proof."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from gto.native.settlement import build_and_run

WHEEL_SHA256 = '237c41e29157b962835d356b370ededd57594a26d5894a795960f0047cb5caf5'
PAYLOADS = {
    'pokerid_rules.py': (10318, '456225cf675a1b8ecf9ac7b16b7e3b6185900fe3dea75fe8f1687ad12354ea5a'),
    'g11_rules_embed.h': (10159, '870b64c0253be86ef139d0c2437d202d9d4f10097e871dd8bde526402dd49353'),
}


def decoded_payload(name, expected_size, expected_sha):
    path = ROOT / 'handoff/gto/compressed' / (name + '.zlib.b64')
    packed = base64.b64decode(path.read_text('ascii').strip(), validate=True)
    decoder = zlib.decompressobj()
    raw = decoder.decompress(packed, expected_size + 1)
    if (len(raw) != expected_size or not decoder.eof or decoder.unused_data
            or decoder.unconsumed_tail or hashlib.sha256(raw).hexdigest() != expected_sha):
        raise ValueError('transferred payload size/hash/stream mismatch: ' + name)
    return raw


def extract_headers(wheel, destination):
    if wheel.is_symlink() or not wheel.is_file() or wheel.stat().st_size > 1024 * 1024:
        raise ValueError('bounded regular pybind11 wheel required')
    with wheel.open('rb') as stream:
        raw = stream.read(1024 * 1024 + 1)
    if hashlib.sha256(raw).hexdigest() != WHEEL_SHA256:
        raise ValueError('pinned pybind11 wheel SHA-256 mismatch')
    count = total = 0
    # Extract the exact already-hashed bytes, not a second read of a mutable path.
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            if (path.is_absolute() or '..' in path.parts or '\\' in member.filename
                    or stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError('unsafe wheel entry')
            if member.is_dir() or not member.filename.startswith('pybind11/include/'):
                continue
            total += member.file_size
            count += 1
            if count > 1000 or total > 16 * 1024 * 1024:
                raise ValueError('header extraction limit exceeded')
            target = destination.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
    if not (destination / 'pybind11/include/pybind11/pybind11.h').is_file():
        raise ValueError('pinned wheel missing pybind11 header')
    return {'wheel_sha256': WHEEL_SHA256, 'headers': count}


def verify(wheel, compiler='c++'):
    payloads = {name: decoded_payload(name, *expected) for name, expected in PAYLOADS.items()}
    with tempfile.TemporaryDirectory(prefix='pokerid-gto-integration-') as directory:
        native_root = Path(directory)
        # All build products and extracted dependencies remain outside the repository.
        headers = extract_headers(wheel, native_root / 'dependencies/pybind11')
        include = native_root / 'g12_next'
        include.mkdir()
        (include / 'g11_rules_embed.h').write_bytes(payloads['g11_rules_embed.h'])
        result = build_and_run(native_root, compiler)
        return {
            'status': result['status'],
            'settlement_cases': result['case_count'],
            'rank7_status': result['rank7']['status'],
            'rank7_cases': result['rank7']['case_count'],
            'all_native_compared': all(row['native_compared'] for row in
                                      result['results'] + result['rank7']['results']),
            'reference_payloads': {name: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
                                   for name, raw in payloads.items()},
            'dependency': headers,
            'test_only_bridge': True,
            'three_solver_rebuild': False,
            'historical_baseline_used': False,
            'strategy_convergence_proof': False,
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--compiler', default='c++')
    args = parser.parse_args()
    print(json.dumps(verify(args.wheel, args.compiler), indent=2))
