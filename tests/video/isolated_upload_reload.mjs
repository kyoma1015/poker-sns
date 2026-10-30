import assert from 'node:assert/strict'

export async function verifyUploadReload({browser,origin,jwt,anon,bytes}) {
  for(const scenario of ['reload-reservation','reload-storage-commit','tampered-ack','journal-write-denied','foreign-journal']) {
    const page=await browser.newPage()
    const errors=[]
    let reservations=0,uploads=0,finalizations=0,release,committed=false
    page.on('pageerror',e=>errors.push(String(e)))
    try {
      await page.addInitScript(({jwt,anon,scenario})=>{
        window.__VIDEO_QA_JWT=jwt;window.__VIDEO_QA_ANON=anon
        const id=JSON.parse(atob(jwt.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
        if(scenario==='foreign-journal') {
          const owner='ffffffff-ffff-4fff-8fff-ffffffffffff'
          sessionStorage.setItem('poker-id-video-transfer-v1:'+owner,JSON.stringify({owner,path:owner+'/eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee.webm',phase:'acknowledged',content:'PRIVATE-FOREIGN-DRAFT'}))
        }
        if(scenario==='tampered-ack') {
          const path=id+'/eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee.webm'
          sessionStorage.setItem('poker-id-video-transfer-v1:'+id,JSON.stringify({owner:id,path,phase:'acknowledged',sha256:'a'.repeat(64),size:1,type:'video/webm',startedAt:Date.now()+999999999}))
          // A forged pending pointer must not bypass the unconfirmed journal.
          sessionStorage.setItem('poker-id-pending-video-v1',JSON.stringify({owner:id,path,content:'PRIVATE-FORGED-DRAFT'}))
        }
        if(scenario==='journal-write-denied') {
          const set=Storage.prototype.setItem
          Storage.prototype.setItem=function(key,value){if(key.startsWith('poker-id-video-transfer-v1:'))throw Error('PRIVATE-STORAGE-ERROR');return set.call(this,key,value)}
        }
      },{jwt,anon,scenario})
      await page.route('**/internal/video/finalize',async route=>{
        if(route.request().postDataJSON().action!=='reserve') {finalizations++;return route.continue()}
        reservations++
        if(scenario==='reload-reservation') {
          const response=await route.fetch();assert.equal(response.status(),201);committed=true
          await new Promise(resolve=>{release=resolve})
          try {await route.fulfill({response})} catch { /* navigation aborted original request */ }
          return
        }
        return route.continue()
      })
      await page.route('**/storage/v1/object/post-videos/**',async route=>{
        if(route.request().method()!=='POST') return route.continue()
        uploads++
        if(scenario==='reload-storage-commit') {
          const response=await route.fetch();assert.ok(response.ok());committed=true
          await new Promise(resolve=>{release=resolve})
          try {await route.fulfill({response})} catch { /* navigation aborted original request */ }
          return
        }
        return route.continue()
      })
      await page.goto(origin+'/tests/video/browser-real-timeline.html')
      if(scenario!=='tampered-ack') {
        await page.locator('article video').first().waitFor({timeout:20000})
        await page.evaluate(()=>window.dispatchEvent(new Event('poker-id-open-compose')))
        const composer=page.getByRole('dialog',{name:'新しい投稿'})
        await composer.waitFor()
        await composer.locator('textarea').fill('isolated reload must not publish')
        await page.locator('input[type="file"][accept*="video/mp4"]').setInputFiles({name:'reload.webm',mimeType:'video/webm',buffer:bytes})
        await composer.locator('video').waitFor()
        if(scenario==='foreign-journal') {
          assert.equal(await composer.getByText(/重複を防ぐため動画の再送信を停止/).count(),0,'another owner journal cannot block current account')
          assert.equal(await page.getByText('PRIVATE-FOREIGN-DRAFT',{exact:false}).count(),0,'never show foreign recovery content')
          assert.equal(await page.evaluate(()=>sessionStorage.getItem('poker-id-video-transfer-v1:ffffffff-ffff-4fff-8fff-ffffffffffff')!==null),true,'never clear another owner journal')
          assert.deepEqual({reservations,uploads,finalizations},{reservations:0,uploads:0,finalizations:0})
          assert.deepEqual(errors,[])
          console.log('PASS: actual Timeline upload reload '+scenario)
          continue
        }
        await composer.getByRole('button',{name:'投稿する',exact:true}).click()
        if(scenario!=='journal-write-denied') {
          for(let wait=0;!release&&wait<1000;wait++) await page.waitForTimeout(20)
          assert.ok(release);assert.ok(committed,'real side effect precedes navigation')
          await page.reload()
          release();release=undefined
        }
      }
      const composer=page.getByRole('dialog',{name:'新しい投稿'})
      await composer.getByText(/重複を防ぐため動画の再送信を停止/).first().waitFor()
      const before={reservations,uploads,finalizations}
      // Exercise the production helper as well as the UI; stored phase/hash is
      // never converted into permission for a new request or finalize.
      const refused=await page.evaluate(async bytes=>{
        const id=JSON.parse(atob(window.__VIDEO_QA_JWT.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
        const {uploadPostVideo}=await import('/src/videoUpload.ts')
        try {await uploadPostVideo(id,new File([new Uint8Array(bytes)],'retry.webm',{type:'video/webm'}));return false}
        catch {return true}
      },[...bytes])
      assert.equal(refused,true)
      await page.locator('input[type="file"][accept*="video/mp4"]').setInputFiles({name:'retry.webm',mimeType:'video/webm',buffer:bytes})
      await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))
      assert.deepEqual({reservations,uploads,finalizations},before,'reloaded/untrusted state causes zero additional writes')
      assert.equal(finalizations,0,'never finalize an unconfirmed object')
      if(scenario==='reload-reservation') {assert.equal(reservations,1);assert.equal(uploads,0)}
      if(scenario==='reload-storage-commit') {assert.equal(reservations,1);assert.equal(uploads,1)}
      if(scenario==='journal-write-denied'||scenario==='tampered-ack') {assert.equal(reservations,0);assert.equal(uploads,0)}
      assert.equal(await page.getByText(/PRIVATE-(FORGED-DRAFT|STORAGE-ERROR)/).count(),0)
      assert.deepEqual(errors,[])
      console.log('PASS: actual Timeline upload reload '+scenario)
    } finally {release?.();await page.close()}
  }
}

