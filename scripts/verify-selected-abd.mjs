import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
const m=JSON.parse(readFileSync('docs/qa/selected-abd-20261026/source-manifest.json','utf8'))
const hash=b=>createHash('sha1').update(Buffer.from('blob '+b.length+'\0')).update(b).digest('hex')
for(const row of m.sources){
 const actual=readFileSync(row.target_path)
 if(!row.adaptation || row.adaptation==='byte-identical rename') assert.equal(hash(actual),row.source_blob,row.target_path)
 else {
  const source=execFileSync('git',['show',row.source_commit+':'+row.source_path],{encoding:'utf8'})
  const expected=source.replace(/new URL\('\.\.\/',\s*import\.meta\.url\)/g,"new URL('../../', import.meta.url)").replace(/import\('\.\.\/src\//g,"import('../../src/")
  assert.equal(actual.toString(),expected,row.target_path+' only relocation edits allowed')
 }
}
for(const row of m.protected_main_blobs) assert.equal(hash(readFileSync(row.path)),row.sha,row.path+' must retain main bytes')
const allowed=new Set([...m.sources.map(r=>r.target_path),'scripts/verify-selected-abd.mjs','scripts/run-selected-abd.mjs','tests/selected-browser.test.mjs','.github/workflows/selected-abd.yml','docs/qa/selected-abd-20261026/source-manifest.json','docs/workers/SELECTED_ABD_INTEGRATION_20261026.md'])
for(const path of execFileSync('git',['diff','--name-only',m.base_main,'HEAD'],{encoding:'utf8'}).trim().split('\n').filter(Boolean)) assert(allowed.has(path),'unreviewed diff '+path)
assert(!m.sources.some(r=>/gto/i.test(r.target_path)))
console.log(JSON.stringify({status:'PASS',source_files:m.sources.length,protected_files:m.protected_main_blobs.length,gto:'EXCLUDED',sql:'UNCHANGED',base:m.base_main}))
