// Run with a separately installed playwright-core; browser never contacts a DB.
import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { createServer } from 'vite'
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright-core')
const root = fileURLToPath(new URL('../../', import.meta.url))
const server = await createServer({ root, configFile: false, server: { host: '127.0.0.1', port: 0 },
  plugins: [{ name: 'qa-only-supabase', enforce: 'pre', resolveId(source, importer) {
    if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/tda-supabase.ts')
  }, configureServer(server) { server.middlewares.use('/__qa', (req,res) => {
    res.setHeader('Content-Type', 'text/html'); res.end('<div id="root"></div><script type="module" src="/tests/browser/tda-entry.tsx"></script>')
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
  const check = (name, fn) => fn().then(() => { results.push(name); console.log('PASS', name) })
  const open = async (scenario) => {
    await page.goto(base + '/__qa?case=' + scenario)
    await page.getByRole('button', { name: /TDAクイズ/ }).click()
  }
  for (const [name, button] of [['normal','クイズを始める'],['hard','挑戦する'],['wrong','復習する']]) {
    await check(name + ' fetch recovers after a thrown transport error', async () => {
      await open('throw-once')
      await page.getByRole('button', { name: button, exact: true }).click()
      await page.getByRole('alert').waitFor()
      assert.equal(await page.getByRole('button', { name: button, exact: true }).isEnabled(), true)
      await page.getByRole('button', { name: button, exact: true }).click()
      await page.getByRole('heading', { name: 'QA用の合成問題' }).waitFor()
      assert.equal(await page.getByRole('button', { name: '合成選択肢B', exact: false }).count(), 1)
    })
  }
  await check('malformed options fail closed without a render crash', async () => {
    await open('malformed')
    await page.getByRole('button', { name: 'クイズを始める', exact: true }).click()
    await page.getByRole('alert').getByText('問題データの整合性を確認できませんでした。再度お試しください。').waitFor()
    assert.equal(await page.getByRole('heading', { name: 'QA用の合成問題' }).count(), 0)
  })
  await check('saved answer survives optional explanation transport failure without duplicate writes', async () => {
    await open('detail-throws')
    await page.getByRole('button', { name: 'クイズを始める', exact: true }).click()
    await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
    await page.getByText('保存済みの合成解説', { exact: true }).waitFor()
    assert.equal(await page.evaluate(() => window.tdaQaCalls.filter(name => name === 'submit_tda_quiz_answer').length), 1)
    assert.equal(await page.getByText('SCORE 1', { exact: true }).count(), 1)
  })
  assert.deepEqual(errors, [])
  console.log(JSON.stringify({ verdict: 'PASS', tests: results.length, results, browser: await browser.version(), transport: 'in-memory mock; all questions synthetic; external requests blocked; no DB' }))
} finally { await browser?.close(); await server.close() }
