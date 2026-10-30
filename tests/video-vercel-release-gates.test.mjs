import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, mkdtempSync, mkdirSync, writeFileSync, symlinkSync, rmSync } from 'node:fs'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
import {fileURLToPath} from 'node:url'
import {assertApiFunctionBudget,listApiFunctionSources} from '../scripts/video_api_function_budget.mjs'

const config = JSON.parse(readFileSync(new URL('../vercel.json', import.meta.url), 'utf8'))
const finalize = readFileSync(new URL('../api/video-finalize.ts', import.meta.url), 'utf8')
const bundler = readFileSync(new URL('../scripts/bundle-ffprobe.mjs', import.meta.url), 'utf8')
const packageJson = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'))

test('Hobby serverless function budget cannot regress', () => {
  const entries = assertApiFunctionBudget(fileURLToPath(new URL('../api/', import.meta.url)))
  assert.ok(entries.includes('og.mjs'),'existing MJS endpoint must count toward the same limit')
  assert.ok(!entries.includes('video-recovery-candidate.ts'),'internal recovery module must not be deployed as a separate function')
  assert.match(finalize,/from '\.\.\/server\/video-recovery-candidate\.js'/)
  assert.ok(!entries.includes('video-runtime-attestation.ts'))
  assert.ok(!Object.keys(config.functions || {}).some(path => path.includes('runtime-attestation')))
})

test('function inventory catches MJS overflow, nested endpoints and CJS without counting declarations or QA aliases',()=>{
 const root=mkdtempSync(join(tmpdir(),'video-function-budget-'))
 try {
  for(let index=0;index<12;index++)writeFileSync(join(root,`handler${index}.ts`),'export default ()=>{}')
  writeFileSync(join(root,'og.mjs'),'export default ()=>{}')
  assert.throws(()=>assertApiFunctionBudget(root),/found 13/,'prior TS/JS-only check missed this exact production failure')
  rmSync(join(root,'handler11.ts'))
  writeFileSync(join(root,'types.d.ts'),'declare const a:string')
  symlinkSync('handler0.ts',join(root,'handler0.js'))
  assert.equal(assertApiFunctionBudget(root).length,12)
  mkdirSync(join(root,'nested'));writeFileSync(join(root,'nested','route.cjs'),'module.exports=()=>{}')
  assert.ok(listApiFunctionSources(root).includes(join('nested','route.cjs')))
  assert.throws(()=>assertApiFunctionBudget(root),/found 13/)
 } finally {rmSync(root,{recursive:true,force:true})}
})

test('ffprobe runtime attestation shares finalize function and stays preview-only', () => {
  assert.ok(config.rewrites.some(rule => rule.source === '/internal/video/runtime-attestation' && rule.destination.includes('/api/video-finalize?runtime_attestation=ffprobe')))
  assert.ok(finalize.includes("process.env.VERCEL_ENV !== 'preview'"))
  assert.ok(finalize.includes("spawn(executable, ['-version']"))
  assert.ok(finalize.includes('return res.status(404).end()'))
})

test('build requires SHA256-pinned executable and Vercel function inclusion', () => {
  assert.equal(packageJson.scripts.prebuild, 'node scripts/bundle-ffprobe.mjs')
  assert.match(bundler, /const sha256 = '[a-f0-9]{64}'/)
  assert.match(bundler, /digest !== sha256/)
  assert.ok(bundler.includes('chmodSync(staged, 0o755)'))
  assert.ok(bundler.includes("spawnSync(staged, ['-version']"))
  assert.ok(bundler.includes('renameSync(staged, target)'))
  assert.ok(bundler.includes('rmSync(staged, { force: true })'))
  assert.equal(config.functions['api/video-finalize.ts'].includeFiles, 'api/bin/ffprobe')
})
