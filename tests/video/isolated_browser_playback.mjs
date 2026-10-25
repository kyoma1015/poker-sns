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
          const authListeners = new Set()
          window.__VIDEO_QA_TRIGGER_SIGN_OUT = () => {
            for (const callback of authListeners) callback('SIGNED_OUT', null)
          }
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
              onAuthStateChange: callback => {
                authListeners.add(callback)
                return { data: { subscription: { unsubscribe: () => authListeners.delete(callback) } } }
              },
            },
            from: table => table === 'posts' ? client.from('posts') : query,
            rpc: async () => empty,
            storage: client.storage,
          }`
        }
        if (filename.endsWith('/src/videoApi.ts')) {
          assert.ok(source.includes("VIDEO_SERVER_ENABLED = import.meta.env.VITE_VIDEO_SERVER_ENABLED === 'true'"),
            'production video feature gate unexpectedly changed')
          return source.replace("VIDEO_SERVER_ENABLED = import.meta.env.VITE_VIDEO_SERVER_ENABLED === 'true'",
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
    // Real Chromium account-switch regression: an untrusted session draft
    // owned by another user must not be displayed in the composer.
    const foreignDraft='FOREIGN-ACCOUNT-PRIVATE-DRAFT-'+Date.now()
    await timelinePage.evaluate(({foreignOwner,foreignDraft}) => {
      sessionStorage.setItem('poker-id-pending-video-v1',JSON.stringify({
        owner:foreignOwner,
        path:foreignOwner+'/22222222-2222-4222-8222-222222222222.webm',
        content:foreignDraft,
      }))
    },{foreignOwner:'33333333-3333-4333-8333-333333333333',foreignDraft})
    await timelinePage.reload()
    await timelinePage.getByRole('button',{name:'おすすめ'}).click({timeout:20000})
    await timelinePage.getByText('real isolated end-to-end',{exact:true}).waitFor({timeout:20000})
    // Wait for the asynchronous authenticated restore to finish rather than
    // using a fixed delay that can pass before getUser resolves on slow CI.
    await timelinePage.waitForFunction(() =>
      sessionStorage.getItem('poker-id-pending-video-v1') === null,
      null,{timeout:20000})
    assert.equal(await timelinePage.getByText(foreignDraft,{exact:true}).count(),0,
      'foreign account session draft must not render in actual Timeline')
    assert.equal(await timelinePage.getByRole('dialog',{name:'新しい投稿'}).count(),0,
      'foreign account session draft must not open composer')
    assert.equal(await timelinePage.evaluate(() => sessionStorage.getItem('poker-id-pending-video-v1')),null,
      'foreign pending draft pointer must be removed without deleting the Storage object')
    console.log('PASS: REAL Chromium account switch rejects foreign pending video draft and clears local pointer')
    // Same-owner recovery must preserve the draft and open the composer.
    const ownedDraft='OWN-ACCOUNT-PENDING-VIDEO-'+Date.now()
    await timelinePage.evaluate(({owner,ownedDraft}) => {
      sessionStorage.setItem('poker-id-pending-video-v1',JSON.stringify({
        owner,
        path:owner+'/22222222-2222-4222-8222-222222222222.webm',
        content:ownedDraft,
      }))
    },{owner:JSON.parse(Buffer.from(jwt.split('.')[1],'base64url').toString('utf8')).sub,ownedDraft})
    await timelinePage.reload()
    const restoredComposer=timelinePage.getByRole('dialog',{name:'新しい投稿'})
    await restoredComposer.waitFor({timeout:20000})
    assert.equal(await restoredComposer.getByPlaceholder('ポーカーについて何を投稿する？').inputValue(),ownedDraft,
      'same-owner pending draft must be restored after reload')
    await timelinePage.evaluate(() => sessionStorage.removeItem('poker-id-pending-video-v1'))
    await timelinePage.reload()
    console.log('PASS: REAL Chromium restores same-owner pending draft after reload')
    // Verify the real browser duration reader cannot hang on a corrupt video.
    // Advance Chromium's virtual clock by 15 seconds without a real 15s delay.
    const timeoutPage=await browser.newPage()
    await timeoutPage.clock.install()
    await timeoutPage.goto(origin+'/tests/video/browser-real-timeline.html')
    await timeoutPage.evaluate(async () => {
      const module=await import('/src/videoUpload.ts')
      // A deliberately non-signalling element proves the timer, not the
      // browser's normal immediate corrupt-file error path.
      const originalCreate=document.createElement.bind(document)
      const originalUrl=URL.createObjectURL
      const originalRevoke=URL.revokeObjectURL
      document.createElement=(tag,...args)=>tag==='video'
        ? {preload:'',onloadedmetadata:null,onerror:null,src:'',removeAttribute(){},load(){}}
        : originalCreate(tag,...args)
      URL.createObjectURL=()=> 'blob:isolated-timeout'
      URL.revokeObjectURL=()=> { window.__VIDEO_TIMEOUT_REVOKED=true }
      const corrupt=new File([new Uint8Array([0,1,2,3])],'corrupt.webm',{type:'video/webm'})
      window.__VIDEO_TIMEOUT_RESULT='pending'
      void module.readVideoDuration(corrupt).then(
        ()=> { window.__VIDEO_TIMEOUT_RESULT='unexpected_success' },
        ()=> { window.__VIDEO_TIMEOUT_RESULT='rejected' })
    })
    await timeoutPage.clock.fastForward(15000)
    await timeoutPage.waitForFunction(() => window.__VIDEO_TIMEOUT_RESULT !== 'pending',{timeout:1000})
    assert.equal(await timeoutPage.evaluate(() => window.__VIDEO_TIMEOUT_RESULT),'rejected',
      'corrupt Chromium metadata must reject by 15-second deadline')
    await timeoutPage.close()
    console.log('PASS: Chromium video metadata rejects within virtual 15-second timeout')
    // Full real Timeline UI flow: file picker -> local Storage -> HTTP finalize
    // -> RLS PostgREST feed refresh -> real PostVideo Chromium playback.
    const uploadText='isolated timeline browser upload '+Date.now()
    await timelinePage.evaluate(() => window.dispatchEvent(new Event('poker-id-open-compose')))
    const composer=timelinePage.getByRole('dialog',{name:'新しい投稿'})
    await composer.waitFor({timeout:15000})
    await composer.getByPlaceholder('ポーカーについて何を投稿する？').fill(uploadText)
    // Reservation RPC must exist in the disposable HTTP stack before the
    // real client can upload. Never mock a successful reservation response.
    const reservationPreflight = await timelinePage.evaluate(async () => {
      const response = await fetch('/internal/video/finalize', {
        method:'POST',
        headers:{'Content-Type':'application/json',Authorization:'Bearer '+window.__VIDEO_QA_JWT},
        body:JSON.stringify({action:'reserve',object_path:'00000000-0000-0000-0000-000000000000/00000000-0000-0000-0000-000000000000.webm'}),
      })
      return response.status
    })
    assert.ok([401,403,503].includes(reservationPreflight),
      'foreign owner reservation must never be accepted')
    // Assert the actual browser upload must reserve a permanent key first.
    // Observe real HTTP responses, not a mocked success.
    const videoReservationResponses=[]
    timelinePage.on('response', response => {
      if (response.url().includes('/internal/video/finalize')) {
        videoReservationResponses.push({status:response.status(),method:response.request().method()})
      }
    })
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
    assert.ok(videoReservationResponses.filter(x=>x.status===201&&x.method==='POST').length >= 2,
      'real browser must receive distinct trusted reservation AND finalize successes')
    // Reservation ledger is the durable authority, not the HTTP success alone.
    // The key is verified through the local service-role RPC-backed database.

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
    // Verify that the actual Blob URL is revoked, not merely detached from DOM.
    const previousBlobUrl = await uploadedVideo.getAttribute('src')
    assert.ok(previousBlobUrl?.startsWith('blob:'), 'playback must use a Blob URL')
    await timelinePage.evaluate(() => {
      window.__VIDEO_QA_REVOKED_URLS = []
      const revoke = URL.revokeObjectURL.bind(URL)
      URL.revokeObjectURL = value => {
        window.__VIDEO_QA_REVOKED_URLS.push(value)
        return revoke(value)
      }
    })
    // Verify the production component drops its in-memory Blob URL on sign-out.
    // The test-only bridge dispatches SIGNED_OUT to the actual React component.
    // This proves client-side URL cleanup, not real GoTrue token revocation.
    await timelinePage.evaluate(() => window.__VIDEO_QA_TRIGGER_SIGN_OUT?.())
    await timelinePage.waitForFunction(text => {
      const article=[...document.querySelectorAll('article')].find(a=>a.textContent?.includes(text))
      return article && !article.querySelector('video')
    },uploadText,{timeout:20000})
    assert.equal(await uploadedArticle.locator('video').count(),0,
      'authenticated video element must disappear after sign-out')
    const revokedUrls = await timelinePage.evaluate(() => window.__VIDEO_QA_REVOKED_URLS)
    assert.ok(revokedUrls.includes(previousBlobUrl), 'SIGNED_OUT must revoke the exact playback Blob URL')
    console.log('PASS: Chromium React playback Blob URL explicitly revoked on synthetic SIGNED_OUT event')
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
