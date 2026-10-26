// Run with a separately installed playwright-core; browser never contacts a DB.
import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { createServer } from 'vite'
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright-core')
const root = fileURLToPath(new URL('../../', import.meta.url))
const server = await createServer({ root, configFile: false, server: { host: '127.0.0.1', port: 0 },
  plugins: [{ name: 'qa-only-supabase', enforce: 'pre', resolveId(source, importer) {
    if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/tda-account-supabase.ts')
  }, configureServer(server) { server.middlewares.use('/__qa', (req,res) => {
    res.setHeader('Content-Type', 'text/html'); res.end('<div id="root"></div><script type="module" src="/tests/browser/tda-account-entry.tsx"></script>')
  }) } }], esbuild: { jsx: 'automatic' } })
let browser
const results = []
try {
  await server.listen()
  const base = `http://127.0.0.1:${server.httpServer.address().port}`
  browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort())
  const failures = []
  page.setDefaultTimeout(1800)
  const check = async (name, fn) => { try { await fn(); results.push(name); console.log('PASS', name) } catch (error) { failures.push({name, message:error.message}); console.log('FAIL', name, error.message.split('\n')[0]) } }
  const openQuiz = async () => { await page.goto(base + '/__qa'); await page.getByRole('button', {name:/TDAクイズ/}).click() }
  const start = async () => { await page.getByRole('button', {name:'クイズを始める',exact:true}).click() }
  const answer = async () => { await page.getByRole('button', {name:'合成B',exact:false}).click() }
  const calls = async name => page.evaluate(name => window.tdaAccountQa.calls.filter(call=>call.name===name), name)
  const emit = async id => page.evaluate(id => window.tdaAccountQa.emit(id), id)
  const defer = async kind => page.evaluate(kind => window.tdaAccountQa.defer(kind), kind)
  const resolve = async kind => { await page.evaluate(kind => window.tdaAccountQa.resolve(kind), kind); await page.waitForTimeout(40) }
  await check('account change clears completed answer and history', async () => {
    await openQuiz(); await start(); await answer()
    await page.getByRole('button', {name:'結果を見る',exact:true}).click()
    await page.getByRole('heading', {name:'account-aの合成問題',exact:true}).waitFor()
    await emit('account-b')
    await page.waitForTimeout(40)
    assert.equal(await page.getByText('account-aの合成問題',{exact:true}).count(),0)
    assert.equal(await page.getByText('account-aの追加解説',{exact:true}).count(),0)
  })
  await check('delayed private wrong-question response is discarded after account change', async () => {
    await openQuiz(); await defer('questions')
    await page.getByRole('button', {name:'復習する',exact:true}).click()
    await page.waitForFunction(()=>window.tdaAccountQa.calls.some(call=>call.name==='get_my_wrong_tda_quiz_questions'))
    await emit('account-b'); await resolve('questions')
    assert.equal(await page.getByText('account-aの合成問題',{exact:true}).count(),0)
    await page.getByRole('button', {name:/TDAクイズ/}).click(); await start()
    await page.getByRole('heading',{name:'account-bの合成問題',exact:true}).waitFor()
  })
  await check('account change during answer auth refuses write after stale verified user', async () => {
    await openQuiz(); await start(); await defer('auth'); await answer()
    await emit('account-b'); await resolve('auth')
    assert.equal((await calls('submit_tda_quiz_answer')).length,0)
    assert.equal(await page.getByText('account-aの合成問題',{exact:true}).count(),0)
  })
  await check('already-dispatched save cannot populate the new account', async () => {
    await openQuiz(); await start(); await defer('submit'); await answer()
    await page.waitForFunction(()=>window.tdaAccountQa.calls.some(call=>call.name==='submit_tda_quiz_answer'))
    await emit('account-b'); await resolve('submit')
    assert.equal(await page.getByText('account-aの保存済み解説',{exact:true}).count(),0)
    assert.equal((await calls('check_tda_quiz_answer')).length,0)
  })
  await check('late optional details cannot restore signed-out private results', async () => {
    await openQuiz(); await start(); await defer('detail'); await answer()
    await page.getByText('account-aの保存済み解説',{exact:true}).waitFor()
    await emit(null); await resolve('detail')
    assert.equal(await page.getByText('account-aの保存済み解説',{exact:true}).count(),0)
    assert.equal(await page.getByText('account-aの追加解説',{exact:true}).count(),0)
  })
  await check('same-account token refresh preserves pending quiz and score', async () => {
    await openQuiz(); await start(); await defer('submit'); await answer()
    await page.waitForFunction(()=>window.tdaAccountQa.calls.some(call=>call.name==='submit_tda_quiz_answer'))
    await page.evaluate(()=>window.tdaAccountQa.emit('account-a','TOKEN_REFRESHED')); await resolve('submit')
    await page.getByText('SCORE 1',{exact:true}).waitFor()
    assert.equal((await calls('submit_tda_quiz_answer')).length,1)
  })
  await check('synchronous signout then old option activation cannot dispatch', async () => {
    await openQuiz(); await start()
    await page.evaluate(()=>{const button=[...document.querySelectorAll('button')].find(button=>button.textContent.includes('合成B'));window.tdaAccountQa.emit(null);button.click()})
    await page.waitForTimeout(40)
    assert.equal((await calls('submit_tda_quiz_answer')).length,0)
    assert.equal(await page.getByText('account-aの合成問題',{exact:true}).count(),0)
  })
  await check('fresh verified account mismatch without event refuses write and clears old quiz', async () => {
    await openQuiz(); await start(); await page.evaluate(()=>window.tdaAccountQa.silentlyChange('account-b')); await answer()
    await page.waitForTimeout(40)
    assert.equal((await calls('submit_tda_quiz_answer')).length,0)
    assert.equal(await page.getByText('account-aの合成問題',{exact:true}).count(),0)
  })
  await check('auth callbacks are synchronous without SDK reentrancy and unsubscribe on unmount', async () => {
    await openQuiz(); await emit('account-b'); await page.evaluate(()=>window.unmountTda())
    const stats=await page.evaluate(()=>window.tdaAccountQa.stats())
    assert.equal(stats.callbackSdkCalls,0);assert.equal(stats.asyncCallbacks,0);assert.equal(stats.listeners,0);assert.ok(stats.unsubscribed>0)
  })
  assert.deepEqual(errors, [])
  if (failures.length) { console.log(JSON.stringify({verdict:'FAIL',pass:results.length,fail:failures.length,failures})); process.exitCode=1 }
  console.log(JSON.stringify({verdict:failures.length?'FAIL':'PASS',tests:results.length,results,browser:await browser.version(),transport:'synthetic in-memory only; external blocked; no DB'}))
} finally { await browser?.close(); await server.close() }
