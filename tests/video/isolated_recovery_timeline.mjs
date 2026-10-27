import assert from 'node:assert/strict'
import {createHash} from 'node:crypto'

export async function verifyRecoveryTimeline({browser,origin,jwt,anon,bytes,legacyPath,expire}) {
  for(const scenario of ['uploaded-reload','published-response-loss','tampered-hash','expired','legacy','foreign-path']) {
    const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true})
    const errors=[],calls=[]
    let uploads=0,release,path,committed=false
    page.on('pageerror',e=>errors.push(String(e)))
    try {
      await page.addInitScript(({jwt,anon,scenario,legacyPath,sha,size})=>{
        window.__VIDEO_QA_JWT=jwt;window.__VIDEO_QA_ANON=anon
        if(scenario==='legacy'||scenario==='foreign-path') {
          const owner=JSON.parse(atob(jwt.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
          const path=scenario==='legacy'?legacyPath:'ffffffff-ffff-4fff-8fff-ffffffffffff/eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee.webm'
          sessionStorage.setItem('poker-id-video-transfer-v1:'+owner,JSON.stringify({owner,path,sha256:sha,size,type:'video/webm',phase:'acknowledged',startedAt:Date.now()}))
        }
      },{jwt,anon,scenario,legacyPath,sha:createHash('sha256').update(bytes).digest('hex'),size:bytes.length})
      await page.route('**/internal/video/finalize',async route=>{
        const body=route.request().postDataJSON();calls.push(body)
        if(body.action==='reserve')path=body.object_path
        if(scenario==='published-response-loss'&&body.action==='recovery_finalize'&&calls.filter(c=>c.action==='recovery_finalize').length===1) {
          const response=await route.fetch();assert.equal(response.status(),200);committed=true
          await new Promise(resolve=>{release=resolve})
          try{await route.fulfill({response})}catch{/* navigation lost original response */}
          return
        }
        return route.continue()
      })
      await page.route('**/storage/v1/object/post-videos/**',async route=>{
        if(route.request().method()!=='POST')return route.continue()
        uploads++
        if(scenario==='published-response-loss')return route.continue()
        const response=await route.fetch();assert.ok(response.ok());committed=true
        await new Promise(resolve=>{release=resolve})
        try{await route.fulfill({response})}catch{/* navigation lost upload acknowledgment */}
      })
      await page.goto(origin+'/tests/video/browser-real-timeline.html')
      const composer=page.getByRole('dialog',{name:'新しい投稿'})
      const text='isolated Timeline recovery '+scenario+' '+Date.now()
      if(!['legacy','foreign-path'].includes(scenario)) {
        await page.locator('article video').first().waitFor({timeout:20000})
        await page.evaluate(()=>window.dispatchEvent(new Event('poker-id-open-compose')))
        await composer.waitFor()
        await composer.locator('textarea').fill(text)
        await page.locator('input[accept="video/mp4,video/webm"]').setInputFiles({name:'recovery-ui.webm',mimeType:'video/webm',buffer:bytes})
        await composer.locator('video').waitFor()
        await composer.getByRole('button',{name:'投稿する',exact:true}).click()
        for(let wait=0;!release&&wait<1000;wait++)await page.waitForTimeout(20)
        assert.ok(release);assert.ok(committed,'real commit before reload')
        assert.equal(calls.filter(c=>c.action==='bind_recovery').length,1,'actual Timeline binds before first upload')
        if(scenario==='tampered-hash') await page.evaluate(()=>{
          const owner=JSON.parse(atob(window.__VIDEO_QA_JWT.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
          const key='poker-id-video-transfer-v1:'+owner,r=JSON.parse(sessionStorage.getItem(key));r.sha256='0'.repeat(64);sessionStorage.setItem(key,JSON.stringify(r))
        })
        if(scenario==='expired')expire(path)
        await page.reload()
        release();release=undefined
      }
      if(scenario==='uploaded-reload'||scenario==='published-response-loss') {
        const article=page.locator('article').filter({hasText:text})
        await article.waitFor({timeout:45000})
        await page.waitForFunction(()=>{
          const owner=JSON.parse(atob(window.__VIDEO_QA_JWT.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
          return sessionStorage.getItem('poker-id-video-transfer-v1:'+owner)===null&&sessionStorage.getItem('poker-id-pending-video-v1')===null
        },null,{timeout:45000})
        assert.equal(await article.count(),1,'recovery shows exactly one post')
        await article.locator('video').waitFor()
        await article.locator('video').evaluate(video=>video.play())
        await page.waitForFunction(text=>[...document.querySelectorAll('article')].find(a=>a.textContent.includes(text))?.querySelector('video')?.currentTime>0,text)
        assert.equal(calls.filter(c=>c.action==='reserve').length,1)
        assert.equal(calls.filter(c=>c.action==='bind_recovery').length,1)
        assert.equal(uploads,1,'reload cannot upload a second object')
        assert.ok(calls.filter(c=>c.action==='recovery_status').length>=1)
        const finalized=calls.filter(c=>c.action==='recovery_finalize')
        assert.equal(finalized.length,scenario==='published-response-loss'?2:1)
        assert.ok(finalized.every(c=>c.object_path===path&&c.content===text),'only server-bound immutable draft may recover')
        assert.equal(await page.evaluate(()=>{
          const owner=JSON.parse(atob(window.__VIDEO_QA_JWT.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
          return sessionStorage.getItem('poker-id-video-transfer-v1:'+owner)||sessionStorage.getItem('poker-id-pending-video-v1')
        }),null,'confirmed recovery clears only its local pointers')
      } else {
        await composer.getByText(/重複を防ぐため動画の再送信を停止/).first().waitFor()
        // Observe completed reconciliation, not the temporary loading notice.
        await page.waitForFunction(()=>![...document.querySelectorAll('[role="dialog"] button')].some(b=>b.textContent==='投稿中...'))
        assert.equal(calls.filter(c=>c.action==='recovery_finalize').length,0,'unverified/tampered/expired/legacy/foreign cannot finalize')
        assert.equal(calls.filter(c=>c.action==='reserve').length,['legacy','foreign-path'].includes(scenario)?0:1)
        assert.equal(uploads,['legacy','foreign-path'].includes(scenario)?0:1)
      }
      assert.deepEqual(errors,[])
      console.log('PASS: actual Timeline manifest recovery '+scenario)
    } finally {release?.();await page.close()}
  }
}
