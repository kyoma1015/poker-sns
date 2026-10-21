// Immutable input acceptance: actual React UI with synthetic deferred transport.
import assert from 'node:assert/strict'
import test from 'node:test'
import path from 'node:path'
import os from 'node:os'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import { chromium } from 'playwright-core'
const root = fileURLToPath(new URL('../', import.meta.url))
async function withPage(fn) {
  const cache = await fs.mkdtemp(path.join(os.tmpdir(), 'pokerid-search-acceptance-'))
  const server = await createServer({ root, cacheDir: cache, configFile: false,
    server: { host: '127.0.0.1', port: 0 }, esbuild: { jsx: 'automatic' },
    plugins: [{ name: 'synthetic-search', enforce: 'pre', resolveId(source, importer) {
      if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/tda-search-supabase.ts')
    }, configureServer(server) { server.middlewares.use('/__search', (_req,res) => {
      res.setHeader('Content-Type','text/html');res.end('<div id="root"></div><script type="module" src="/tests/browser/tda-entry.tsx"></script>')
    }) } }] })
  let browser
  try {
    await server.listen()
    const base = `http://127.0.0.1:${server.httpServer.address().port}`
    browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
    const page = await browser.newPage({ viewport: { width:390,height:844 } })
    page.on('pageerror', () => {}) // Rejections must be checked through visible recovery below.
    await page.route('**/*',route=>route.request().url().startsWith(base+'/')?route.continue():route.abort())
    await page.goto(base+'/__search')
    await fn(page, page.getByPlaceholder('例：ワンチップ、ショーダウン順、体臭...'))
  } finally { await browser?.close();await server.close();await fs.rm(cache,{recursive:true,force:true}) }
}
const waitCalls = (p,n) => p.waitForFunction(n=>window.tdaSearchQA.calls.length===n,n,{timeout:2000})
const resolve = (p,index,label) => p.evaluate(({index,label})=>window.tdaSearchQA.resolve(index,label),{index,label})
const titles = p => p.locator('.tda-rule-card h3').allTextContents()
const tick = p => p.waitForTimeout(80)
test('latest request wins even when older search resolves last',()=>withPage(async(p,input)=>{
  await input.fill('alpha');await waitCalls(p,1);await input.fill('beta');await waitCalls(p,2)
  await resolve(p,1,'synthetic beta');await tick(p);await resolve(p,0,'synthetic alpha');await tick(p)
  assert.deepEqual(await titles(p),['synthetic beta'])
}))
test('new input invalidates an old response before debounce expires',()=>withPage(async(p,input)=>{
  await input.fill('alpha');await waitCalls(p,1);await input.fill('beta');await resolve(p,0,'synthetic alpha');await tick(p)
  assert.deepEqual(await titles(p),[])
}))
test('clearing search prevents late result resurrection and ends loading',()=>withPage(async(p,input)=>{
  await input.fill('alpha');await waitCalls(p,1);await input.fill('');await p.waitForTimeout(400)
  await resolve(p,0,'synthetic alpha');await tick(p)
  assert.deepEqual(await titles(p),[]);assert.equal(await p.getByText('検索しています...', {exact:true}).count(),0)
}))
test('thrown transport ends loading and permits next search recovery',()=>withPage(async(p,input)=>{
  await input.fill('alpha');await waitCalls(p,1);await p.evaluate(()=>window.tdaSearchQA.reject(0));await tick(p)
  assert.equal(await p.getByText('検索しています...', {exact:true}).count(),0)
  assert.match(await p.locator('body').innerText(),/検索.*(エラー|失敗|通信)/)
  await input.fill('beta');await waitCalls(p,2);await resolve(p,1,'synthetic recovered');await tick(p)
  assert.deepEqual(await titles(p),['synthetic recovered'])
}))
test('old failed request cannot end newer request loading or show stale error',()=>withPage(async(p,input)=>{
  await input.fill('alpha');await waitCalls(p,1);await input.fill('beta');await waitCalls(p,2)
  await p.evaluate(()=>window.tdaSearchQA.fail(0));await tick(p)
  assert.equal(await p.getByText('検索しています...', {exact:true}).count(),1)
  assert.equal(await p.getByText('検索中にエラーが発生しました。',{exact:true}).count(),0)
  await resolve(p,1,'synthetic beta');await tick(p);assert.deepEqual(await titles(p),['synthetic beta'])
}))

for (const [name,data] of [
  ['non-array payload', { unexpected: true }],
  ['null rule row', [null]],
  ['invalid title value', [{ rule_number: 1, title_ja: { internal: 'synthetic marker' } }]],
  ['invalid rule number', [{ rule_number: '1', title_ja: 'synthetic invalid number' }]],
]) test(`malformed search ${name} fails closed and permits retry`,()=>withPage(async(p,input)=>{
  await input.fill('alpha');await waitCalls(p,1)
  await p.evaluate(data=>window.tdaSearchQA.resolveRaw(0,data),data);await tick(p)
  assert.match(await p.locator('body').innerText(),/検索.*(エラー|失敗|通信)/)
  assert.equal(await p.getByText('検索しています...', {exact:true}).count(),0)
  assert.equal(await p.getByPlaceholder('例：ワンチップ、ショーダウン順、体臭...').count(),1)
  assert.deepEqual(await titles(p),[])
  await input.fill('beta');await waitCalls(p,2);await resolve(p,1,'synthetic recovered');await tick(p)
  assert.deepEqual(await titles(p),['synthetic recovered'])
}))
