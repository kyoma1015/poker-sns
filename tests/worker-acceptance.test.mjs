import assert from 'node:assert/strict'
import test from 'node:test'
import path from 'node:path'
import os from 'node:os'
import { mkdtemp, rm, readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import { chromium } from 'playwright-core'
const root = fileURLToPath(new URL('../', import.meta.url))
test('a physical double-click answers only the visible diagnosis question', async () => {
  const cacheDir = await mkdtemp(path.join(os.tmpdir(), 'pokerid-diagnosis-gesture-'))
  const server = await createServer({ root, cacheDir, configFile: false, server: { host: '127.0.0.1', port: 0 },
    plugins: [{ name: 'double-click-test-transport', enforce: 'pre', resolveId(source, importer) {
      if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/diagnosis-supabase.ts')
    }, configureServer(server) { server.middlewares.use('/__diagnosis', (_req,res) => {
      res.setHeader('Content-Type', 'text/html'); res.end('<meta name="viewport" content="width=device-width, initial-scale=1"><div id="root"></div><script type="module" src="/tests/browser/diagnosis-entry.tsx"></script>')
    }) } }], esbuild: { jsx: 'automatic' } })
  let browser
  try {
    await server.listen()
    const base = `http://127.0.0.1:${server.httpServer.address().port}`
    browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
    await page.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort())
    await page.goto(base + '/__diagnosis?intro=1')
    await page.getByRole('button', { name: '診断をはじめる', exact: true }).click()
    await page.getByText('QUESTION 1', { exact: true }).waitFor()
    await page.locator('.ptd-option').first().dblclick({ delay: 75 })
    assert.equal((await page.locator('.ptd-question-number').innerText()).trim(), 'QUESTION 2')
    // A later intentional click must still advance to Q3.
    await page.locator('.ptd-option').first().click()
    await page.getByText('QUESTION 3', { exact: true }).waitFor({ timeout: 2000 })
  } finally { await browser?.close(); await server.close(); await rm(cacheDir, { recursive: true, force: true }) }
})


// Protected redaction acceptance: real TSX, local memory transport, synthetic marker only.
async function redactionHarness(fn) {
  const cacheDir = await mkdtemp(path.join(os.tmpdir(), 'pokerid-diagnosis-redaction-'))
  const server = await createServer({ root, cacheDir, configFile: false,
    server: { host: '127.0.0.1', port: 0 }, esbuild: { jsx: 'automatic' },
    plugins: [{ name: 'redaction-test-transport', enforce: 'pre', resolveId(source, importer) {
      if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/diagnosis-redaction-supabase.ts')
    }, configureServer(server) { server.middlewares.use('/__diagnosis', (_req,res) => {
      res.setHeader('Content-Type', 'text/html'); res.end('<meta name="viewport" content="width=device-width, initial-scale=1"><div id="root"></div><script type="module" src="/tests/browser/diagnosis-entry.tsx"></script>')
    }) } }] })
  let browser
  try {
    await server.listen()
    const base = `http://127.0.0.1:${server.httpServer.address().port}`
    browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
    await page.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort())
    await fn(page, base)
  } finally { await browser?.close(); await server.close(); await rm(cacheDir, { recursive: true, force: true }) }
}
const privateMarker = 'SYNTHETIC_PRIVATE_DIAGNOSIS_DETAIL'
async function reachLastQuestion(page, base) {
  await page.goto(base + '/__diagnosis?intro=1')
  await page.getByRole('button', { name: '診断をはじめる', exact: true }).click()
  for (let number = 1; number <= 49; number++) {
    await page.getByText(`QUESTION ${number}`, { exact: true }).waitFor()
    await page.locator('.ptd-option').first().click()
  }
  await page.getByText('QUESTION 50', { exact: true }).waitFor()
}

test('saved-result failure hides backend details and retry still submits exactly50 answers', async () => {
  await redactionHarness(async (page, base) => {
    await reachLastQuestion(page, base)
    await page.evaluate(() => { window.diagnosisControls.failSave = true })
    await page.locator('.ptd-option').first().click()
    await page.locator('.ptd-error').waitFor()
    const visible = await page.locator('body').innerText()
    assert.equal(visible.includes(privateMarker), false, 'backend exception details must not reach the DOM')
    assert.match(await page.locator('.ptd-error').innerText(), /結果を保存できませんでした。.*もう一度/)
    await page.evaluate(() => { window.diagnosisControls.failSave = false })
    await page.locator('.ptd-option').first().click()
    await page.getByRole('heading', { name: 'ライオン', exact: true }).waitFor()
    assert.deepEqual(await page.evaluate(() => window.diagnosisCalls.filter(c => c.name === 'complete_player_type_v2_diagnosis').map(c => c.args.p_option_ids.length)), [50,50])
  })
})

