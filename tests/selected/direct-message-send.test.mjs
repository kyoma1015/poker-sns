import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import { chromium } from 'playwright-core'
const root = fileURLToPath(new URL('../../', import.meta.url))
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
test('DM returned insert error preserves draft, redacts details and permits explicit retry', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.errorInsert = true })
  await enter(page)
  await page.getByText('DMを送信できませんでした。もう一度お試しください。', { exact: true }).waitFor()
  assert.equal(await page.getByPlaceholder('メッセージ...').inputValue(), 'Synthetic message')
  assert.doesNotMatch(await page.locator('body').innerText(), /SYNTHETIC_PRIVATE_ERROR/)
  await enter(page); await page.waitForFunction(() => window.dmQA.inserts.length === 2)
}))
test('DM block verification error fails closed without writing', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.blockError = true })
  await enter(page)
  await page.getByText('ブロック中のためメッセージを送信できません。', { exact: true }).waitFor()
  assert.equal(await page.evaluate(() => window.dmQA.inserts.length), 0)
}))
test('DM accepted write followed by reload failure is reported as sent without restoring draft', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.rejectReload = true })
  await enter(page)
  await page.getByText('送信しましたが、表示の更新に失敗しました。ページを再読み込みしてください。', { exact: true }).waitFor()
  assert.equal(await page.evaluate(() => window.dmQA.inserts.length), 1)
  assert.equal(await page.getByPlaceholder('メッセージ...').inputValue(), '')
  assert.doesNotMatch(await page.locator('body').innerText(), /SYNTHETIC_PRIVATE_ERROR/)
}))
test('DM whitespace and IME composition never write a message', () => withChat(async page => {
  await page.getByPlaceholder('メッセージ...').fill('   '); await enter(page)
  await page.getByPlaceholder('メッセージ...').fill('Synthetic message')
  await page.getByPlaceholder('メッセージ...').evaluate(input => input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', isComposing: true, bubbles: true })))
  assert.equal(await page.evaluate(() => window.dmQA.inserts.length), 0)
}))
test('DM a late response from the previous conversation cannot replace the current messages', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.holdOldMessages = true; window.dmQA.holdInsert = true })
  await enter(page); await page.waitForFunction(() => window.dmQA.inserts.length === 1)
  await page.evaluate(() => window.dmQA.finish())
  await page.waitForFunction(() => window.dmQA.oldMessages.length === 1)
  await page.evaluate(() => window.dmQA.navigate('/dm/third'))
  await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
  await page.getByPlaceholder('メッセージ...').fill('New conversation draft')
  await page.evaluate(() => window.dmQA.oldMessages.splice(0).forEach(done => done({ data: [{ id: 'old-message', sender_id: 'other', receiver_id: 'me', content: 'OTHER_SYNTHETIC', created_at: '2026-10-24T00:00:00Z', read_at: null }], error: null })))
  await page.waitForTimeout(80)
  const body = await page.locator('body').innerText()
  assert.match(body, /THIRD_SYNTHETIC/); assert.doesNotMatch(body, /OTHER_SYNTHETIC/)
  assert.equal(await page.getByPlaceholder('メッセージ...').inputValue(), 'New conversation draft')
}))
test('DM leaving and returning to the same peer cannot let an old send clear a new draft', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.holdInsert = true })
  await enter(page); await page.waitForFunction(() => window.dmQA.inserts.length === 1)
  await page.evaluate(() => window.dmQA.navigate('/dm/third'))
  await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
  await page.evaluate(() => window.dmQA.navigate('/dm/other'))
  await page.locator('header').getByText('Synthetic player', { exact: true }).waitFor()
  await page.getByPlaceholder('メッセージ...').fill('New visit draft')
  await page.evaluate(() => window.dmQA.finish())
  await page.waitForTimeout(80)
  assert.equal(await page.getByPlaceholder('メッセージ...').inputValue(), 'New visit draft')
}))
test('DM sign out clears private messages and draft without waiting for another request', () => withChat(async page => {
  await page.evaluate(() => window.dmQA.navigate('/dm/third'))
  await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
  await page.getByPlaceholder('メッセージ...').fill('Private old draft')
  await page.evaluate(() => window.dmQA.emitAuth(null))
  await page.waitForTimeout(80)
  const body = await page.locator('body').innerText()
  assert.doesNotMatch(body, /THIRD_SYNTHETIC|Private old draft/)
  assert.equal(await page.getByPlaceholder('メッセージ...').count(), 0)
}))
test('DM switching account remounts the conversation without retaining old private data', () => withChat(async page => {
  await page.evaluate(() => window.dmQA.navigate('/dm/third'))
  await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
  await page.getByPlaceholder('メッセージ...').fill('Private old draft')
  await page.evaluate(() => window.dmQA.emitAuth('newme'))
  await page.waitForTimeout(80)
  assert.match(await page.locator('body').innerText(), /NEW_ACCOUNT_SYNTHETIC/)
  assert.doesNotMatch(await page.locator('body').innerText(), /THIRD_SYNTHETIC/)
  assert.equal(await page.getByPlaceholder('メッセージ...').inputValue(), '')
}))
test('DM pending authorization check cannot write after sign out', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.holdBlocks = true })
  await enter(page); await page.waitForFunction(() => window.dmQA.checks.length === 1)
  await page.evaluate(() => { window.dmQA.emitAuth(null); window.dmQA.release() })
  await page.waitForTimeout(80)
  assert.equal(await page.evaluate(() => window.dmQA.inserts.length), 0)
}))
test('DM revalidates authenticated identity before a write if its auth event was missed', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.userId = 'newme' })
  await enter(page); await page.waitForTimeout(100)
  assert.equal(await page.evaluate(() => window.dmQA.inserts.length), 0)
}))
test('DM same-account token refresh preserves the unsent draft', () => withChat(async page => {
  await page.evaluate(() => window.dmQA.emitAuth('me', 'TOKEN_REFRESHED'))
  await page.waitForTimeout(50)
  assert.equal(await page.getByPlaceholder('メッセージ...').inputValue(), 'Synthetic message')
}))
test('DM auth callbacks do not call Supabase reentrantly and unsubscribe on exit', () => withChat(async page => {
  await page.evaluate(() => window.dmQA.emitAuth('newme'))
  await page.locator('header').getByText('Synthetic player', { exact: true }).waitFor()
  await page.waitForTimeout(60)
  assert.equal(await page.evaluate(() => window.dmQA.authCallsInsideCallback), 0)
  assert.equal(await page.evaluate(() => window.dmQA.authListeners.size), 1)
  await page.evaluate(() => window.dmQA.navigate('/login'))
  await page.getByText('Synthetic login', { exact: true }).waitFor()
  assert.equal(await page.evaluate(() => window.dmQA.authListeners.size), 0)
}))
test('DM queued Realtime delivery cannot mark old messages read after synchronous signout', () => withChat(async page => {
  await page.waitForFunction(() => window.dmQA.channels.length > 0)
  const counts = await page.evaluate(() => {
    const before = window.dmQA.readUpdates
    const old = window.dmQA.channels[0]
    window.dmQA.emitAuth(null)
    old.handler({ eventType: 'INSERT', new: { id: 'late', sender_id: 'other', receiver_id: 'me', content: 'LATE_PRIVATE', created_at: '2026-10-25T00:00:00Z', read_at: null } })
    return { before, after: window.dmQA.readUpdates }
  })
  assert.equal(counts.after, counts.before)
  await page.waitForTimeout(60)
  assert.doesNotMatch(await page.locator('body').innerText(), /LATE_PRIVATE/)
}))
test('DM duplicate current-conversation INSERT events reload one saved row without duplicating it', () => withChat(async page => {
  await page.evaluate(() => window.dmQA.navigate('/dm/third'))
  await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
  await page.evaluate(async () => {
    const channel = window.dmQA.channels.findLast(channel => channel.active)
    const payload = { eventType: 'INSERT', new: { id: 'third-message', sender_id: 'third', receiver_id: 'me', content: 'THIRD_SYNTHETIC', created_at: '2026-10-24T00:00:00Z', read_at: null } }
    await Promise.all([channel.handler(payload), channel.handler(payload)])
  })
  assert.equal(await page.getByText('THIRD_SYNTHETIC', { exact: true }).count(), 1)
}))
test('DM initial authentication rejection shows redacted recoverable read guidance', () => withChat(async page => {
  await page.evaluate(() => { window.dmQA.rejectUserOnce = true; window.dmQA.navigate('/dm/third') })
  const retry = page.getByRole('button', { name: 'DMを再読み込み', exact: true })
  await retry.waitFor({ timeout: 1200 })
  assert.doesNotMatch(await page.locator('body').innerText(), /SYNTHETIC_PRIVATE_AUTH/)
  await retry.click(); await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
}))
test('DM returned auth error never trusts accompanying user data or marks messages read', () => withChat(async page => {
  const before = await page.evaluate(() => { const before = window.dmQA.readUpdates; window.dmQA.errorUserOnce = true; window.dmQA.navigate('/dm/third'); return before })
  await page.waitForTimeout(80)
  assert.equal(await page.evaluate(() => window.dmQA.readUpdates), before)
  const retry = page.getByRole('button', { name: 'DMを再読み込み', exact: true })
  await retry.waitFor({ timeout: 1200 })
  assert.doesNotMatch(await page.locator('body').innerText(), /SYNTHETIC_PRIVATE_AUTH/)
  await retry.click(); await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
}))

