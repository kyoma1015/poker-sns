"""Read-only G12 integrity preflight. Does not establish historical compatibility.

The legacy C++ loader consumes a 32-byte trailer but does not verify its digest.
Use a verified temporary snapshot before calling that loader. SHA-256 detects
accidental corruption; it does not authenticate an untrusted sender.
"""
from contextlib import contextmanager
import hashlib
import math
from pathlib import Path
import struct
import tempfile


@contextmanager
def verified_snapshot(source, expected_contract, *, max_bytes=4 * 1024**3):
    """Copy/hash once, check the complete snapshot, then expose only that copy."""
    source = Path(source)
    with tempfile.TemporaryDirectory(prefix='pokerid-checkpoint-verified-') as directory:
        snapshot = Path(directory) / 'checkpoint.bin'
        digest = hashlib.sha256()
        tail = b''
        total = 0
        with source.open('rb') as original, snapshot.open('xb') as target:
            while chunk := original.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError('checkpoint size limit exceeded')
                target.write(chunk)
                combined = tail + chunk
                if len(combined) > 32:
                    digest.update(combined[:-32])
                tail = combined[-32:]
        if total < 40 or len(tail) != 32 or digest.digest() != tail:
            raise ValueError('checkpoint SHA-256 trailer mismatch')
        with snapshot.open('rb') as stream:
            def read(size):
                raw = stream.read(size)
                if len(raw) != size or stream.tell() > total - 32:
                    raise ValueError('truncated checkpoint header')
                return raw
            def uint():
                return struct.unpack('<Q', read(8))[0]
            def real():
                return struct.unpack('<d', read(8))[0]
            def text(limit):
                size = uint()
                if size > limit:
                    raise ValueError('checkpoint string limit exceeded')
                return read(size).decode('utf-8')
            if read(8) != b'PIDG12S1':
                raise ValueError('unsupported checkpoint magic')
            contract = text(1024 * 1024)
            if contract != expected_contract:
                raise ValueError('checkpoint contract mismatch')
            flags = [uint() for _ in range(5)]
            if any(flag not in (0, 1) for flag in flags) or flags[4] != 1:
                raise ValueError('invalid/unsupported G12 solver flags')
            alpha = real()
            iteration, visits = uint(), uint()
            epsilon = real()
            rng = text(20000)
            rows = uint()
            if not all(math.isfinite(x) and 0 < x <= 1 for x in (alpha, epsilon)):
                raise ValueError('invalid checkpoint alpha/epsilon')
            if rows > 1000000 or not rng:
                raise ValueError('invalid checkpoint row count/RNG')
        metadata = {'contract': contract, 'iteration': iteration, 'visits': visits,
                    'rows': rows, 'bytes': total, 'sha256_payload': digest.hexdigest()}
        yield snapshot, metadata


def load_verified_checkpoint(solver, source, expected_contract, *, max_bytes=4 * 1024**3):
    """Preflight digest/header, then let native loader validate modes and rows."""
    with verified_snapshot(source, expected_contract, max_bytes=max_bytes) as (snapshot, metadata):
        solver.load_binary(str(snapshot), expected_contract)
        return metadata
