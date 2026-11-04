import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import { chromium } from 'playwright-core'
const root = fileURLToPath(new URL('../../', import.meta.url))
async function withNotifications(fn) {
  const cacheDir = await fs.mkdtemp(path.join(os.tmpdir(), 'pokerid-dm-'))
  const server = await createServer({ root, cacheDir, configFile: false, server: { host: '127.0.0.1', port: 0 },
    esbuild: { jsx: 'automatic' }, plugins: [{ name: 'isolated-dm', enforce: 'pre',
      resolveId(source, importer) { if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/notifications-flow-supabase.ts') },
      configureServer(s) { s.middlewares.use('/__notifications', (_req, res) => { res.setHeader('Content-Type', 'text/html'); res.end('<div id="root"></div><script type="module" src="/tests/browser/notifications-flow-entry.tsx"></script>') }) },
    }] })
  let browser
  try {
    await server.listen(); const base = `http://127.0.0.1:${server.httpServer.address().port}`
    browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } }); page.setDefaultTimeout(1800)
    await page.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort())
    await page.goto(base + '/__notifications')
    await fn(page)
  } finally { await browser?.close(); await server.close(); await fs.rm(cacheDir, { recursive: true, force: true }) }
}
async function ready(page){await page.getByText('PRIVATE_ACTOR_A',{exact:true}).waitFor()}
async function retry(page){await page.getByRole('button',{name:'通知を再読み込み',exact:true}).click()}
test('notifications signout removes private actor and subscription',()=>withNotifications(async page=>{await ready(page);await page.evaluate(()=>window.notificationQA.emit(null));await page.getByText('Synthetic login').waitFor();assert.doesNotMatch(await page.locator('body').innerText(),/PRIVATE_ACTOR_A/);assert.equal(await page.evaluate(()=>window.notificationQA.channels.filter(c=>c.active).length),0)}))
test('notifications switch account replaces private state and scopes realtime',()=>withNotifications(async page=>{await ready(page);await page.evaluate(()=>window.notificationQA.emit('newme'));await page.getByText('PRIVATE_ACTOR_B',{exact:true}).waitFor();assert.doesNotMatch(await page.locator('body').innerText(),/PRIVATE_ACTOR_A/);assert.equal(await page.evaluate(()=>window.notificationQA.reentrant),0);assert.equal(await page.evaluate(()=>window.notificationQA.channels.filter(c=>c.active)[0].filter.filter),'user_id=eq.newme')}))
test('notifications pending profile cannot mark old account read after switch',()=>withNotifications(async page=>{await ready(page);await page.evaluate(()=>{window.notificationQA.holdProfile=true;window.notificationQA.realtime()});await page.waitForFunction(()=>window.notificationQA.pendingProfiles.length===1);await page.evaluate(()=>{window.notificationQA.holdProfile=false;window.notificationQA.emit('newme')});await page.getByText('PRIVATE_ACTOR_B',{exact:true}).waitFor();const count=await page.evaluate(()=>window.notificationQA.updates.length);await page.evaluate(()=>window.notificationQA.releaseProfile());await page.waitForTimeout(60);assert.equal(await page.evaluate(()=>window.notificationQA.updates.length),count);assert.doesNotMatch(await page.locator('body').innerText(),/LATE_OLD_ACTOR/)}))
test('notifications failed reads recover explicitly without backend details',()=>withNotifications(async page=>{await ready(page);await page.evaluate(()=>{window.notificationQA.failRead=true;window.notificationQA.realtime()});await page.getByRole('button',{name:'通知を再読み込み',exact:true}).waitFor();assert.doesNotMatch(await page.locator('body').innerText(),/SYNTHETIC_PRIVATE_DB/);await retry(page);await ready(page)}))
test('notifications update uses owner filter and handles zero-row denial',()=>withNotifications(async page=>{await ready(page);assert.equal(await page.evaluate(()=>window.notificationQA.updates[0].filters.user_id),'me');await page.evaluate(()=>{window.notificationQA.zeroMark=true;window.notificationQA.realtime()});await page.getByRole('button',{name:'通知を再読み込み',exact:true}).waitFor();assert.match(await page.locator('body').innerText(),/既読/);await page.evaluate(()=>{window.notificationQA.zeroMark=false});await retry(page);await ready(page)}))
test('notifications reject auth error even when user is returned',()=>withNotifications(async page=>{await ready(page);const before=await page.evaluate(()=>window.notificationQA.updates.length);await page.evaluate(()=>{window.notificationQA.authError=true;window.notificationQA.realtime()});await page.getByRole('button',{name:'通知を再読み込み',exact:true}).waitFor();assert.equal(await page.evaluate(()=>window.notificationQA.updates.length),before);assert.doesNotMatch(await page.locator('body').innerText(),/PRIVATE_ACTOR_A|SYNTHETIC_PRIVATE_AUTH/)}))
test('notifications filter unexpected foreign rows and navigate own event to post',()=>withNotifications(async page=>{await ready(page);await page.evaluate(()=>{window.notificationQA.outsider=true;window.notificationQA.realtime()});await page.waitForTimeout(80);assert.doesNotMatch(await page.locator('body').innerText(),/OUTSIDER_PRIVATE/);await page.getByText('あなたの投稿にいいねしました',{exact:false}).last().click();await page.getByText('Synthetic post').waitFor()}))