async function conversationRows(page, rows) {
  await page.evaluate(async rows => {
    window.dmQA.extraRows = rows
    const channel = window.dmQA.channels.findLast(channel => channel.active)
    await channel.handler({ eventType: 'INSERT', new: { id: 'third-message', sender_id: 'third', receiver_id: 'me', content: 'THIRD_SYNTHETIC', created_at: '2026-10-24T00:00:00Z', read_at: null } })
  }, rows)
}
const syntheticRow = (id, sender_id, receiver_id, content) => ({ id, sender_id, receiver_id, content, created_at: '2026-10-24T00:00:00Z', read_at: null })
test('conversation rejects query rows for two unrelated actors', () => withChat(async page => {
  await page.evaluate(() => window.dmQA.navigate('/dm/third'))
  await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
  await conversationRows(page, [syntheticRow('foreign', 'stranger', 'someone', 'FOREIGN_CONVERSATION_PRIVATE')])
  await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
  assert.equal(await page.getByText('FOREIGN_CONVERSATION_PRIVATE', { exact: true }).count(), 0)
}))
test('conversation rejects same-account rows belonging to another peer', () => withChat(async page => {
  await page.evaluate(() => window.dmQA.navigate('/dm/third'))
  await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
  await conversationRows(page, [
    syntheticRow('other-out', 'me', 'other', 'OTHER_PEER_OUTGOING_PRIVATE'),
    syntheticRow('other-in', 'other', 'me', 'OTHER_PEER_INCOMING_PRIVATE'),
  ])
  await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
  assert.equal(await page.getByText('OTHER_PEER_OUTGOING_PRIVATE', { exact: true }).count(), 0)
  assert.equal(await page.getByText('OTHER_PEER_INCOMING_PRIVATE', { exact: true }).count(), 0)
}))
test('conversation preserves both valid directions after defensive query filtering', () => withChat(async page => {
  await page.evaluate(() => window.dmQA.navigate('/dm/third'))
  await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
  await conversationRows(page, [syntheticRow('valid-out', 'me', 'third', 'CURRENT_PEER_OUTGOING')])
  await page.getByText('CURRENT_PEER_OUTGOING', { exact: true }).waitFor()
  assert.equal(await page.getByText('THIRD_SYNTHETIC', { exact: true }).count(), 1)
}))

