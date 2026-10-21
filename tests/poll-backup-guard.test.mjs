import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

const path = 'scripts/poll_private_export.sh';
const source = readFileSync(path, 'utf8');
const syntax = spawnSync('bash', ['-n', path], { encoding: 'utf8' });
assert.equal(syntax.status, 0, syntax.stderr);
assert.match(source, /supabase db dump.*--role-only/);
assert.match(source, /supabase db dump.*--use-copy --data-only/);
assert.match(source, /chmod 600/);
assert.doesNotMatch(source, /github\.com\/.*artifacts|gh release upload/i);
const guard = spawnSync('bash', [path], {
  env: { ...process.env, CI: 'true', GITHUB_ACTIONS: 'true', SUPABASE_DB_URL: 'postgres://secret:secret@example.com/postgres?sslmode=require' },
  encoding: 'utf8',
});
assert.equal(guard.status, 2);
assert.match(guard.stderr, /Production export prohibited in CI/);
assert.doesNotMatch(guard.stdout + guard.stderr, /secret/);
console.log('PASS private export guard: shell syntax, offline-only, role/schema/data, credential-safe CI refusal');
