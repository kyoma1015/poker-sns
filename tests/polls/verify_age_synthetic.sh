#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
export LC_ALL=C
command -v age >/dev/null
command -v age-keygen >/dev/null
command -v shasum >/dev/null || command -v sha256sum >/dev/null
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -m 700 "$work/keys" "$work/data" "$work/offsite"
age-keygen -o "$work/keys/primary.key" 2>"$work/keygen.log"
age-keygen -o "$work/keys/wrong.key" 2>"$work/wrong-keygen.log"
age-keygen -y "$work/keys/primary.key" > "$work/recipient.txt"
printf 'synthetic poker id test only\nno real identities\n' > "$work/data/plain.txt"
age -R "$work/recipient.txt" -o "$work/data/backup.age" "$work/data/plain.txt"
cp "$work/data/backup.age" "$work/offsite/backup.age"
cmp "$work/data/backup.age" "$work/offsite/backup.age"
age -d -i "$work/keys/primary.key" -o "$work/data/restored.txt" "$work/offsite/backup.age"
cmp "$work/data/plain.txt" "$work/data/restored.txt"
if command -v sha256sum >/dev/null; then
  original="$(sha256sum "$work/data/backup.age" | cut -d' ' -f1)"
  duplicate="$(sha256sum "$work/offsite/backup.age" | cut -d' ' -f1)"
else
  original="$(shasum -a 256 "$work/data/backup.age" | cut -d' ' -f1)"
  duplicate="$(shasum -a 256 "$work/offsite/backup.age" | cut -d' ' -f1)"
fi
test "$original" = "$duplicate"
test "$(stat -c '%a' "$work/keys/primary.key")" = "600"
test ! -e "$work/offsite/primary.key"
if age -d -i "$work/keys/wrong.key" -o "$work/data/wrong-output" "$work/data/backup.age" >"$work/wrong.stdout" 2>"$work/wrong.stderr"; then
  echo 'FAIL: wrong key unexpectedly decrypted'; exit 1
fi
cp "$work/data/backup.age" "$work/data/tampered.age"
python3 - "$work/data/tampered.age" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
data = bytearray(p.read_bytes())
data[-8] ^= 1
p.write_bytes(data)
PY
if age -d -i "$work/keys/primary.key" -o "$work/data/tampered-output" "$work/data/tampered.age" >"$work/tampered.stdout" 2>"$work/tampered.stderr"; then
  echo 'FAIL: modified ciphertext unexpectedly decrypted'; exit 1
fi
if grep -aFq 'synthetic poker id test only' "$work/data/backup.age"; then
  echo 'FAIL: plaintext found in encrypted artifact'; exit 1
fi
if grep -aEq 'AGE-SECRET-KEY-|BEGIN (RSA|OPENSSH) PRIVATE KEY' "$work/offsite/backup.age"; then
  echo 'FAIL: key material in encrypted artifact'; exit 1
fi
echo 'PASS: synthetic key generation and recipient extraction'
echo 'PASS: age encryption and correct-key roundtrip'
echo 'PASS: encrypted offsite copy digest parity'
echo 'PASS: key permission and separation'
echo 'PASS: wrong-key rejection'
echo 'PASS: modified-ciphertext rejection'
echo 'PASS: ciphertext plaintext/key marker nonexposure'
echo 'SUMMARY PASS=7 FAIL=0 BLOCKED=0 (synthetic only; not production recovery)'
