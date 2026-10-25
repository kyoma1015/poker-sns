import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, lstatSync } from 'node:fs'

const config = JSON.parse(readFileSync(new URL('../vercel.json', import.meta.url), 'utf8'))
const finalize = readFileSync(new URL('../api/video-finalize.ts', import.meta.url), 'utf8')
const bundler = readFileSync(new URL('../scripts/bundle-ffprobe.mjs', import.meta.url), 'utf8')
const packageJson = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'))

test('Hobby serverless function budget cannot regress', () => {
  const entries = readdirSync(new URL('../api/', import.meta.url)).filter(name => (name.endsWith('.ts') || name.endsWith('.js')) && !lstatSync(new URL(`../api/${name}`, import.meta.url)).isSymbolicLink())
  assert.ok(entries.length <= 12, `Hobby supports at most 12 API functions, found ${entries.length}`)
  assert.ok(!entries.includes('video-runtime-attestation.ts'))
  assert.ok(!Object.keys(config.functions || {}).some(path => path.includes('runtime-attestation')))
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
  assert.ok(bundler.includes('chmodSync(target, 0o755)'))
  assert.ok(bundler.includes("spawnSync(target, ['-version']"))
  assert.equal(config.functions['api/video-finalize.ts'].includeFiles, 'api/bin/ffprobe')
})
