import assert from 'node:assert/strict'
import { createServer } from 'vite'
import react from '@vitejs/plugin-react'
import { chromium } from 'playwright-core'
const server = await createServer({ configFile: false, plugins: [react()], server: { host: '127.0.0.1', port: 0 } })
let browser
try {
  await server.listen()
  browser = await chromium.launch({ headless: true, ...(process.env.GTO_CHROMIUM_PATH ? { executablePath: process.env.GTO_CHROMIUM_PATH } : {}), args: ['--no-sandbox'] })
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true }), errors = []
  page.on('pageerror', e => errors.push(e.message))
  await page.route('**/*', route => ['127.0.0.1', 'localhost'].includes(new URL(route.request().url()).hostname) ? route.continue() : route.abort())
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/gto-browser/index.html`)
  const search = () => page.getByRole('button', { name: '検証済みレンジを検索', exact: true }).click()
  assert.equal(await page.locator('[data-independent-hand]').count(), 0)
  await page.getByRole('button', { name: '研究用：独立学習HU50BB', exact: true }).click()
  await search()
  assert.equal(await page.locator('[data-independent-hand]').count(), 169)
  assert.equal(await page.locator('[data-hand]:enabled').count(), 0)
  console.log('PASS I01 opt-in research gate preserves ordinary verified catalog on390px')
  for (const stage of ['rfi', 'vs_open', 'vs_3bet', 'vs_4bet']) {
    await page.getByLabel('公開アクション履歴', { exact: true }).selectOption(stage); await search()
    assert.equal(await page.locator('[data-independent-hand]').count(), 169)
    const cell = page.locator('[data-independent-hand="AKs"]'); await cell.scrollIntoViewIfNeeded(); await cell.tap()
    await page.getByRole('heading', { name: 'AKs：独立学習の頻度・EV', exact: true }).waitFor()
    assert.equal(await cell.getAttribute('aria-pressed'), 'true')
    assert.equal(await page.locator('[data-independent-detail] li').count(), 3)
  }
  console.log('PASS I02 all4 public histories,169 tap cells and actionEV details')
  await page.getByLabel('独立学習の継続モデル', { exact: true }).selectOption('learned_large')
  assert.equal(await page.locator('[data-independent-hand]').count(), 169)
  console.log('PASS I03 both independently trained continuation models')
  await page.getByLabel('有効スタック（BB）', { exact: true }).fill('49'); await search()
  assert.equal(await page.locator('[data-independent-hand]').count(), 0)
  console.log('PASS I04 condition edit removes stale strategy; unsupported conditions never interpolate')
  assert.deepEqual(errors, [])
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1))
  console.log('PASS I05 no external traffic, browser errors or page overflow at390px')
} finally { await browser?.close(); await server.close() }
