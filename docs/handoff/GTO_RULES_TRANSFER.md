# GTO handoff: Rules dependency direct transfer (2026-10-20)

This file is not a claim of complete GTO solver migration.

Source: `source/g12_next/pokerid_rules.py` from `PokerID_GTO_G12_NATIVE_SOURCE_TRANSFER_20261020.zip`.
Byte-exact compressed/base64 payload has been committed as `handoff/gto/compressed/pokerid_rules.py.zlib.b64`.

- Original size: **10318 bytes**
- Expected original SHA-256: `456225cf675a1b8ecf9ac7b16b7e3b6185900fe3dea75fe8f1687ad12354ea5a`
- Encoded size: **4528 characters**
- Git blob SHA after GitHub fetch: `fdb6c7ec20f4d77a9169c4aa4a97ae5399679b84`

## Codex read-only verification

From repository root, run:
```sh
python - <<'PY'
from pathlib import Path
import base64,zlib,hashlib
p=Path('handoff/gto/compressed/pokerid_rules.py.zlib.b64')
decoded=zlib.decompress(base64.b64decode(p.read_text().strip(),validate=True))
expected='456225cf675a1b8ecf9ac7b16b7e3b6185900fe3dea75fe8f1687ad12354ea5a'
actual=hashlib.sha256(decoded).hexdigest()
print('bytes',len(decoded),'SHA256',actual)
assert len(decoded)==10318 and actual==expected
print('PASS')
PY
```

Do not mark the source verified by Codex before actually running this. GTO core solvers and checkpoint remain not transferred.