test('conversation malformed matching query content cannot crash the current conversation', () => withChat(async page => {
 await page.evaluate(() => window.dmQA.navigate('/dm/third'))
 await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
 const errors=[];page.on('pageerror',e=>errors.push(e.message))
 await conversationRows(page,[syntheticRow('malformed','me','third',{private:'NOT_RENDERABLE'})])
 await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))))
 assert.deepEqual(errors,[])
 assert.equal(await page.getByText('THIRD_SYNTHETIC',{exact:true}).count(),1)
}))
test('conversation malformed matching realtime UPDATE cannot crash or replace saved content', () => withChat(async page => {
 await page.evaluate(() => window.dmQA.navigate('/dm/third'))
 await page.getByText('THIRD_SYNTHETIC', { exact: true }).waitFor()
 const errors=[];page.on('pageerror',e=>errors.push(e.message))
 await page.evaluate(async()=>{
  const channel=window.dmQA.channels.findLast(channel=>channel.active)
  await channel.handler({eventType:'UPDATE',new:{id:'third-message',sender_id:'third',receiver_id:'me',content:{private:'NOT_RENDERABLE'},created_at:'2026-10-24T00:00:00Z',read_at:null}})
 })
 await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))))
 assert.deepEqual(errors,[])
 assert.equal(await page.getByText('THIRD_SYNTHETIC',{exact:true}).count(),1)
}))

