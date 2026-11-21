import assert from 'node:assert/strict'
import { createServer } from 'vite'
import react from '@vitejs/plugin-react'
import { chromium } from 'playwright-core'
const server = await createServer({ configFile: false, plugins: [react()], server: { host: '127.0.0.1', port: 0 } })
let browser
try {
 await server.listen(); browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] })
 const page = await browser.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true }), errors = []
 page.on('pageerror', e => errors.push(e.message))
 await page.route('**/*', r => ['127.0.0.1', 'localhost'].includes(new URL(r.request().url()).hostname) ? r.continue() : r.abort())
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/gto-browser/index.html`)
 const panel = page.getByRole('region', { name: '継続モデルBR比較表' }), search = () => page.getByRole('button', { name: '検証済みレンジを検索', exact: true }).click()
 assert.equal(await panel.count(), 0)
 await page.getByRole('button', { name: '研究用：独立学習HU50BB', exact: true }).click()
 for (const stage of ['vs_3bet', 'vs_4bet']) {
  await page.getByLabel('公開アクション履歴', { exact: true }).selectOption(stage); await search(); await panel.waitFor()
  assert.equal(await page.locator('[data-audit-model]').count(), 5)
  assert.equal(await page.locator('[data-independent-hand]').count(), 169)
  await page.getByLabel('固定するプリフロップ方策', { exact: true }).selectOption('learned_large')
  assert.equal(await page.locator('[data-audit-model]').count(), 5)
 }
 console.log('PASS C01 mobile2CALL stages,5models and169frequency range preserved')
 assert.equal(await page.locator('[data-hand]:enabled').count(), 0)
 assert.equal(await page.getByText(/全体収束の証明ではありません/).count(), 1)
 console.log('PASS C02 continuation BR is explicitly separate from wholegame GTO precision')
 await page.getByLabel('有効スタック（BB）', { exact: true }).fill('0'); await search()
 assert.equal(await panel.count(), 0); assert.equal(await page.getByRole('alert').count(), 1)
 console.log('PASS C03 input errors clear stale audit and range data')
 await page.getByLabel('有効スタック（BB）', { exact: true }).fill('50'); await search(); await panel.waitFor()
 await page.getByLabel('人数', { exact: true }).selectOption('3'); assert.equal(await panel.count(), 0)
 assert.deepEqual(errors, []); assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1))
 console.log('PASS C04 unsupported player count fails closed,no browser errors/overflow/external traffic')
} finally { await browser?.close(); await server.close() }
