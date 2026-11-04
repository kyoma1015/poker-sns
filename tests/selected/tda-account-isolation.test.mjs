import test from 'node:test'
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'

test('account-scoped real React quiz isolates delayed requests, writes, results and history', {timeout:35000}, () => {
  const result = spawnSync(process.execPath, ['tests/browser/tda-account-isolation.mjs'], {
    cwd:process.cwd(),encoding:'utf8',timeout:32000,
  })
  assert.equal(result.error,undefined,'bounded local browser must exit')
  assert.equal(result.status,0,result.stdout+result.stderr)
  const reports=result.stdout.split('\n').filter(line=>line.startsWith('{')).map(line=>JSON.parse(line))
  assert.equal(reports.at(-1)?.verdict,'PASS')
  assert.equal(reports.at(-1)?.tests,9)
})
