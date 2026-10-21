import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, chmodSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const script = 'scripts/poll_verify_backup_bundle.sh';
const syntax = spawnSync('bash', ['-n', script], { encoding: 'utf8' });
assert.equal(syntax.status, 0, syntax.stderr);
const directory = mkdtempSync(join(tmpdir(), 'poker-backup-check-'));
try {
  chmodSync(directory, 0o700);
  const files = ['roles.sql', 'schema.sql', 'data.sql'];
  const hashes = [];
  for (const name of files) {
    const value = '-- synthetic-only ' + name + '\n';
    writeFileSync(join(directory, name), value, { mode: 0o600 });
    chmodSync(join(directory, name), 0o600);
    hashes.push(createHash('sha256').update(value).digest('hex') + '  ' + name);
  }
  writeFileSync(join(directory, 'checksums.sha256'), hashes.join('\n') + '\n', { mode: 0o600 });
  chmodSync(join(directory, 'checksums.sha256'), 0o600);
  const run = () => spawnSync('bash', [script, directory], { encoding: 'utf8' });
  assert.equal(run().status, 0, 'valid private archive must pass checksum verification');
  writeFileSync(join(directory, 'data.sql'), '-- intentionally corrupted synthetic bytes\n', { mode: 0o600 });
  assert.notEqual(run().status, 0, 'tampered archive must be rejected');
  console.log('PASS private export SHA256 detects synthetic corruption and accepts intact restricted bundle');
} finally {
  rmSync(directory, { recursive: true, force: true });
}
