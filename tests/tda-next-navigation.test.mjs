import test from 'node:test'
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
test('next-question transitions consume one answered generation without skipping or false scores', { timeout: 45000 }, () => {
  const chrome=process.env.CHROMIUM_PATH || ['/usr/bin/chromium','/usr/bin/google-chrome'].find(existsSync)
  assert(chrome,'supported Chromium required')
  const result = spawnSync(process.execPath, ['tests/browser/tda-next-navigation.mjs'], {
    cwd: process.cwd(),env:{...process.env,CHROMIUM_PATH:chrome},encoding:'utf8',timeout:40000,maxBuffer:2*1024*1024,
  })
  assert.equal(result.error,undefined,'bounded actual React browser must finish')
  assert.equal(result.status,0,result.stdout+result.stderr)
  const reports=result.stdout.split('\n').filter(line=>line.startsWith('{')).map(line=>JSON.parse(line))
  assert.equal(reports.at(-1)?.verdict,'PASS')
  assert.equal(reports.at(-1)?.tests,3)
  assert.equal(reports.at(-1)?.pass,3)
  assert.equal(reports.at(-1)?.fail,0)
  console.log(JSON.stringify({suite:'next-navigation',...reports.at(-1)}))
})
