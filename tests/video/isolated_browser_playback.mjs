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
      transform(_source, id) {
        if (!id.split('?')[0].endsWith('/src/videoApi.ts')) return null
        return `
          export const VIDEO_SERVER_ENABLED = true
          export async function loadAuthorizedVideo(postId) {
            const response = await fetch('/internal/video/media/' + encodeURIComponent(postId), {
              headers: { Authorization: 'Bearer ' + window.__VIDEO_QA_JWT },
              cache: 'no-store',
            })
            if (!response.ok) throw new Error('unauthorized')
            const blob = await response.blob()
            if (!blob.size || blob.size > 20 * 1024 * 1024 ||
                !['video/mp4','video/webm'].includes(blob.type)) throw new Error('invalid media')
            return URL.createObjectURL(blob)
          }
        `
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
    browser = await chromium.launch({ executablePath: '/usr/bin/chromium',
      headless: true, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] })
    const origin = 'http://127.0.0.1:' + address.port
    const page = await browser.newPage()
    await page.addInitScript(({postId,jwt}) => {
      window.__VIDEO_QA_POST_ID=postId
      window.__VIDEO_QA_JWT=jwt
    }, {postId,jwt})
    await page.goto(origin+'/tests/video/browser-post-video.html')
    const video = page.locator('[data-testid="timeline-post"] video')
    await video.waitFor({timeout:20000})
    await page.waitForFunction(() => {
      const el=document.querySelector('video')
      return el && el.readyState>=2 && el.videoWidth>0 && el.duration>0
    },null,{timeout:20000})
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
