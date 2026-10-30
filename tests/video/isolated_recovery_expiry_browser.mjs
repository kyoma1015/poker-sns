import assert from 'node:assert/strict'
import {createHash} from 'node:crypto'

export async function verifyRecoveryRealExpiry({browser,origin,anon,bytes,createExpiryFixture}) {
 for(const kind of ['jwt','reservation-published','reservation-unpublished','reservation-precommit']) {
  const fixture=await createExpiryFixture(kind)
  const contexts=await Promise.all([browser.newContext(),browser.newContext()])
  const tabs=await Promise.all(contexts.map(context=>context.newPage()))
  const holds=[],finished=[],errors=[],calls=[[],[]]
  let gates=[null,null],heldReply,replyDone,replyFinished,retry=false
  const wait=async(test,label)=>{for(let n=0;n<700;n++){if(test())return;await new Promise(r=>setTimeout(r,20))}throw Error(label)}
  const hint=page=>page.evaluate(()=>sessionStorage.getItem('poker-id-video-transfer-v1:'+window.__EXPIRY_OWNER))
  const idle=page=>page.waitForFunction(()=>![...document.querySelectorAll('[role="dialog"] button')].some(button=>button.textContent==='投稿中...'))
  let baselinePost
  try {
   await fixture.prepare()
   if(kind==='reservation-published')baselinePost=await fixture.publishBaseline()
   await Promise.all(tabs.map(async(page,index)=>{
    page.on('pageerror',error=>errors.push(String(error)))
    await page.addInitScript(({jwt,anon,path,sha,size})=>{
     window.__VIDEO_QA_JWT=jwt;window.__VIDEO_QA_ANON=anon
     const owner=JSON.parse(atob(jwt.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
     window.__EXPIRY_OWNER=owner
     if(!sessionStorage.getItem('__expiry_seeded')){
      sessionStorage.setItem('__expiry_seeded','true')
      sessionStorage.setItem('poker-id-video-transfer-v1:'+owner,JSON.stringify({owner,path,sha256:sha,size,type:'video/webm',phase:'uploading',startedAt:Date.now()}))
     }
    },{jwt:fixture.tokens[index],anon,path:fixture.path,sha:createHash('sha256').update(bytes).digest('hex'),size:bytes.length})
    await page.route('**/storage/v1/object/post-videos/**',route=>{
     if(['POST','PUT','DELETE'].includes(route.request().method())){errors.push('unexpected recovery Storage mutation');return route.abort()}
     return route.continue()
    })
    await page.route('**/internal/video/finalize',async route=>{
     let done
     const complete=new Promise(resolve=>{done=resolve});finished.push(complete)
     const body=route.request().postDataJSON();calls[index].push(body.action)
     try {
      assert.ok(['recovery_status','recovery_finalize'].includes(body.action));assert.equal(body.object_path,fixture.path)
      const response=await route.fetch({timeout:20000})
      if(body.action==='recovery_status') {
       if(retry){assert.equal(response.status(),410,'expired reservation is rejected before another finalize');await route.fulfill({response});return}
       assert.equal(response.status(),200)
       const state=await response.json();assert.equal(state.ffprobe_verified,true)
       assert.equal(state.state,kind==='reservation-published'?'published':'verified_ready')
       await new Promise(resolve=>{gates[index]=resolve;holds.push(resolve)})
      } else {
       assert.equal(response.status(),kind==='jwt'&&index===1?200:409,'actual finalize expiration/valid-competitor result')
       if(index===0){heldReply=true;replyFinished=complete;await new Promise(resolve=>{replyDone=resolve;holds.push(resolve)})}
      }
      try{await route.fulfill({response})}catch{/* obsolete or cancelled UI */}
     } catch(error){errors.push(String(error));try{await route.abort()}catch{/* disposed */}}
     finally{done()}
    })
    await page.goto(origin+'/tests/video/browser-real-timeline.html')
   }))
   await wait(()=>gates.every(Boolean),'both Timeline tabs must complete real inspection before the deadline race')
   const original=await hint(tabs[0])
   if(kind==='jwt') {
    await fixture.acquireLock()
    const token=await fixture.mintShortJwt()
    await tabs[0].evaluate(token=>{window.__VIDEO_QA_GET_SESSION=()=>({data:{session:{access_token:token,user:{id:window.__EXPIRY_OWNER}}},error:null})},token)
   } else {
    await fixture.ageReservation(2)
    await fixture.acquireLock({storage:kind==='reservation-precommit'})
   }
   gates.forEach(release=>release());gates=[null,null]
   await fixture.waitBlocked(2)
   if(kind==='jwt')await fixture.waitJwtExpiry()
   else await fixture.waitReservationExpiry()
   await fixture.releaseLock()
   await wait(()=>heldReply,'real expired finalize reply is held for a newer-record assertion')
   if(kind==='jwt')await tabs[1].waitForFunction(()=>sessionStorage.getItem('poker-id-video-transfer-v1:'+window.__EXPIRY_OWNER)===null)
   else await idle(tabs[1])
   const newer=await tabs[0].evaluate(()=>{
    const key='poker-id-video-transfer-v1:'+window.__EXPIRY_OWNER,value=JSON.parse(sessionStorage.getItem(key));value.startedAt++
    const raw=JSON.stringify(value);sessionStorage.setItem(key,raw);return raw
   })
   assert.notEqual(newer,original)
   replyDone();await replyFinished;await idle(tabs[0]);await Promise.all(finished)
   assert.equal(await hint(tabs[0]),newer,'late expired response cannot erase a newer local recovery locator')
   const composer=tabs[0].getByRole('dialog',{name:'新しい投稿'})
   await composer.locator('textarea').fill('owned lock releases safely after expiry denial')
   assert.equal(await composer.getByRole('button',{name:'投稿する',exact:true}).isEnabled(),true)
   if(kind==='jwt') {
    const id=await fixture.assertJwtRejected();assert.ok(id)
    await fixture.assertPostgrestExpiry()
    console.log('PASS: actual short signed JWT accepted by GoTrue/PostgREST, expires during real reservation lock; DB JWT-expiry rejection/no nonce, valid competing post=1, expired Auth/REST/API retry denied, newer journal retained')
   } else {
    assert.equal(await fixture.auditReservationExpired(),baselinePost)
    retry=true
    await Promise.all(tabs.map(page=>page.reload()))
    await Promise.all(tabs.map(idle))
    // Wait for actual status denial, not the transient pre-inspection UI.
    await wait(()=>calls.every(tab=>tab.filter(action=>action==='recovery_status').length===2),'both expired-reservation retries must reach real API status')
    await Promise.all(finished);await Promise.all(tabs.map(idle))
    assert.equal(await hint(tabs[0]),newer)
    assert.deepEqual(calls.map(tab=>tab.filter(action=>action==='recovery_finalize').length),[1,1],'no further finalize after reservation expiry')
    await fixture.auditReservationExpired()
    console.log('PASS: actual DB-origin one-hour reservation expiry during lock wait '+kind+'; manifest remains future, rejected nonce=0, original post/owner/SHA/generation/content/duration preserved, API reload retry stopped')
   }
   assert.deepEqual(errors,[])
  } finally {
   holds.forEach(release=>release())
   await fixture.stop()
   await Promise.all(contexts.map(context=>context.close()))
  }
 }
}
