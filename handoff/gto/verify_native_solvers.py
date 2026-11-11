"""Verify transferred GTO native solver versions from GitHub-checked-in payloads.

Run from repository root:
  python handoff/gto/verify_native_solvers.py

No source file writes, network calls, database access or production changes.
"""
import base64
import hashlib
from pathlib import Path
import zlib

BASE = Path(__file__).resolve().parent
SOURCES = {
    "g12_next": (31431, "57a03f3cc6fafb0bbf5d1f333b18188b35720a69693519b5e955a8656507c09a"),
    "g12_p1_cache": (34044, "3ae79dfef498306b87bfc536be919d8a54b58313b8f9647b86793d7840e1d90a"),
    "g12_p1_packed": (32084, "f3b31a0703d130372e84b53ee7b05ab37b7a40fcf3856f6be5b45b7dfedfdb0b"),
}

for variant, (expected_size, expected_hash) in SOURCES.items():
    encoded_file = BASE / "compressed" / (variant + "_solver_disk.cc.zlib.b64")
    payload = base64.b64decode(encoded_file.read_text(encoding="ascii").strip(), validate=True)
    raw = zlib.decompress(payload)
    actual = hashlib.sha256(raw).hexdigest()
    if len(raw) != expected_size or actual != expected_hash:
        raise RuntimeError(
            f"FAIL {variant}: bytes={len(raw)}, sha256={actual}; "
            f"expected bytes={expected_size}, sha256={expected_hash}"
        )
    print(f"PASS {variant}: {len(raw)} bytes; SHA-256={actual}")

print("PASS: all three G12 native solver variants are byte-verified")
