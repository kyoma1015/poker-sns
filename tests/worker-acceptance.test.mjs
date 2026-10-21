import assert from 'node:assert/strict'
import test from 'node:test'
import path from 'node:path'
import os from 'node:os'
import { mkdtemp, rm } from 'node:fs/promises'
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
