import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import { chromium } from 'playwright-core'
const root = fileURLToPath(new URL('../', import.meta.url))
async function withChat(fn) {
  const cacheDir = await fs.mkdtemp(path.join(os.tmpdir(), 'pokerid-dm-'))
  const server = await createServer({ root, cacheDir, configFile: false, server: { host: '127.0.0.1', port: 0 },
    esbuild: { jsx: 'automatic' }, plugins: [{ name: 'isolated-dm', enforce: 'pre',
      resolveId(source, importer) { if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/dm-supabase.ts') },
      configureServer(s) { s.middlewares.use('/__dm', (_req, res) => { res.setHeader('Content-Type', 'text/html'); res.end('<div id="root"></div><script type="module" src="/tests/browser/dm-entry.tsx"></script>') }) },
    }] })
  let browser
  try {
    await server.listen(); const base = `http://127.0.0.1:${server.httpServer.address().port}`
    browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
    await page.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort())
    await page.goto(base + '/__dm'); await page.locator('header').getByText('Synthetic player', { exact: true }).waitFor()
    await page.getByPlaceholder('メッセージ...').fill('Synthetic message')
    await fn(page)
  } finally { await browser?.close(); await server.close(); await fs.rm(cacheDir, { recursive: true, force: true }) }
}
async function enter(page) { await page.getByPlaceholder('メッセージ...').press('Enter') }
test('DM repeated Enter during block verification sends exactly once', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.holdBlocks = true })
  await enter(page); await enter(page)
  await page.waitForTimeout(50)
  const checks = await page.evaluate(() => window.dmQA.checks.length)
  await page.evaluate(() => window.dmQA.release())
  await page.waitForFunction(() => window.dmQA.inserts.length > 0)
  await page.waitForTimeout(60)
  assert.equal(checks, 1); assert.equal(await page.evaluate(() => window.dmQA.inserts.length), 1)
}))
test('DM repeated Enter while insert is pending cannot create another message', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.holdInsert = true })
  await enter(page); await page.waitForFunction(() => window.dmQA.inserts.length === 1)
  await enter(page); await page.waitForTimeout(60)
  const count = await page.evaluate(() => window.dmQA.inserts.length)
  await page.evaluate(() => window.dmQA.finish())
  assert.equal(count, 1)
}))
test('DM rejected transport unlocks retry and does not display backend details', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.rejectInsert = true })
  await enter(page)
  await page.waitForFunction(() => !document.querySelector('button[aria-label="送信"]').disabled, null, { timeout: 1200 })
  const text = await page.locator('body').innerText()
  assert.match(text, /送信.*(失敗|できません)/); assert.doesNotMatch(text, /SYNTHETIC_PRIVATE_ERROR/)
  await enter(page); await page.waitForFunction(() => window.dmQA.inserts.length === 2)
}))
