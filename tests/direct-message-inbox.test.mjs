import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import { chromium } from 'playwright-core'
const root = fileURLToPath(new URL('../', import.meta.url))
async function withInbox(fn) {
  const cacheDir = await fs.mkdtemp(path.join(os.tmpdir(), 'pokerid-dm-'))
  const server = await createServer({ root, cacheDir, configFile: false, server: { host: '127.0.0.1', port: 0 },
    esbuild: { jsx: 'automatic' }, plugins: [{ name: 'isolated-dm', enforce: 'pre',
      resolveId(source, importer) { if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/dm-inbox-supabase.ts') },
      configureServer(s) { s.middlewares.use('/__inbox', (_req, res) => { res.setHeader('Content-Type', 'text/html'); res.end('<div id="root"></div><script type="module" src="/tests/browser/dm-inbox-entry.tsx"></script>') }) },
    }] })
  let browser
  try {
    await server.listen(); const base = `http://127.0.0.1:${server.httpServer.address().port}`
    browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } }); page.setDefaultTimeout(1800)
    await page.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort())
    await page.goto(base + '/__inbox')
    await fn(page)
  } finally { await browser?.close(); await server.close(); await fs.rm(cacheDir, { recursive: true, force: true }) }
}
async function ready(page) { await page.getByText('PRIVATE_OLD_MESSAGE', { exact: true }).waitFor() }
async function retry(page) { await page.getByRole('button', { name: 'DM一覧を再読み込み', exact: true }).click() }
test('inbox immediately removes private previews on signout and unsubscribes', () => withInbox(async page => {
 await ready(page); await page.evaluate(() => window.inboxQA.emit(null)); await page.getByText('Synthetic login').waitFor()
 assert.doesNotMatch(await page.locator('body').innerText(), /PRIVATE_OLD_MESSAGE/)
 assert.equal(await page.evaluate(() => window.inboxQA.channels.filter(c => c.active).length), 0)
}))
test('inbox account switch loads only the new identity and cleans old realtime', () => withInbox(async page => {
 await ready(page); await page.evaluate(() => window.inboxQA.emit('newme')); await page.getByText('PRIVATE_NEW_MESSAGE', { exact: true }).waitFor()
 assert.doesNotMatch(await page.locator('body').innerText(), /PRIVATE_OLD_MESSAGE/)
 assert.equal(await page.evaluate(() => window.inboxQA.channels.filter(c => c.active).length), 1)
 assert.equal(await page.evaluate(() => window.inboxQA.reentrant), 0)
}))
test('inbox transport failure offers explicit redacted recovery', () => withInbox(async page => {
 await ready(page); await page.evaluate(() => { window.inboxQA.rejectMessages = true; window.inboxQA.realtime() })
 await page.getByRole('button', { name: 'DM一覧を再読み込み', exact: true }).waitFor()
 assert.doesNotMatch(await page.locator('body').innerText(), /SYNTHETIC_PRIVATE|PRIVATE_OLD_MESSAGE/)
 await retry(page); await ready(page)
}))
test('inbox profile transport failure can recover without private backend text', () => withInbox(async page => {
 await ready(page); await page.evaluate(() => { window.inboxQA.rejectProfiles = true; window.inboxQA.realtime() })
 await page.getByRole('button', { name: 'DM一覧を再読み込み', exact: true }).waitFor(); assert.doesNotMatch(await page.locator('body').innerText(), /SYNTHETIC_PRIVATE/)
 await retry(page); await ready(page)
}))
test('inbox older reload cannot replace the latest realtime snapshot', () => withInbox(async page => {
 await ready(page); await page.evaluate(() => { window.inboxQA.holdMessages = true; window.inboxQA.realtime() })
 await page.waitForFunction(() => window.inboxQA.pending.length === 1)
 await page.evaluate(() => { window.inboxQA.holdMessages = false; window.inboxQA.content = 'LATEST_MESSAGE'; window.inboxQA.realtime() })
 await page.getByText('LATEST_MESSAGE', { exact: true }).waitFor(); await page.evaluate(() => window.inboxQA.release()); await page.waitForTimeout(60)
 assert.match(await page.locator('body').innerText(), /LATEST_MESSAGE/); assert.doesNotMatch(await page.locator('body').innerText(), /LATE_OLD_MESSAGE/)
}))
test('inbox pending old account result never appears after switch', () => withInbox(async page => {
 await ready(page); await page.evaluate(() => { window.inboxQA.holdMessages = true; window.inboxQA.realtime() }); await page.waitForFunction(() => window.inboxQA.pending.length === 1)
 await page.evaluate(() => { window.inboxQA.holdMessages = false; window.inboxQA.emit('newme') }); await page.getByText('PRIVATE_NEW_MESSAGE', { exact: true }).waitFor()
 await page.evaluate(() => window.inboxQA.release()); await page.waitForTimeout(60); assert.doesNotMatch(await page.locator('body').innerText(), /LATE_OLD_MESSAGE/)
}))
test('inbox excludes unrelated returned rows and sends an ownership filter', () => withInbox(async page => {
 await ready(page); await page.evaluate(() => { window.inboxQA.extraRows = [{ id: 'unrelated', sender_id: 'stranger', receiver_id: 'someone', content: 'UNRELATED_PRIVATE', created_at: '2026-10-25T01:00:00Z', read_at: null }]; window.inboxQA.realtime() })
 await page.waitForTimeout(80); assert.doesNotMatch(await page.locator('body').innerText(), /UNRELATED_PRIVATE/)
 assert.match(await page.evaluate(() => window.inboxQA.filters.at(-1)), /sender_id.eq.me,receiver_id.eq.me/)
}))
test('inbox auth failure with user data fails closed and permits recovery', () => withInbox(async page => {
 await ready(page); const before = await page.evaluate(() => window.inboxQA.messageReads)
 await page.evaluate(() => { window.inboxQA.errorAuth = true; window.inboxQA.realtime() }); await page.getByRole('button', { name: 'DM一覧を再読み込み', exact: true }).waitFor()
 assert.equal(await page.evaluate(() => window.inboxQA.messageReads), before)
 await page.evaluate(() => { window.inboxQA.errorAuth = false }); await retry(page); await ready(page)
}))
