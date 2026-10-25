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
  const failures = []
  page.setDefaultTimeout(1800)
  const check = async (name, fn) => { try { await fn(); results.push(name); console.log('PASS', name) } catch (error) { failures.push({name, message:error.message}); console.log('FAIL', name, error.message.split('\n')[0]) } }
  const open = async (scenario) => {
    await page.goto(base + '/__qa?case=' + scenario)
    await page.getByRole('button', { name: /TDAクイズ/ }).click()
  }
  for (const scenario of ['save-throws', 'save-empty', 'malformed-answer']) {
    await check(scenario + ' preserves uncertain answer and permits unscored completion', async () => {
      await open(scenario)
      await page.getByRole('button', { name: 'クイズを始める', exact: true }).click()
      await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
      await page.getByRole('alert').waitFor()
      assert.equal(await page.getByRole('button', { name: '合成選択肢B', exact: false }).isDisabled(), true)
      await page.getByRole('button', { name: '未確認の回答を採点せず結果を見る', exact: true }).click()
      await page.getByText('確認できた回答 0問 / 出題 1問', { exact: true }).waitFor()
      await page.getByText('保存・判定を確認できなかった回答：1問。正解・不正解には含めていません。', { exact: true }).waitFor()
      assert.equal(await page.getByText('全問正解です。', { exact: true }).count(), 0)
      assert.equal(await page.evaluate(() => window.tdaQaCalls.filter(name => name === 'submit_tda_quiz_answer').length), 1)
    })
  }
  await check('uncertain first answer never corrupts next verified answer or review numbering', async () => {
    await open('uncertain-then-next')
    await page.getByRole('button', { name: 'クイズを始める', exact: true }).click()
    await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
    await page.getByRole('button', { name: 'この回答を採点せず次の問題へ', exact: true }).click()
    await page.getByRole('heading', { name: 'QA用の合成問題2', exact: true }).waitFor()
    await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
    await page.getByText('保存済みの合成解説', { exact: true }).waitFor()
    await page.getByRole('button', { name: '結果を見る', exact: true }).click()
    await page.getByText('確認できた回答 1問 / 出題 2問', { exact: true }).waitFor()
    await page.getByText('Q2', { exact: true }).waitFor()
    assert.equal(await page.getByText('Q1', { exact: true }).count(), 0)
    assert.equal(await page.getByText('全問正解です。', { exact: true }).count(), 0)
    assert.equal(await page.evaluate(() => window.tdaQaCalls.filter(name => name === 'submit_tda_quiz_answer').length), 2)
  })
  await check('explicit permission rejection retains login guidance and permits later verified answer', async () => {
    await open('permission-once')
    await page.getByRole('button', { name: 'クイズを始める', exact: true }).click()
    await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
    await page.getByRole('button', { name: 'ログインする', exact: true }).waitFor()
    assert.equal(await page.getByRole('button', { name: '合成選択肢B', exact: false }).isDisabled(), false)
    await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
    await page.getByText('保存済みの合成解説', { exact: true }).waitFor()
    await page.getByRole('button', { name: '結果を見る', exact: true }).click()
    await page.getByText('全問正解です。', { exact: true }).waitFor()
    assert.equal(await page.evaluate(() => window.tdaQaCalls.filter(name => name === 'submit_tda_quiz_answer').length), 2)
  })
  await check('saved answer remains usable while optional detail never returns', async () => {
    await open('detail-never')
    await page.getByRole('button', { name: 'クイズを始める', exact: true }).click()
    await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
    await page.getByText('保存済みの合成解説', { exact: true }).waitFor()
    await page.getByRole('button', { name: '結果を見る', exact: true }).click()
    await page.getByText('全問正解です。', { exact: true }).waitFor()
    assert.equal(await page.evaluate(() => window.tdaQaCalls.filter(name => name === 'submit_tda_quiz_answer').length), 1)
  })
  await check('late optional details cannot replace the next question answer', async () => {
    await open('detail-late')
    await page.getByRole('button', { name: 'クイズを始める', exact: true }).click()
    await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
    await page.getByRole('button', { name: '次の問題へ', exact: true }).click()
    await page.getByRole('button', { name: '合成選択肢B', exact: false }).click()
    await page.getByText('保存済みの合成解説', { exact: true }).waitFor()
    await page.evaluate(() => window.resolveTdaDetail())
    await page.waitForTimeout(50)
    assert.equal(await page.getByText('遅延した前問の解説', { exact: true }).count(), 0)
    await page.getByRole('button', { name: '結果を見る', exact: true }).click()
    assert.equal(await page.evaluate(() => window.tdaQaCalls.filter(name => name === 'submit_tda_quiz_answer').length), 2)
    await page.getByText('全問正解です。', { exact: true }).waitFor()
  })
  assert.deepEqual(errors, [])
  if (failures.length) { console.log(JSON.stringify({verdict:'FAIL',pass:results.length,fail:failures.length,failures})); process.exitCode=1 }
  console.log(JSON.stringify({ verdict: failures.length ? 'FAIL' : 'PASS', tests: results.length, results, browser: await browser.version(), transport: 'in-memory mock; all questions synthetic; external requests blocked; no DB' }))
} finally { await browser?.close(); await server.close() }
