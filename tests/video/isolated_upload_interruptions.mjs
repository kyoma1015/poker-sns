import assert from 'node:assert/strict'

export async function verifyUploadInterruptions({browser,origin,jwt,anon,bytes}) {
  for(const scenario of ['lost-upload-response','upload-deadline','unmount-reservation','unmount-upload','expire-after-reservation','lost-reservation-response']) {
    const page=await browser.newPage()
    const errors=[], reservations=[],uploads=[],finalizations=[]
    let release,routeDone,committed=false,failedUploads=0
    page.on('pageerror',error=>errors.push(String(error)))
    page.on('requestfailed',request=>{if(request.url().includes('/storage/v1/object/post-videos/')) failedUploads++})
    try {
      await page.addInitScript(({jwt,anon})=>{window.__VIDEO_QA_JWT=jwt;window.__VIDEO_QA_ANON=anon},{jwt,anon})
      if(scenario==='upload-deadline') await page.clock.install()
      await page.goto(origin+'/tests/video/browser-real-timeline.html')
      await page.locator('article video').first().waitFor({timeout:20000})
      await page.evaluate(()=>window.dispatchEvent(new Event('poker-id-open-compose')))
      const composer=page.getByRole('dialog',{name:'新しい投稿'})
      await composer.waitFor()
      const content='isolated '+scenario+' '+Date.now()
      await composer.locator('textarea').fill(content)
      await page.locator('input[accept="video/mp4,video/webm"]').setInputFiles({name:'interrupt.webm',mimeType:'video/webm',buffer:bytes})
      await composer.locator('video').waitFor()
      if(scenario==='expire-after-reservation') await page.evaluate(()=>{
        const id=JSON.parse(atob(window.__VIDEO_QA_JWT.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
        window.__VIDEO_QA_GET_USER=()=>window.__UPLOAD_AUTH_EXPIRED
          ? {data:{user:null},error:{message:'PRIVATE-EXPIRED-ERROR'}} : {data:{user:{id}},error:null}
      })
      await page.route('**/internal/video/finalize',async route=>{
        const body=route.request().postDataJSON()
        if(body.action!=='reserve') {finalizations.push(body.object_path);return route.continue()}
        reservations.push(body.object_path)
        if(scenario==='lost-reservation-response' && reservations.length===1) {
          const response=await route.fetch()
          assert.equal(response.status(),201,'reservation commits before its response is lost')
          committed=true
          return route.fulfill({status:503,contentType:'application/json',body:'{"error":"PRIVATE-RESERVATION-ERROR"}'})
        }
        if(scenario==='expire-after-reservation') {
          const response=await route.fetch()
          assert.equal(response.status(),201)
          await page.evaluate(()=>{window.__UPLOAD_AUTH_EXPIRED=true})
          return route.fulfill({response})
        }
        if(scenario==='unmount-reservation') {
          const response=await route.fetch()
          assert.equal(response.status(),201)
          committed=true
          await new Promise(resolve=>{release=resolve})
          try {await route.fulfill({response})} catch { /* page aborted this exact request */ }
          routeDone?.()
          return
        }
        return route.continue()
      })
      await page.route('**/storage/v1/object/post-videos/**',async route=>{
        if(route.request().method()!=='POST') return route.continue()
        uploads.push(new URL(route.request().url()).pathname)
        if(scenario==='lost-upload-response' && uploads.length===1) {
          const response=await route.fetch()
          assert.ok(response.ok(),'actual Storage upload must commit before response loss')
          committed=true
          return route.fulfill({status:503,contentType:'application/json',body:'{"message":"PRIVATE-LOST-UPLOAD-ERROR"}'})
        }
        if((scenario==='upload-deadline' || scenario==='unmount-upload') && uploads.length===1) {
          await new Promise(resolve=>{release=resolve})
          try {await route.abort()} catch { /* already aborted by the real fetch signal */ }
          routeDone?.()
          return
        }
        return route.continue()
      })
      await composer.getByRole('button',{name:'投稿する',exact:true}).click()
      if(scenario==='unmount-reservation' || scenario==='unmount-upload' || scenario==='upload-deadline') {
        // Wait for the precise transport boundary, not arbitrary wall-clock delay.
        for(let wait=0;!release && wait<1000;wait++) await page.waitForTimeout(20)
        assert.ok(release,'upload must reach controlled transport boundary')
        const done=new Promise(resolve=>{routeDone=resolve})
        if(scenario==='upload-deadline') {
          await page.clock.fastForward(90001)
          await composer.getByText(/動画の送信を確認できませんでした/).waitFor()
          await page.waitForFunction(()=>[...document.querySelectorAll('[role="dialog"] button')].some(b=>b.textContent==='投稿する'&&!b.disabled))
        } else {
          const aborted=page.waitForEvent('requestfailed',{predicate:request=>request.url().includes(scenario==='unmount-upload'?'/storage/v1/object/post-videos/':'/internal/video/finalize')})
          await page.evaluate(()=>window.__VIDEO_QA_UNMOUNT())
          await aborted
        }
        release();await done
        if(scenario.startsWith('unmount')) {
          assert.equal(finalizations.length,0,'abandoned work must never finalize')
          if(scenario==='unmount-reservation') {
            assert.ok(committed,'reservation really committed before unmount')
            assert.equal(uploads.length,0,'aborted reservation response cannot start upload')
          } else {
            // Observe the actual fetch abort, not only a detached component.
            await page.waitForFunction(()=>document.getElementById('root').childElementCount===0)
            assert.ok(failedUploads>0,'unmount aborts underlying Storage request')
          }
          assert.deepEqual(errors,[])
          console.log('PASS: actual Timeline upload boundary '+scenario)
          continue
        }
      } else {
        await composer.getByText(/動画を投稿できませんでした/).waitFor()
        await page.waitForFunction(()=>[...document.querySelectorAll('[role="dialog"] button')].some(b=>b.textContent==='投稿する'&&!b.disabled))
      }
      assert.equal(finalizations.length,0,'no finalize before upload confirmation/reconciliation')
      if(scenario==='lost-upload-response') assert.ok(committed)
      if(scenario==='lost-reservation-response') {
        assert.ok(committed)
        assert.equal(uploads.length,0,'ambiguous reservation never sends Storage bytes')
      }
      if(scenario==='expire-after-reservation') {
        assert.equal(uploads.length,0,'expired identity sends zero Storage bytes')
        await page.evaluate(()=>{delete window.__VIDEO_QA_GET_USER})
      }
      assert.equal(await page.getByText(/PRIVATE-.*-ERROR/).count(),0,'provider error stays private')
      await composer.getByRole('button',{name:'投稿する',exact:true}).click()
      await page.locator('article').filter({hasText:content}).waitFor({timeout:30000})
      if(scenario==='lost-reservation-response') {
        assert.equal(reservations.length,2,'an ambiguous reservation key must not be reused')
        assert.notEqual(reservations[0],reservations[1])
        assert.equal(finalizations[0],reservations[1])
      } else assert.equal(reservations.length,1,'retry must never consume another confirmed reservation')
      assert.equal(finalizations.length,1,'retry finalizes once')
      assert.equal(new Set(uploads).size,1,'same immutable upload path across retries')
      assert.equal(uploads.length,['expire-after-reservation','lost-reservation-response'].includes(scenario)?1:2)
      assert.equal(await page.locator('article').filter({hasText:content}).count(),1)
      assert.equal(await page.evaluate(()=>sessionStorage.getItem('poker-id-pending-video-v1')),null)
      assert.deepEqual(errors,[])
      console.log('PASS: actual Timeline upload boundary '+scenario)
    } finally {
      release?.()
      await page.close()
    }
  }
}
