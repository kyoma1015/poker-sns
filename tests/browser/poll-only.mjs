// Run with a separately installed playwright-core; browser never contacts a DB.
import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { createServer } from 'vite'
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright-core')
const root = fileURLToPath(new URL('../../', import.meta.url))
const server = await createServer({ root, configFile: false, server: { host: '127.0.0.1', port: 0 },
  plugins: [{ name: 'qa-only-supabase', enforce: 'pre', resolveId(source, importer) {
    if (source === './supabase' && importer?.includes('/src/')) return path.join(root, 'tests/browser/supabase.ts')
  }, configureServer(server) { server.middlewares.use('/__qa', (req,res) => {
    res.setHeader('Content-Type', 'text/html'); res.end('<div id="root"></div><script type="module" src="/tests/browser/entry.tsx"></script>')
  }) } }], esbuild: { jsx: 'automatic' } })
let browser
const results = []
try {
  await server.listen()
  const base = `http://127.0.0.1:${server.httpServer.address().port}`
  browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] })
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort())
  const check = (name, fn) => fn().then(() => { results.push(name); console.log('PASS', name) })
  await check('home composer has only poll creation and submits named poll', async () => {
    await page.goto(base + '/__qa')
    await page.getByRole('button', { name: '📊 アンケート', exact: true }).click()
    assert.equal(await page.getByText('質問箱').count(), 0)
    await page.locator('#poker-id-post-composer').fill('Browser poll')
    await page.getByLabel('選択肢1', { exact: true }).fill('A')
    await page.getByLabel('選択肢2', { exact: true }).fill('B')
    await page.getByRole('button', { name: '投稿', exact: true }).click()
    await page.waitForFunction(() => window.qaRpcCalls.some(call => call.name === 'create_interactive_post_v4'))
    const calls = await page.evaluate(() => window.qaRpcCalls)
    assert.equal(calls.find(call => call.name === 'create_interactive_post_v4').args.p_kind, 'poll')
    assert.equal(calls.find(call => call.name === 'create_interactive_post_v4').args.p_is_anonymous, false)
  })
  await check('bottom-nav compose event opens poll-only composer and submits anonymous poll', async () => {
    await page.evaluate(() => window.dispatchEvent(new Event('poker-id-open-compose')))
    const dialog = page.getByRole('dialog', { name: '新しい投稿' })
    await dialog.waitFor()
    assert.equal(await dialog.getByText('質問箱').count(), 0)
    await dialog.getByRole('button', { name: '📊 アンケート', exact: true }).click()
    await dialog.locator('textarea').fill('Anonymous poll')
    await dialog.getByLabel('選択肢1', { exact: true }).fill('A')
    await dialog.getByLabel('選択肢2', { exact: true }).fill('B')
    await dialog.getByRole('button', { name: '匿名投票', exact: true }).click()
    await dialog.getByRole('button', { name: '投稿する', exact: true }).click()
    await page.waitForFunction(() => window.qaRpcCalls.filter(call => call.name === 'create_interactive_post_v4').length === 2)
    assert.equal(await page.evaluate(() => window.qaRpcCalls.filter(call => call.name === 'create_interactive_post_v4')[1].args.p_is_anonymous), true)
  })
  await check('anonymous card hides voter identities and voter-list actions', async () => {
    await page.goto(base + '/__qa?case=anonymous')
    await page.getByText('アンケート（匿名）', { exact: false }).waitFor()
    assert.equal(await page.getByRole('button', { name: '回答者一覧を見る' }).count(), 0)
    assert.doesNotMatch(await page.locator('body').innerText(), /qa-identity-secret|QA Named User/)
  })
  await check('named card exposes named voter list as disclosed', async () => {
    await page.goto(base + '/__qa?case=named')
    await page.getByRole('button', { name: '回答者一覧を見る' }).click()
    await page.getByRole('dialog', { name: '投票者一覧' }).getByText('QA Named User').waitFor()
  })
  await check('historical question card stays unmounted with zero RPC writes', async () => {
    await page.goto(base + '/__qa?case=question')
    await page.waitForFunction(() => window.qaRpcCalls !== undefined)
    assert.equal(await page.locator('#root').innerText(), '')
    assert.deepEqual(await page.evaluate(() => window.qaRpcCalls), [])
  })
  assert.deepEqual(errors, [])
  console.log(JSON.stringify({ verdict: 'PASS', tests: results.length, results, browser: await browser.version(), transport: 'in-memory mock; external requests blocked; no DB' }))
} finally { await browser?.close(); await server.close() }
