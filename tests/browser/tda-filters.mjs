// Protected real-React mobile acceptance. All RPCs are synthetic and external requests are blocked.
import assert from 'node:assert/strict'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { createServer } from 'vite'
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright-core')
const root = fileURLToPath(new URL('../../', import.meta.url))
const cacheDir = await mkdtemp(path.join(tmpdir(), 'pokerid-filter-vite-'))
let server, browser
const completed = []
try {
  server = await createServer({ root, configFile: false, cacheDir,
    server: { host: '127.0.0.1', port: 0 },
    plugins: [{ name: 'qa-only-filter-transport', enforce: 'pre',
      resolveId(source, importer) {
        if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/tda-filters-supabase.ts')
      },
      configureServer(vite) {
        vite.middlewares.use('/__qa', (_req, res) => {
          res.setHeader('Content-Type', 'text/html')
          res.end('<div id="root"></div><script type="module" src="/tests/browser/tda-entry.tsx"></script>')
        })
      },
    }], esbuild: { jsx: 'automatic' } })
  await server.listen()
  const base = `http://127.0.0.1:${server.httpServer.address().port}`
  browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
  for (const [scenario, expected] of [
    ['bad-difficulty', [[''], ['', 'MTT']]],
    ['bad-category', [['', 'BEGINNER'], ['']]],
    ['mixed-items', [['', 'BEGINNER'], ['', 'MTT']]],
    ['valid', [['', 'BEGINNER', 'ADVANCED'], ['', 'MTT', 'RING']]],
  ]) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
    page.setDefaultTimeout(4000)
    const errors = []
    page.on('pageerror', error => errors.push(error.message))
    await page.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort())
    try {
      await page.goto(base + '/__qa?case=' + scenario)
      await page.getByRole('button', { name: /TDAクイズ/ }).click()
      await page.waitForFunction(() => window.tdaFilterResponseDelivered === true)
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
      assert.deepEqual(errors, [], scenario + ' must not crash React')
      const selects = page.locator('.tda-quiz-select-grid select')
      assert.equal(await selects.count(), 2)
      for (let index = 0; index < 2; index++) {
        assert.deepEqual(await selects.nth(index).locator('option').evaluateAll(options => options.map(option => option.value)), expected[index])
        if (expected[index].length > 1) await selects.nth(index).selectOption(expected[index][1])
      }
      await page.getByRole('button', { name: 'クイズを始める', exact: true }).click()
      await page.getByRole('heading', { name: 'QA用の合成問題' }).waitFor()
      const calls = await page.evaluate(() => window.tdaFilterCalls)
      assert.deepEqual(calls.find(call => call.name === 'get_tda_quiz_questions')?.args,
        { p_difficulty: expected[0][1] || null, p_category: expected[1][1] || null, p_limit: 10 })
      assert.equal(calls.filter(call => call.name === 'submit_tda_quiz_answer').length, 0)
      assert.deepEqual(errors, [])
      completed.push(scenario)
      console.log('PASS browser optional filters:', scenario)
    } finally { await page.close() }
  }
  console.log(JSON.stringify({ verdict: 'PASS', browser_cases: completed.length, cases: completed,
    browser: await browser.version(), transport: 'synthetic RPC; external requests blocked; no DB' }))
} finally {
  await browser?.close()
  await server?.close()
  await rm(cacheDir, { recursive: true, force: true })
}