test('share failure hides backend details and the next share can recover', async () => {
  await redactionHarness(async (page, base) => {
    await page.goto(base + '/__diagnosis')
    await page.getByRole('heading', { name: 'ライオン', exact: true }).waitFor()
    await page.getByRole('button', { name: 'Poker IDのタイムラインに投稿', exact: true }).click()
    await page.evaluate(() => { window.diagnosisControls.failShare = true })
    await page.getByRole('button', { name: 'この内容で投稿する', exact: true }).click()
    await page.locator('.ptd-result-hint[role="status"]').waitFor()
    assert.equal((await page.locator('body').innerText()).includes(privateMarker), false, 'share exception details must not reach the DOM')
    assert.match(await page.locator('.ptd-result-hint[role="status"]').innerText(), /投稿に失敗しました。.*もう一度/)
    await page.evaluate(() => { window.diagnosisControls.failShare = false })
    await page.getByRole('button', { name: 'この内容で投稿する', exact: true }).click()
    await page.getByText('タイムラインに投稿しました。', { exact: true }).waitFor()
  })
})

test('late rejected save and share cannot pollute a different result', async () => {
  await redactionHarness(async (page, base) => {
    await reachLastQuestion(page, base)
    await page.evaluate(() => { window.diagnosisControls.pendingSave = true })
    await page.locator('.ptd-option').first().click()
    await page.waitForFunction(() => window.diagnosisControls.rejectSave !== null)
    await page.getByRole('button', { name: 'QA result one', exact: true }).click()
    await page.getByRole('heading', { name: 'ライオン', exact: true }).waitFor()
    await page.evaluate(() => window.diagnosisControls.rejectSave())
    await page.waitForTimeout(100)
    assert.equal((await page.locator('body').innerText()).includes(privateMarker), false)
    assert.equal(await page.locator('.ptd-error').count(), 0)
    await page.getByRole('button', { name: 'Poker IDのタイムラインに投稿', exact: true }).click()
    await page.evaluate(() => { window.diagnosisControls.pendingShare = true })
    await page.getByRole('button', { name: 'この内容で投稿する', exact: true }).click()
    await page.waitForFunction(() => window.diagnosisControls.rejectShare !== null)
    await page.getByRole('button', { name: 'QA result two', exact: true }).click()
    await page.getByRole('heading', { name: 'トラ', exact: true }).waitFor()
    await page.evaluate(() => window.diagnosisControls.rejectShare())
    await page.waitForTimeout(100)
    assert.equal((await page.locator('body').innerText()).includes(privateMarker), false)
    assert.equal(await page.locator('.ptd-result-hint[role="status"]').count(), 0)
  })
})


test('PNG export failure hides exception details and retry preserves PNG dimensions', async () => {
  await redactionHarness(async (page, base) => {
    await page.goto(base + '/__diagnosis')
    await page.getByRole('heading', { name: 'ライオン', exact: true }).waitFor()
    await page.evaluate(() => {
      window.savedPngToBlob = HTMLCanvasElement.prototype.toBlob
      HTMLCanvasElement.prototype.toBlob = function () { throw new Error('SYNTHETIC_PRIVATE_PNG_EXPORT_DETAIL') }
    })
    await page.getByRole('button', { name: '画像を保存', exact: true }).click()
    await page.getByText(/画像の保存に失敗しました/).waitFor()
    assert.equal((await page.locator('body').innerText()).includes('SYNTHETIC_PRIVATE_PNG_EXPORT_DETAIL'), false, 'PNG exception detail must not reach DOM')
    assert.match(await page.getByText(/画像の保存に失敗しました/).innerText(), /画像の保存に失敗しました。.*もう一度/)
    await page.evaluate(() => { HTMLCanvasElement.prototype.toBlob = window.savedPngToBlob })
    const pendingDownload = page.waitForEvent('download')
    await page.getByRole('button', { name: '画像を保存', exact: true }).click()
    const download = await pendingDownload
    const bytes = await readFile(await download.path())
    assert.equal(bytes.readUInt32BE(16), 1080)
    assert.equal(bytes.readUInt32BE(20), 1500)
    assert.match(download.suggestedFilename(), /^PokerID_lion_one\.png$/)
  })
})

test('late PNG failure cannot add errors or loading to another diagnosis result', async () => {
  await redactionHarness(async (page, base) => {
    await page.goto(base + '/__diagnosis')
    await page.getByRole('heading', { name: 'ライオン', exact: true }).waitFor()
    await page.evaluate(() => { HTMLCanvasElement.prototype.toBlob = function (callback) { window.rejectPendingPng = () => callback(null) } })
    await page.getByRole('button', { name: '画像を保存', exact: true }).click()
    await page.waitForFunction(() => typeof window.rejectPendingPng === 'function')
    await page.getByRole('button', { name: 'QA result two', exact: true }).click()
    await page.getByRole('heading', { name: 'トラ', exact: true }).waitFor()
    await page.evaluate(() => window.rejectPendingPng())
    await page.waitForTimeout(100)
    assert.equal(await page.getByText(/画像の保存に失敗しました/).count(), 0)
    assert.equal(await page.getByText('画像を作成しています...').count(), 0)
  })
})
