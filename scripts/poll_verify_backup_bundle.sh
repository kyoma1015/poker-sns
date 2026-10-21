#!/usr/bin/env bash
set -euo pipefail
umask 077
fail() { printf 'Backup verification failed: %s\n' "$1" >&2; exit 2; }
[[ $# == 1 ]] || fail 'specify private bundle directory'
[[ -d "$1" && ! -L "$1" ]] || fail 'bundle directory missing/symlink'
dir=$(cd "$1" && pwd -P)
mode=$(stat -c %a "$dir" 2>/dev/null || stat -f %Lp "$dir" 2>/dev/null || echo unknown)
[[ "$mode" == 700 ]] || fail 'bundle directory permissions are not 0700'
for f in roles.sql schema.sql data.sql checksums.sha256; do
  [[ -f "$dir/$f" && ! -L "$dir/$f" && -s "$dir/$f" ]] || fail 'missing, empty or symlinked file'
  file_mode=$(stat -c %a "$dir/$f" 2>/dev/null || stat -f %Lp "$dir/$f" 2>/dev/null || echo unknown)
  [[ "$file_mode" == 600 ]] || fail 'bundle file permissions are not 0600'
done
if command -v shasum >/dev/null 2>&1; then
  (cd "$dir" && shasum -a 256 -c checksums.sha256 >/dev/null) || fail 'SHA256 mismatch'
elif command -v sha256sum >/dev/null 2>&1; then
  (cd "$dir" && sha256sum -c checksums.sha256 >/dev/null) || fail 'SHA256 mismatch'
else
  fail 'SHA256 tool missing'
fi
echo 'PASS: private export integrity verified (checksums only; restoration NOT verified)'
