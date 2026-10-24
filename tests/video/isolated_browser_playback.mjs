// Actual React PostVideo in headless Chromium, backed by isolated Supabase
// through the real authorized media API. Never used in production builds.
import assert from 'node:assert/strict'
import { createServer as createHttpServer } from 'node:http'
import { createServer as createViteServer } from 'vite'
import { chromium } from 'playwright-core'
import { createVideoMediaHandler } from '../../api/video-media.ts'
import { createVideoFinalizeHandler } from '../../api/video-finalize.ts'
import { createIsolatedSupabaseVideoAdapters } from '../../api/video-isolated-supabase-adapters.ts'

export async function verifyRealBrowserPlayback({ postId, jwt, deniedJwt, anon, service, bytes }) {
  assert.ok(service && bytes?.length,'isolated full upload test credentials and media required')
  assert.ok(anon,'isolated anon key required')
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
          return `import { createClient } from '@supabase/supabase-js'
          const jwt = window.__VIDEO_QA_JWT
          const client = createClient('http://127.0.0.1:56321', window.__VIDEO_QA_ANON, {
            global: { headers: { Authorization: 'Bearer ' + jwt } },
            auth: { persistSession:false, autoRefreshToken:false },
          })
          // Isolated-only stubs for unrelated social tables absent from local QA schema.
          const empty = { data:[], error:null }
          const query = new Proxy({}, { get(_target, key) {
            if (key === 'then') return (resolve, reject) => Promise.resolve(empty).then(resolve, reject)
            return () => query
          } })
          export const supabase = {
            auth: {
              getSession: async () => ({ data:{session:{access_token:jwt}}, error:null }),
              getUser: async () => client.auth.getUser(jwt),
            },
            from: table => table === 'posts' ? client.from('posts') : query,
            rpc: async () => empty,
            storage: client.storage,
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
  const finalize = createVideoFinalizeHandler(createIsolatedSupabaseVideoAdapters('http://127.0.0.1:56321',anon,service,jwt),{isolatedLocalOnly:true})
  const server = createHttpServer((req, res) => {
    if (req.url === '/internal/video/finalize') {
      void (async () => {
        const chunks=[]
        for await (const chunk of req) {
          chunks.push(chunk)
          if (Buffer.concat(chunks).length > 12288) {res.writeHead(413);res.end();return}
        }
        const raw=Buffer.concat(chunks)
        let body
        try {body=JSON.parse(raw.toString('utf8'))} catch {res.writeHead(400);res.end();return}
        const response={
          setHeader:(name,value)=>{res.setHeader(name,value);return response},
          status:code=>{res.statusCode=code;return response},
          json:value=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(value));return response},
          end:()=>{res.end();return response},
        }
        await finalize({method:req.method,headers:{...req.headers,'content-length':String(raw.length)},body},response)
      })().catch(()=>{if(!res.headersSent)res.statusCode=503;if(!res.writableEnded)res.end()})
      return
    }
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
    await page.addInitScript(({postId,jwt,anon}) => {
      window.__VIDEO_QA_POST_ID=postId
      window.__VIDEO_QA_JWT=jwt
      window.__VIDEO_QA_ANON=anon
    }, {postId,jwt,anon})
    await page.goto(origin+'/tests/video/browser-post-video.html')
    const video = page.locator('[data-testid="timeline-post"][data-post-id="'+postId+'"] video')
    try { await video.waitFor({timeout:20000}) } catch(error) {
      throw new Error('Browser feed did not render owner video: '+JSON.stringify({html:(await page.locator('main').allTextContents()).slice(0,3),errors}),{cause:error})
    }
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
    // Mount the ACTUAL Timeline.tsx and read the real local PostgREST posts.
    // Only unrelated social tables and RPCs are stubbed (no local QA schema).
    const timelinePage=await browser.newPage()
    await timelinePage.addInitScript(({jwt,anon}) => {
      window.__VIDEO_QA_JWT=jwt
      window.__VIDEO_QA_ANON=anon
    },{jwt,anon})
    await timelinePage.goto(origin+'/tests/video/browser-real-timeline.html')
    const timelineErrors=[]
    timelinePage.on('pageerror',error=>timelineErrors.push(String(error)))
    timelinePage.on('console',message=>{if(message.type()==='error')timelineErrors.push(message.text())})
    try {
      await timelinePage.getByRole('button',{name:'おすすめ'}).click({timeout:20000})
      await timelinePage.getByText('real isolated end-to-end',{exact:true}).waitFor({timeout:20000})
    } catch(error) {
      throw new Error('Actual Timeline mount/feed failed: '+JSON.stringify({
        body:(await timelinePage.locator('body').allTextContents()).slice(0,2).map(t=>t.slice(0,900)),
        errors:timelineErrors
      }),{cause:error})
    }
    const actualVideo=timelinePage.locator('article video').first()
    await actualVideo.waitFor({timeout:20000})
    await timelinePage.waitForFunction(() => {
      const el=document.querySelector('article video')
      return el && el.readyState>=2 && el.videoWidth>0
    },null,{timeout:20000})
    await actualVideo.evaluate(el=>el.play())
    await timelinePage.waitForFunction(() => document.querySelector('article video')?.currentTime>0,
      null,{timeout:15000})
    // Full real Timeline UI flow: file picker -> local Storage -> HTTP finalize
    // -> RLS PostgREST feed refresh -> real PostVideo Chromium playback.
    const uploadText='isolated timeline browser upload '+Date.now()
    await timelinePage.evaluate(() => window.dispatchEvent(new Event('poker-id-open-compose')))
    const composer=timelinePage.getByRole('dialog',{name:'新しい投稿'})
    await composer.waitFor({timeout:15000})
    await composer.getByPlaceholder('ポーカーについて何を投稿する？').fill(uploadText)
    await timelinePage.locator('input[accept="video/mp4,video/webm"]').setInputFiles({
      name:'timeline-e2e.webm',mimeType:'video/webm',buffer:bytes,
    })
    await composer.getByRole('button',{name:'投稿する'}).click({timeout:20000})
    try {
      await timelinePage.locator('article').filter({hasText:uploadText}).waitFor({timeout:45000})
    } catch(error) {
      throw new Error('Full Timeline upload/finalize/feed failed: '+JSON.stringify({
        body:(await timelinePage.locator('body').allTextContents()).slice(0,2).map(t=>t.slice(0,1200)),
        errors:timelineErrors
      }),{cause:error})
    }
    const uploadedArticle=timelinePage.locator('article').filter({hasText:uploadText})
    const uploadedVideo=uploadedArticle.locator('video')
    await uploadedVideo.waitFor({timeout:20000})
    await timelinePage.waitForFunction(text => {
      const article=[...document.querySelectorAll('article')].find(a=>a.textContent?.includes(text))
      const el=article?.querySelector('video')
      return el && el.readyState>=2 && el.videoWidth>0
    },uploadText,{timeout:20000})
    await uploadedVideo.evaluate(el=>el.play())
    await timelinePage.waitForFunction(text => {
      const article=[...document.querySelectorAll('article')].find(a=>a.textContent?.includes(text))
      return article?.querySelector('video')?.currentTime>0
    },uploadText,{timeout:15000})
    console.log('PASS: FULL ACTUAL Timeline.tsx UI video file selection -> real isolated Storage HTTP upload -> real finalize HTTP -> RLS PostgREST feed -> Chromium playback')
    console.log('PASS: ACTUAL Timeline.tsx renders real RLS PostgREST video and Chromium plays it (social dependencies isolated)')
    await timelinePage.close()
    const denied = await browser.newPage()
    await denied.addInitScript(({postId,jwt,anon}) => {
      window.__VIDEO_QA_POST_ID=postId
      window.__VIDEO_QA_JWT=jwt
      window.__VIDEO_QA_ANON=anon
    }, {postId,jwt:deniedJwt,anon})
    await denied.goto(origin+'/tests/video/browser-post-video.html')
    await denied.locator('main[data-feed-loaded="true"]').waitFor({timeout:20000})
    assert.equal(await denied.getByRole('alert').count(),0,'denied feed must complete without query error')
    assert.equal(await denied.locator('[data-testid="timeline-post"][data-post-id="'+postId+'"]').count(),0,'RLS must hide owner post from other user')
    await denied.close()
    console.log('PASS: REAL Chromium actual React PostVideo timeline card -> authenticated server API -> playable video; unauthorized user denied')
  } finally {
    if (browser) await browser.close()
    await new Promise(resolve=>server.close(resolve))
    await vite.close()
  }
}
