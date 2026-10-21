import assert from 'node:assert/strict';
import { chmodSync, mkdtempSync, mkdirSync, readdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

const base = mkdtempSync(join(tmpdir(), 'poker-export-atomic-'));
const bin = join(base, 'bin');
const backups = join(base, 'backup');
try {
  mkdirSync(bin, { mode: 0o700 });
  mkdirSync(backups, { mode: 0o700 });
  chmodSync(backups, 0o700);
  const fakeCli = join(bin, 'supabase');
  writeFileSync(fakeCli, [
    '#!/usr/bin/env bash',
    'set -euo pipefail',
    'dest=""',
    'for ((i=1;i<=$#;i++)); do if [[ "${!i}" == -f ]]; then j=$((i+1)); dest="${!j}"; fi; done',
    '[[ -n "$dest" ]] || exit 44',
    'printf "%s\\n" "synthetic-only SQL contents" > "$dest"',
    'if [[ "${SIMULATE_DUMP_FAILURE:-}" == true && "$dest" == */schema.sql ]]; then exit 72; fi',
  ].join('\n') + '\n', { mode: 0o700 });
  chmodSync(fakeCli, 0o700);
  const env = {
    ...process.env, CI: '', GITHUB_ACTIONS: '',
    PATH: bin + ':' + process.env.PATH,
    POLL_BACKUP_DIR: backups,
    SUPABASE_DB_URL: 'postgres://synthetic:synthetic@localhost/postgres?sslmode=require',
  };
  const run = (overrides = {}) => spawnSync('bash', ['scripts/poll_private_export.sh'], { env: { ...env, ...overrides }, encoding: 'utf8' });
  const failure = run({ SIMULATE_DUMP_FAILURE: 'true' });
  assert.notEqual(failure.status, 0, 'failed export should fail');
  assert.deepEqual(readdirSync(backups), [], 'failed export must discard the new partial bundle');
  const success = run();
  assert.equal(success.status, 0, success.stderr);
  assert.match(success.stdout, /integrity verified/);
  assert.equal(readdirSync(backups).length, 1, 'successful export retains exactly one private bundle');
  console.log('PASS private export atomicity: partial cleanup, checksum gate, valid bundle retained (synthetic CLI)');
} finally {
  rmSync(base, { recursive: true, force: true });
}
