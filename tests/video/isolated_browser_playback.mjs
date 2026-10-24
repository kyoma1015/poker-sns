// Actual React PostVideo in headless Chromium, backed by isolated Supabase
// through the real authorized media API. Never used in production builds.
import assert from 'node:assert/strict'
import { createServer as createHttpServer } from 'node:http'
import { createServer as createViteServer } from 'vite'
import { chromium } from 'playwright-core'
import { createVideoMediaHandler } from '../../api/video-media.ts'

export async function verifyRealBrowserPlayback({ postId, jwt, deniedJwt }) {
  assert.equal(process.env.VITE_SUPABASE_URL, 'http://127.0.0.1:56321')
  const vite = await createViteServer({
    configFile: false,
    server: { middlewareMode: true, hmr: false },
    plugins: [{
      name: 'isolated-video-api-test-only',
      enforce: 'pre',
      transform(source, id) {
        const filename=id.split('?')[0]
        if (filename.endsWith('/src/supabase.ts')) {
          // Only the session source is injected. The real videoApi.ts
          // loadAuthorizedVideo implementation and PostVideo component run.
          return `export const supabase = {
            auth: { getSession: async () => ({
              data: { session: { access_token: window.__VIDEO_QA_JWT } },
              error: null,
            }) },
          }`
        }
        if (filename.endsWith('/src/videoApi.ts')) {
          assert.ok(source.includes('VIDEO_SERVER_ENABLED = false as boolean'),
            'production video feature gate unexpectedly changed')
          return source.replace('VIDEO_SERVER_ENABLED = false as boolean',
            'VIDEO_SERVER_ENABLED = true as boolean')
        }
        return null

      },
    }],
  })
  const handler = createVideoMediaHandler({ isolatedLocalOnly: true })
  const server = createHttpServer((req, res) => {
    const match = /^\/internal\/video\/media\/([0-9a-f-]{36})$/.exec(req.url || '')
    if (match) {
      const response = {
        setHeader: (name, value) => { res.setHeader(name, value); return response },
        status: code => { res.statusCode = code; return response },
        send: bytes => { res.end(bytes); return response },
        end: () => { res.end(); return response },
      }
      void handler({ method: req.method, headers: req.headers,
        query: { post_id: match[1] } }, response).catch(() => {
        if (!res.headersSent) res.statusCode = 503
        if (!res.writableEnded) res.end()
      })
      return
    }
    vite.middlewares(req, res)
  })
  let browser
  try {
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
    const address = server.address()
    assert.ok(address && typeof address !== 'string')
    browser = await chromium.launch({
      headless: true, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] })
    const origin = 'http://127.0.0.1:' + address.port
    const page = await browser.newPage()
    const errors = []
    page.on('pageerror', error => errors.push(String(error)))
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
    page.on('response', response => { if (response.url().includes('/internal/video/media/')) console.log('Chromium media HTTP status:',response.status()) })
    await page.addInitScript(({postId,jwt}) => {
      window.__VIDEO_QA_POST_ID=postId
      window.__VIDEO_QA_JWT=jwt
    }, {postId,jwt})
    await page.goto(origin+'/tests/video/browser-post-video.html')
    const video = page.locator('[data-testid="timeline-post"] video')
    await video.waitFor({timeout:20000})
    try {
      await page.waitForFunction(() => {
        const el=document.querySelector('video')
        return el && el.readyState>=2 && el.videoWidth>0 && el.duration>0
      },null,{timeout:20000})
    } catch (error) {
      const diagnostic = await video.evaluate(el => ({readyState:el.readyState, networkState:el.networkState,
        mediaError:el.error?.code, canPlayWebm:el.canPlayType('video/webm; codecs="vp8"'),
        currentSrc:el.currentSrc.slice(0,80)})).catch(e=>({evaluationError:String(e)}))
      throw new Error('Chromium media readiness failed: '+JSON.stringify({diagnostic,errors}),{cause:error})
    }
    await video.evaluate(el=>el.play())
    await page.waitForFunction(() => document.querySelector('video')?.currentTime>0,
      null,{timeout:15000})
    await page.close()
    const denied = await browser.newPage()
    await denied.addInitScript(({postId,jwt}) => {
      window.__VIDEO_QA_POST_ID=postId
      window.__VIDEO_QA_JWT=jwt
    }, {postId,jwt:deniedJwt})
    await denied.goto(origin+'/tests/video/browser-post-video.html')
    await denied.getByRole('status').filter({hasText:'動画を読み込めません'}).waitFor({timeout:20000})
    assert.equal(await denied.locator('video').count(),0)
    await denied.close()
    console.log('PASS: REAL Chromium actual React PostVideo timeline card -> authenticated server API -> playable video; unauthorized user denied')
  } finally {
    if (browser) await browser.close()
    await new Promise(resolve=>server.close(resolve))
    await vite.close()
  }
}
