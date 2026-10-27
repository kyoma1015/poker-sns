import assert from 'node:assert/strict'
import { createServer } from 'vite'
import react from '@vitejs/plugin-react'
import { chromium } from 'playwright-core'

const server = await createServer({ configFile: false, plugins: [react()],
  server: { host: '127.0.0.1', port: 0 } })
let browser
try {
  await server.listen()
  const port = server.httpServer.address().port
  const url = `http://127.0.0.1:${port}/tests/gto-browser/index.html`
  browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] })
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.route('**/*', route => {
    const host = new URL(route.request().url()).hostname
    return ['127.0.0.1', 'localhost'].includes(host) ? route.continue() : route.abort()
  })
  await page.goto(url)
  await page.getByRole('heading', { name: 'プリフロップレンジ検索', exact: true }).waitFor()
  assert.equal(await page.locator('button[data-hand]').count(), 169)
  assert.equal(await page.locator('button[data-hand]:enabled').count(), 0)
  console.log('PASS B01 unsupported ordinary default condition renders169 unknown cells')
  await page.getByLabel('人数', { exact: true }).selectOption('2')
  assert.deepEqual(await page.getByLabel('ポジション', { exact: true }).locator('option').allTextContents(), ['BTN / SB', 'BB'])
  await page.getByLabel('人数', { exact: true }).selectOption('6')
  console.log('PASS B02 player counts update native-seat positions')
  async function fill() {
    await page.getByLabel('有効スタック（BB）', { exact: true }).fill('100')
    await page.getByLabel('オープンサイズ（BB）', { exact: true }).fill('2.5')
    await page.getByLabel('3ベットサイズ（BB）', { exact: true }).fill('9')
    await page.getByLabel('4ベットサイズ（BB）', { exact: true }).fill('21')
    await page.getByRole('button', { name: '検証済みレンジを検索', exact: true }).click()
  }
  await fill()
  await page.getByRole('status').filter({ hasText: 'この条件の検証済みデータはまだありません。' }).waitFor()
  assert.equal(await page.locator('button[data-hand]:enabled').count(), 0)
  assert.equal(await page.getByLabel('レーキ', { exact: true }).isDisabled(), true)
  console.log('PASS B03 unsupported conditions never display a strategy or EV')
  await page.goto(`${url}?fixture=1`)
  await page.getByRole('heading', { name: 'プリフロップレンジ検索', exact: true }).waitFor()
  await fill()
  assert.equal(await page.locator('button[data-hand]:enabled').count(), 169)
  await page.locator('button[data-hand="AKs"]').click()
  await page.getByRole('heading', { name: 'AKsの頻度とEV', exact: true }).waitFor()
  assert.equal(await page.getByText('Call：50.0%', { exact: true }).count(), 1)
  console.log('PASS B04 isolated synthetic fixture renders frequencies and selected-hand EV')
  await page.getByLabel('有効スタック（BB）', { exact: true }).fill('99')
  assert.equal(await page.locator('button[data-hand]:enabled').count(), 0)
  assert.equal(await page.getByRole('heading', { name: 'AKsの頻度とEV', exact: true }).count(), 0)
  console.log('PASS B05 editing any condition clears stale results')
  assert.deepEqual(errors, [])
  console.log('PASS B06 no unhandled browser errors; external requests blocked')
  await page.goto(url)
  await page.getByRole('button', { name: '検証済みテスト条件：HU1BB', exact: true }).click()
  assert.equal(await page.getByLabel('オープンサイズ（BB）', { exact: true }).isDisabled(), true)
  await page.getByRole('button', { name: '検証済みレンジを検索', exact: true }).click()
  assert.equal(await page.locator('button[data-hand]:enabled').count(), 169)
  assert.equal(await page.getByText('コール（1BBオールイン）：100.0%', { exact: true }).count(), 1)
  assert.equal(await page.getByText(/99\.9999998%/).count(), 1)
  assert.deepEqual(errors, [])
  console.log('PASS B07 actual native-certified test data displays169hands, EV intervals and statistical confidence')
} finally {
  await browser?.close()
  await server.close()
}
