import { chromium } from 'playwright-core'
import assert from 'node:assert/strict'
import { readFileSync, mkdirSync } from 'node:fs'
import { createServer } from 'node:http'
import { pathToFileURL } from 'node:url'
import path from 'node:path'
const html = readFileSync('public/gto-demo/index.html')
const server = createServer((req, res) => {if (req.method !== 'GET' || req.url !== '/') {res.writeHead(404);res.end();return} res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });res.end(html)})
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
let browser
try {
  browser = await chromium.launch({ executablePath: process.env.GTO_DEMO_CHROMIUM, headless: true, args: ['--no-sandbox'] })
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })
  const page = await context.newPage(), errors = [], requests = []
  page.on('pageerror', e => errors.push(e.message));page.on('request', r => requests.push(r.url()))
  await context.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort())
  await page.goto(`http://127.0.0.1:${server.address().port}/`)
  assert.equal(await page.locator('#grid button').count(), 169)
  assert.ok(await page.locator('[data-hand="AA"]').evaluate(b => getComputedStyle(b).backgroundImage.includes('linear-gradient')))
  assert.ok(await page.getByText('研究版／実戦GTO精度未検証', { exact: true }).isVisible())
  assert.equal(await page.locator('input[type=password],form').count(), 0)
  console.log('PASS D01 empty mobile context loads169 hands without auth or app bootstrap')
  for (const mode of ['flop_controller', 'checkdown']) {
    await page.selectOption('#mode', mode)
    for (const stage of ['rfi', 'vs_open', 'vs_3bet', 'vs_4bet']) {
      await page.locator(`[data-stage="${stage}"]`).tap()
      await page.locator('[data-hand="72o"]').tap()
      assert.equal(await page.locator('#hand').textContent(), '72o')
      assert.equal(await page.locator('#actions .action').count(), 3)
      assert.ok((await page.locator('#ev').textContent()).includes('BB'))
      assert.equal(await page.locator(`[data-stage="${stage}"]`).getAttribute('aria-pressed'), 'true')
    }
  }
  console.log('PASS D02 all8 contexts expose tappable frequencies, conditional EV and intervals')
  await page.selectOption('#mode', 'checkdown');await page.locator('[data-hand="AA"]').tap()
  assert.ok((await page.locator('#exact').textContent()).includes('標本誤差なし'))
  await page.locator('[data-hand="AA"]').focus();await page.keyboard.press('ArrowRight')
  assert.equal(await page.locator('#hand').textContent(), 'AKs')
  console.log('PASS D03 exact model values are labelled and keyboard navigation updates details')
  for (const width of [320, 390, 768]) {
    await page.setViewportSize({ width, height: 844 })
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1))
  }
  await page.setViewportSize({ width: 390, height: 844 })
  const rect = await page.locator('[data-hand="AA"]').boundingBox();assert.ok(rect.width >= 24 && rect.height >= 36)
  mkdirSync('/tmp/gto-demo-shots', { recursive: true });await page.screenshot({ path: '/tmp/gto-demo-shots/mobile.png', fullPage: true })
  console.log('PASS D04 mobile320/390 and tablet layouts contain no page overflow')
  assert.equal(requests.length, 1);assert.equal(errors.length, 0)
  assert.equal(await page.evaluate(() => localStorage.length + sessionStorage.length), 0)
  assert.equal((await context.cookies()).length, 0)
  console.log('PASS D05 no runtime network, cookies, storage or browser exceptions')
  await context.close()
  const offline = await browser.newContext({ viewport: { width: 390, height: 844 }, offline: true });const file = await offline.newPage()
  await file.goto(pathToFileURL(path.resolve('public/gto-demo/index.html')).href)
  assert.equal(await file.locator('#grid button').count(), 169)
  await file.locator('[data-stage="vs_4bet"]').click();await file.locator('[data-hand="AKo"]').click()
  assert.equal(await file.locator('#hand').textContent(), 'AKo')
  await offline.close();console.log('PASS D06 single HTML remains interactive offline via file URL')
} finally {if (browser) await browser.close();await new Promise(resolve => server.close(resolve))}
