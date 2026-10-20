"""Byte-check transferred artifacts; exercise backend only in temporary SQLite."""
import base64
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zlib

BASE = Path(__file__).resolve().parents[1]
EXPECTED = {
    'g11_rules_embed.h': (10159, '870b64c0253be86ef139d0c2437d202d9d4f10097e871dd8bde526402dd49353'),
    'pokerid_rules.py': (10318, '456225cf675a1b8ecf9ac7b16b7e3b6185900fe3dea75fe8f1687ad12354ea5a'),
    'g12_p1_packed_live_backend.py': (7749, '9d166dfbd0d9da199585de631788e03636c295f595d568451239f0c0e652da52'),
}
raw_files = {}
for name, (size, digest) in EXPECTED.items():
    encoded = (BASE / 'compressed' / (name + '.zlib.b64')).read_text('ascii').strip()
    raw = zlib.decompress(base64.b64decode(encoded, validate=True))
    assert len(raw) == size and hashlib.sha256(raw).hexdigest() == digest, name
    raw_files[name] = raw
    print('PASS', name, size, digest, flush=True)
with tempfile.TemporaryDirectory(prefix='pokerid-backend-qa-') as directory:
    root = Path(directory)
    (root / 'packed_backend.py').write_bytes(raw_files['g12_p1_packed_live_backend.py'])
    shutil.copyfile(BASE / 'tests' / 'test_commit_packed.py', root / 'test_commit_packed.py')
    subprocess.run([sys.executable, str(root / 'test_commit_packed.py')], check=True, cwd=root)
