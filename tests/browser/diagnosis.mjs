import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { createServer } from 'vite'
import { chromium } from 'playwright-core'
const root = fileURLToPath(new URL('../../', import.meta.url))
const server = await createServer({ root, configFile: false, server: { host: '127.0.0.1', port: 0 },
  plugins: [{ name: 'diagnosis-memory-transport', enforce: 'pre', resolveId(source, importer) {
    if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/diagnosis-supabase.ts')
  }, configureServer(server) { server.middlewares.use('/__diagnosis', (_req,res) => {
    res.setHeader('Content-Type', 'text/html'); res.end('<meta name="viewport" content="width=device-width, initial-scale=1"><div id="root"></div><script type="module" src="/tests/browser/diagnosis-entry.tsx"></script>')
  }) } }], esbuild: { jsx: 'automatic' } })
let browser
const results = []
try {
  await server.listen()
  const base = `http://127.0.0.1:${server.httpServer.address().port}`
  browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 })
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort())
  const check = async (name, fn) => { await fn(); results.push(name); console.log('PASS', name) }
  const ready = async animal => page.getByRole('heading', { name: animal, exact: true }).waitFor()
  await check('result switch resets old animal caption and share editor', async () => {
    await page.goto(base + '/__diagnosis')
    await ready('ライオン')
    await page.getByRole('button', { name: 'Poker IDのタイムラインに投稿' }).click()
    assert.match(await page.getByLabel('診断結果の投稿文').inputValue(), /ライオン/)
    await page.getByRole('button', { name: 'QA result two', exact: true }).click()
    await ready('トラ')
    assert.equal(await page.getByLabel('診断結果の投稿文').count(), 0)
    await page.getByRole('button', { name: 'Poker IDのタイムラインに投稿' }).click()
    assert.match(await page.getByLabel('診断結果の投稿文').inputValue(), /トラ/)
  })
  await check('late share completion cannot add success message on a different result', async () => {
    await page.evaluate(() => { window.diagnosisControls.pendingShare = true })
    await page.getByRole('button', { name: 'この内容で投稿する', exact: true }).click()
    await page.waitForFunction(() => window.diagnosisControls.resolveShare !== null)
    await page.getByRole('button', { name: 'QA result one', exact: true }).click()
    await ready('ライオン')
    await page.evaluate(() => window.diagnosisControls.resolveShare())
    await page.waitForTimeout(100)
    assert.equal(await page.getByText('タイムラインに投稿しました。', { exact: true }).count(), 0)
  })
  await check('non-owner cannot access share or restart controls', async () => {
    await page.getByRole('button', { name: 'QA visitor', exact: true }).click()
    await ready('ライオン')
    await page.getByText('このプレイヤーのタイプ', { exact: true }).waitFor()
    assert.equal(await page.getByRole('button', { name: 'Poker IDのタイムラインに投稿' }).count(), 0)
    assert.equal(await page.getByRole('button', { name: '画像を保存' }).count(), 0)
    assert.equal(await page.getByRole('button', { name: 'もう一度診断する' }).count(), 0)
  })
  await check('mobile saved-result refresh, PNG dimensions and no overflow', async () => {
    await page.goto(base + '/__diagnosis')
    await ready('ライオン')
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true)
    const downloadPromise = page.waitForEvent('download')
    await page.getByRole('button', { name: '画像を保存' }).click()
    const download = await downloadPromise
    assert.match(download.suggestedFilename(), /^PokerID_lion_one\.png$/)
    const bytes = await readFile(await download.path())
    assert.equal(bytes.readUInt32BE(16), 1080)
    assert.equal(bytes.readUInt32BE(20), 1500)
    await page.reload(); await ready('ライオン')
  })
  await check('50th-answer failure retries exactly 50 IDs and restart clears result URL', async () => {
    await page.goto(base + '/__diagnosis?intro=1')
    await page.getByRole('button', { name: '診断をはじめる', exact: true }).click()
    for (let number = 1; number <= 49; number++) {
      await page.getByText(`QUESTION ${number}`, { exact: true }).waitFor()
      await page.locator('.ptd-option').first().click()
    }
    await page.evaluate(() => { window.diagnosisControls.failSave = true })
    await page.locator('.ptd-option').first().click()
    await page.getByText('結果を保存できませんでした：test retry', { exact: true }).waitFor()
    await page.evaluate(() => { window.diagnosisControls.failSave = false })
    await page.locator('.ptd-option').first().click(); await ready('ライオン')
    const counts = await page.evaluate(() => window.diagnosisCalls.filter(c => c.name === 'complete_player_type_v2_diagnosis').map(c => c.args.p_option_ids.length))
    assert.deepEqual(counts, [50, 50])
    await page.getByRole('button', { name: 'もう一度診断する' }).click()
    await page.getByText('QUESTION 1', { exact: true }).waitFor()
    await page.waitForFunction(() => document.querySelector('[data-testid=route]').textContent === '/player-type')
    assert.equal(await page.getByTestId('route').innerText(), '/player-type')
  })
  await check('rejected old save cannot put an error on a newly loaded result', async () => {
    await page.goto(base + '/__diagnosis?intro=1')
    await page.getByRole('button', { name: '診断をはじめる', exact: true }).click()
    for (let number = 1; number <= 49; number++) {
      await page.getByText(`QUESTION ${number}`, { exact: true }).waitFor()
      await page.locator('.ptd-option').first().click()
    }
    await page.evaluate(() => { window.diagnosisControls.pendingSave = true })
    await page.locator('.ptd-option').first().click()
    await page.waitForFunction(() => window.diagnosisControls.rejectSave !== null)
    await page.getByRole('button', { name: 'QA result one', exact: true }).click(); await ready('ライオン')
    await page.evaluate(() => window.diagnosisControls.rejectSave())
    await page.waitForTimeout(100)
    assert.equal(await page.getByText('結果を保存できませんでした。通信状況を確認して、最後の回答をもう一度選んでください。', { exact: true }).count(), 0)
  })
  assert.deepEqual(errors, [])
  console.log(JSON.stringify({ verdict: 'PASS', tests: results.length, results, viewport: '390x844', browser: await browser.version(), transport: 'in-memory mock; external requests blocked; no DB' }))
} finally { await browser?.close(); await server.close() }
