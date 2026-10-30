import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync,readFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
const m=JSON.parse(readFileSync('docs/qa/selected-abd-20261026/source-manifest.json','utf8'))
const chrome=process.env.CHROMIUM_PATH || ['/usr/bin/chromium','/usr/bin/google-chrome'].find(existsSync)
assert(chrome,'supported Chromium installation required')
for(const suite of m.browser_suites) test('selected browser boundary: '+suite,{timeout:125000},()=>{
 const r=spawnSync(process.execPath,[suite],{cwd:process.cwd(),env:{...process.env,CHROMIUM_PATH:chrome},encoding:'utf8',timeout:120000,maxBuffer:8*1024*1024})
 assert.equal(r.error,undefined,'bounded child completed')
 assert.equal(r.status,0,r.stdout+r.stderr)
 assert.match(r.stdout,/(?:ℹ tests [1-9][0-9]*|"verdict":"PASS")/,'nonzero actual test execution required')
 console.log('CHILD '+suite+'\n'+r.stdout)
})
