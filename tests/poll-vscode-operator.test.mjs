import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
for (const path of ['scripts/poll_backup_vscode.sh','scripts/poll_restore_local_only.sh']) {
  const syntax = spawnSync('bash',['-n',path],{encoding:'utf8'});
  assert.equal(syntax.status,0,syntax.stderr);
  const source=readFileSync(path,'utf8');
  assert.match(source,/GITHUB_ACTIONS/);
  assert.match(source,/\[\[ -t 0 && -t 1 \]\]/);
  const refusal=spawnSync('bash',[path],{encoding:'utf8',env:{...process.env,CI:'true',GITHUB_ACTIONS:'true'}});
  assert.equal(refusal.status,2,`CI refusal failed for ${path}`);
  assert.doesNotMatch(refusal.stdout+refusal.stderr,/password|postgres:\/\/.*@/i);
}
const wizard=readFileSync('scripts/poll_backup_vscode.sh','utf8');
assert.match(wizard,/read -r -s -p/);
assert.match(wizard,/ephptepeuespnxtzdqby/);
assert.match(wizard,/poll_private_export\.sh/);
const restore=readFileSync('scripts/poll_restore_local_only.sh','utf8');
assert.match(restore,/127\.0\.0\.1/);
assert.match(restore,/RESTORE ISOLATED/);
assert.match(restore,/--single-transaction/);
assert.match(restore,/poll_verify_backup_bundle\.sh/);
console.log('PASS VS Code interactive export/restore entrypoints: CI refusal, hidden input and localhost restore restriction');