for (const mode of ['switched-account','auth-error','auth-rejected']) {
 test('DM read acknowledgement revalidates identity after profile wait: '+mode, () => withChat(async page => {
  await page.waitForFunction(()=>window.dmQA.readUpdates===1)
  const before=await page.evaluate(()=>{const n=window.dmQA.readUpdates;window.dmQA.holdProfiles=true;window.dmQA.navigate('/dm/third');return n})
  await page.waitForFunction(()=>window.dmQA.profileWaiters.length===1)
  await page.evaluate(mode=>{
   if(mode==='switched-account')window.dmQA.userId='newme'
   if(mode==='auth-error')window.dmQA.errorUserOnce=true
   if(mode==='auth-rejected')window.dmQA.rejectUserOnce=true
   window.dmQA.releaseProfiles()
  },mode)
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))))
  assert.equal(await page.evaluate(()=>window.dmQA.readUpdates),before,'unverified acknowledgement must issue no UPDATE')
  await page.getByRole('button',{name:'DMを再読み込み',exact:true}).waitFor({timeout:1200})
  assert.doesNotMatch(await page.locator('body').innerText(),/SYNTHETIC_PRIVATE_AUTH|THIRD_SYNTHETIC|NEW_ACCOUNT_SYNTHETIC/)
 }))
}
test('DM delayed valid profile still acknowledges the incoming conversation once',()=>withChat(async page=>{
 await page.waitForFunction(()=>window.dmQA.readUpdates===1)
 const before=await page.evaluate(()=>{const n=window.dmQA.readUpdates;window.dmQA.holdProfiles=true;window.dmQA.navigate('/dm/third');return n})
 await page.waitForFunction(()=>window.dmQA.profileWaiters.length===1)
 await page.evaluate(()=>window.dmQA.releaseProfiles())
 await page.getByText('THIRD_SYNTHETIC',{exact:true}).waitFor()
 assert.equal(await page.evaluate(()=>window.dmQA.readUpdates),before+1)
}))

for(const mode of ['switched-account','auth-error','auth-rejected']){
 test('DM send revalidates identity after block wait: '+mode,()=>withChat(async page=>{
  await page.evaluate(()=>{window.dmQA.holdBlocks=true})
  await enter(page)
  await page.waitForFunction(()=>window.dmQA.checks.length===1)
  await page.evaluate(mode=>{
   if(mode==='switched-account')window.dmQA.userId='newme'
   if(mode==='auth-error')window.dmQA.errorUserOnce=true
   if(mode==='auth-rejected')window.dmQA.rejectUserOnce=true
   window.dmQA.release()
  },mode)
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))))
  assert.equal(await page.evaluate(()=>window.dmQA.inserts.length),0,'unverified sender must issue no INSERT')
  assert.doesNotMatch(await page.locator('body').innerText(),/SYNTHETIC_PRIVATE_AUTH/)
 }))
}
test('DM delayed valid block check still sends one message',()=>withChat(async page=>{
 await page.evaluate(()=>{window.dmQA.holdBlocks=true})
 await enter(page);await page.waitForFunction(()=>window.dmQA.checks.length===1)
 await page.evaluate(()=>window.dmQA.release())
 await page.waitForFunction(()=>window.dmQA.inserts.length===1)
 assert.equal(await page.evaluate(()=>window.dmQA.inserts.length),1)
}))

for(const mode of ['switched-account','auth-error','auth-rejected']){
 test('DM realtime acknowledgement uses the authenticated load path: '+mode,()=>withChat(async page=>{
  await page.evaluate(()=>window.dmQA.navigate('/dm/third'))
  await page.getByText('THIRD_SYNTHETIC',{exact:true}).waitFor()
  const before=await page.evaluate(()=>window.dmQA.readUpdates)
  await page.evaluate(async mode=>{
   if(mode==='switched-account')window.dmQA.userId='newme'
   if(mode==='auth-error')window.dmQA.errorUserOnce=true
   if(mode==='auth-rejected')window.dmQA.rejectUserOnce=true
   const channel=window.dmQA.channels.findLast(channel=>channel.active)
   await channel.handler({eventType:'INSERT',new:{id:'late',sender_id:'third',receiver_id:'me',content:'LATE_ACK_PRIVATE',created_at:'2026-10-28T00:00:00Z',read_at:null}})
  },mode)
  assert.equal(await page.evaluate(()=>window.dmQA.readUpdates),before)
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))))
  assert.doesNotMatch(await page.locator('body').innerText(),/LATE_ACK_PRIVATE|SYNTHETIC_PRIVATE_AUTH/)
 }))
}

test('DM current incoming realtime event uses one read acknowledgement path',()=>withChat(async page=>{
 await page.evaluate(()=>window.dmQA.navigate('/dm/third'))
 await page.getByText('THIRD_SYNTHETIC',{exact:true}).waitFor()
 const before=await page.evaluate(()=>window.dmQA.readUpdates)
 await page.evaluate(async()=>{
  const channel=window.dmQA.channels.findLast(channel=>channel.active)
  await channel.handler({eventType:'INSERT',new:{id:'third-message',sender_id:'third',receiver_id:'me',content:'THIRD_SYNTHETIC',created_at:'2026-10-24T00:00:00Z',read_at:null}})
 })
 assert.equal(await page.evaluate(()=>window.dmQA.readUpdates),before+1)
 assert.equal(await page.getByText('THIRD_SYNTHETIC',{exact:true}).count(),1)
}))
