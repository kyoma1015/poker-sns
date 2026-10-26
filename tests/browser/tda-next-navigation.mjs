import assert from 'node:assert/strict'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { createServer } from 'vite'
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright-core')
const root = fileURLToPath(new URL('../../', import.meta.url))
const cache = await mkdtemp(path.join(tmpdir(), 'poker-tda-next-'))
let server, browser
const passed = [], failures = []
try {
  server = await createServer({ root, cacheDir: cache, configFile: false,
    server: { host: '127.0.0.1', port: 0 }, esbuild: { jsx: 'automatic' },
    plugins: [{ name: 'synthetic-tda-navigation', enforce: 'pre', resolveId(source, importer) {
      if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/tda-supabase.ts')
    }, configureServer(vite) { vite.middlewares.use('/__qa', (_req, res) => {
      res.setHeader('Content-Type', 'text/html')
      res.end('<div id="root"></div><script type="module" src="/tests/browser/tda-entry.tsx"></script>')
    }) } }] })
  await server.listen()
  const base = 'http://127.0.0.1:' + server.httpServer.address().port
  browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
  page.setDefaultTimeout(2500)
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort())
  const check = async (name, run) => {
    try { await run(); passed.push(name); console.log('PASS', name) }
    catch (error) { failures.push({ name, message: error.message }); console.log('FAIL', name, error.message.split('\n')[0]) }
  }
  const open = async scenario => {
    await page.goto(base + '/__qa?case=' + scenario)
    await page.getByRole('button', { name: /TDAクイズ/ }).click()
    await page.getByRole('button', { name: 'クイズを始める', exact: true }).click()
  }
  const doubleNext = async label => {
    await page.getByRole('button', { name: label, exact: true }).waitFor()
    await page.evaluate(label => {
      const next = [...document.querySelectorAll('button')].find(button => button.textContent.trim() === label)
      if (!next) throw new Error('Synthetic next button missing')
      next.click(); next.click()
    }, label)
  }
  const submits = () => page.evaluate(() => window.tdaQaCalls.filter(name => name === 'submit_tda_quiz_answer').length)
  for (const [scenario, nextLabel] of [['detail-late', '次の問題へ'], ['uncertain-then-next', 'この回答を採点せず次の問題へ']]) {
    await check(scenario + ': same-tick next cannot skip question or corrupt review', async () => {
      await open(scenario)
      await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
      await doubleNext(nextLabel)
      await page.getByRole('heading', { name: 'QA用の合成問題2', exact: true }).waitFor()
      assert.equal(await page.getByText('QUESTION 2 / 2', { exact: true }).count(), 1)
      await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
      await page.getByRole('button', { name: '結果を見る', exact: true }).click()
      await page.getByText('Q2', { exact: true }).waitFor()
      if (scenario === 'detail-late') {
        await page.getByText('Q1', { exact: true }).waitFor()
        await page.getByRole('heading', { name: '2 / 2', exact: true }).waitFor()
      } else {
        assert.equal(await page.getByText('Q1', { exact: true }).count(), 0)
        await page.getByText('確認できた回答 1問 / 出題 2問', { exact: true }).waitFor()
        await page.getByText('保存・判定を確認できなかった回答：1問。正解・不正解には含めていません。', { exact: true }).waitFor()
      }
      assert.equal(await submits(), 2)
    })
  }
  await check('double final transition retains one answer and one review item', async () => {
    await open('double-final')
    await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
    await doubleNext('結果を見る')
    await page.getByRole('heading', { name: '1 / 1', exact: true }).waitFor()
    assert.equal(await page.getByText('Q1', { exact: true }).count(), 1)
    assert.equal(await submits(), 1)
  })
  assert.deepEqual(errors, [])
  console.log(JSON.stringify({ verdict: failures.length ? 'FAIL' : 'PASS', tests: 3, pass: passed.length, fail: failures.length, passed, failures, browser: await browser.version(), transport: 'synthetic; external requests blocked; no DB' }))
  if (failures.length) process.exitCode = 1
} finally {
  await browser?.close()
  await server?.close()
  await rm(cache, { recursive: true, force: true })
}
