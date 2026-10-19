# GTO dependency source transfer — GitHub-native route

2026-10-20: The 10,159-byte G11 dependency `g11_rules_embed.h` is now present as compressed Base64 source bytes in `handoff/gto/compressed/g11_rules_embed.h.zlib.b64`. This is not merely a hash ledger.

Original file: `source/g12_next/g11_rules_embed.h` inside 69 KB native-source ZIP.
Expected uncompressed SHA-256: `870b64c0253be86ef139d0c2437d202d9d4f10097e871dd8bde526402dd49353`.

## Read-only Codex verification

Run these commands in an **isolated temporary directory** (do not overlay repository app source):

```sh
python - <<'PY'
from pathlib import Path
import base64, hashlib, zlib
p=Path('handoff/gto/compressed/g11_rules_embed.h.zlib.b64')
raw=zlib.decompress(base64.b64decode(p.read_text().strip(),validate=True))
sha=hashlib.sha256(raw).hexdigest()
expected='870b64c0253be86ef139d0c2437d202d9d4f10097e871dd8bde526402dd49353'
print('bytes:',len(raw),'sha256:',sha,'MATCH:',sha==expected)
assert len(raw)==10159 and sha==expected
PY
```

This confirms just **one** header was received; it does not unblock GTO solver compilation or restart. Main native solvers `g12_solver_disk.cc` and checkpoints are not yet in GitHub. Do not mark them transferred.

No main merges, prod writes, deployment or SQL.
