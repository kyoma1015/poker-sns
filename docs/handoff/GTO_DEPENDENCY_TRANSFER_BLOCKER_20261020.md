# GTO-HANDOFF-11 transfer boundary (2026-10-20)

Status: **BLOCKED; do not attempt C++ build or claim dependencies received.**

The sender has locally verified a ZIP at `/mnt/data/PokerID_GTO_G11_VENDORED_DEPENDENCIES_20261020.zip`, about 3.4 MB, containing 1,588 vendored source files and `SOURCE_SHA256.csv` and `README.txt` (1,590 ZIP entries). This sender-local path is **not accessible to Codex**. Two Codex attachment attempts did not mount the ZIP. The ZIP **has not been uploaded to GitHub**. A GitHub tree scan at commit `9cfc29e71394ce4e07aab5e952cd1188cce372ff` confirmed its absence.

The current assistant's container cannot resolve github.com for direct Git operations. GitHub connector can write UTF-8 text files, but cannot read the container-local binary ZIP or stream its bytes to GitHub. **No successful cross-environment binary transfer has been established.**

Do not assume `/mnt/data` is mounted in Codex. Do not repeat GTO-HANDOFF-11 until actual GitHub blob/path or other independently readable source is verified. Do not install substitute versions and call the result an original-environment reproduction.

Known original build script: `handoff/gto/build_original/g12_p1_cache/build.sh`. The original packed backend is already transferred as `handoff/gto/compressed/g12_p1_packed_live_backend.py.zlib.b64`, verified independently in GTO-HANDOFF-09 and passed 25 temporary SQLite tests in GTO-HANDOFF-10.

Next dependency task is **transfer**, not further testing. No changes to main, Supabase, production, or historical checkpoints.
