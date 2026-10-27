import assert from 'node:assert/strict'
import {createHash} from 'node:crypto'

// Actual Timeline in independent BrowserContexts, with real owner JWT/server
// inspection/RPC/Storage. Only response timing/loss and the clock are controlled.
export async function verifyRecoveryConcurrentTabs({browser,origin,jwt,anon,bytes,createConcurrentFixture}) {
 const fixture=await createConcurrentFixture()
 const contexts=await Promise.all([browser.newContext({viewport:{width:390,height:844}}),browser.newContext({viewport:{width:390,height:844}})])
 const tabs=await Promise.all(contexts.map(c=>c.newPage()))
 const errors=[],calls=[[],[]],holds=[],handlers=[]
 let round='initial',statusGates=[null,null],lost=false,timeoutResponse,timeoutDone
 const wait=async(predicate,label)=>{for(let n=0;n<700;n++){if(predicate())return;await new Promise(r=>setTimeout(r,20))}throw Error(label)}
 const hint=async(page)=>page.evaluate(()=>sessionStorage.getItem('poker-id-video-transfer-v1:'+window.__MULTITAB_OWNER))
 const idle=page=>page.waitForFunction(()=>![...document.querySelectorAll('[role="dialog"] button')].some(b=>b.textContent==='投稿中...'))
 const cleared=page=>page.waitForFunction(()=>sessionStorage.getItem('poker-id-video-transfer-v1:'+window.__MULTITAB_OWNER)===null)
 const reseed=async(page,version)=>page.evaluate(({path,hash,size,version})=>{
  const raw=JSON.stringify({owner:window.__MULTITAB_OWNER,path,sha256:hash,size,type:'video/webm',phase:'uploading',startedAt:Date.now()+version})
  sessionStorage.setItem('poker-id-video-transfer-v1:'+window.__MULTITAB_OWNER,raw);return raw
 },{path:fixture.path,hash:createHash('sha256').update(bytes).digest('hex'),size:bytes.length,version})
 try {
  await fixture.prepare()
  await fixture.audit(0,0)
  await fixture.acquireLock()
  await Promise.all(tabs.map(async(page,index)=>{
   page.on('pageerror',e=>errors.push(String(e)))
   await page.addInitScript(({jwt,anon,path,hash,size})=>{
    window.__VIDEO_QA_JWT=jwt;window.__VIDEO_QA_ANON=anon
    const owner=JSON.parse(atob(jwt.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
    window.__MULTITAB_OWNER=owner
    if(!sessionStorage.getItem('__multitab_seeded')) {
     sessionStorage.setItem('__multitab_seeded','true')
     sessionStorage.setItem('poker-id-video-transfer-v1:'+owner,JSON.stringify({owner,path,sha256:hash,size,type:'video/webm',phase:'uploading',startedAt:Date.now()}))
    }
   },{jwt,anon,path:fixture.path,hash:createHash('sha256').update(bytes).digest('hex'),size:bytes.length})
   await page.route('**/storage/v1/object/post-videos/**',route=>{
    if(['POST','PUT','DELETE'].includes(route.request().method())){errors.push('unexpected Storage mutation during recovery');return route.abort()}
    return route.continue()
   })
   await page.route('**/internal/video/finalize',async route=>{
    let done
    const finished=new Promise(resolve=>{done=resolve});handlers.push(finished)
    const thisRound=round,body=route.request().postDataJSON()
    calls[index].push({round:thisRound,action:body.action})
    try {
     assert.ok(['recovery_status','recovery_finalize'].includes(body.action),'no reserve/bind/upload during recovery')
     assert.equal(body.object_path,fixture.path)
     const response=await route.fetch({timeout:20000})
     assert.equal(response.status(),200,'real verified response, including concurrent first publication')
     const data=await response.json()
     if(body.action==='recovery_status') {
      assert.equal(data.state,thisRound==='initial'?'verified_ready':'published');assert.equal(data.ffprobe_verified,true)
      assert.equal(data.sha256,createHash('sha256').update(bytes).digest('hex'))
      if(['initial','retry-status','both-retry'].includes(thisRound))await new Promise(resolve=>{statusGates[index]=resolve;holds.push(resolve)})
     } else {
      assert.equal(data.state,'published')
      if(thisRound==='initial'&&index===0){lost=true;await route.abort('internetdisconnected');return}
      if(thisRound==='timeout'&&index===0) {
       timeoutResponse=data
       await new Promise(resolve=>{holds.push(resolve);timeoutDone=resolve})
      }
     }
     try{await route.fulfill({response})}catch{/* timed-out or disposed browser request */}
    } catch(error){errors.push(String(error));try{await route.abort()}catch{/* already disposed */}}
    finally{done()}
   })
   await page.goto(origin+'/tests/video/browser-real-timeline.html')
  }))
  await wait(()=>statusGates.every(Boolean),'both tabs must inspect the same unpublished object')
  const original=await hint(tabs[0])
  statusGates.forEach(release=>release());statusGates=[null,null]
  await fixture.waitBlocked(2)
  await fixture.audit(0,2)
  await fixture.releaseLock()
  await wait(()=>lost,'one real committed finalize response must be lost')
  await cleared(tabs[1]);await idle(tabs[0])
  assert.equal(await hint(tabs[0]),original,'lost response preserves the original uncertain locator')
  const postId=await fixture.audit(1,2)
  console.log('PASS: two independent Timeline tabs first-publish under real reservation row lock; lost response preserves journal; one post/two distinct consumed nonces')

  // The losing tab retries, receives a real committed response only after its
  // 30s UI deadline, then reloads with a newer local record. Keep the NEW
  // inspection paused while delivering the OLD response to prove no cleanup.
  round='timeout'
  await tabs[0].clock.install()
  await tabs[0].reload()
  await wait(()=>Boolean(timeoutResponse),'retry must commit before its response is delayed')
  const failed=tabs[0].waitForEvent('requestfailed',{predicate:r=>r.url().includes('/internal/video/finalize')})
  await tabs[0].clock.fastForward(30001);await failed;await idle(tabs[0])
  assert.equal(await hint(tabs[0]),original,'timeout preserves the uncertain record')
  assert.equal(await fixture.audit(1,3),postId)
  const newer=await reseed(tabs[0],1)
  round='retry-status';statusGates=[null,null]
  await tabs[0].reload()
  await wait(()=>Boolean(statusGates[0]),'newer retry must be inspecting before the old reply arrives')
  timeoutDone();timeoutDone=undefined
  await Promise.all(handlers.slice(0,-1))
  assert.equal(await hint(tabs[0]),newer,'late prior response cannot erase a newer tab record')
  assert.equal(await tabs[0].getByRole('dialog',{name:'新しい投稿'}).getByRole('button',{name:'投稿中...',exact:true}).isDisabled(),true,'old response cannot release the new recovery lock')
  statusGates[0]();statusGates=[null,null]
  await cleared(tabs[0])
  assert.equal(await fixture.audit(1,4),postId)
  console.log('PASS: committed response timeout then real retry preserves newer record against late old response; same post/fresh nonces')

  round='both-retry'
  await Promise.all(tabs.map((p,i)=>reseed(p,i+2)))
  await fixture.acquireLock()
  await Promise.all(tabs.map(p=>p.reload()))
  await wait(()=>statusGates.every(Boolean),'both retry tabs must independently re-inspect published object')
  statusGates.forEach(release=>release());statusGates=[null,null]
  await fixture.waitBlocked(2)
  await fixture.audit(1,6)
  await fixture.releaseLock()
  await Promise.all(tabs.map(cleared))
  assert.equal(await fixture.audit(1,6),postId)
  await Promise.all(handlers)
  assert.deepEqual(calls.map(tab=>tab.filter(c=>c.action==='recovery_finalize').length),[4,2],'bounded explicit retries; no automatic request loop')
  assert.deepEqual(errors,[])
  console.log('PASS: simultaneous two-tab retry serializes in DB; one immutable post, six unique consumed nonces, unchanged reservation/Storage/manifest and zero extra upload')
 } finally {
  holds.forEach(release=>release())
  await fixture.stop()
  await Promise.all(contexts.map(c=>c.close()))
 }
}
