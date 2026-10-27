import assert from 'node:assert/strict'
import {createHash} from 'node:crypto'

// Reuse one immutable owner-scoped staged object: interruption tests must not
// burn new reservation quota or upload replacement bytes.
export async function verifyRecoveryBoundaries({browser,origin,jwt,anon,bytes,boundaryPath,assertBoundaryPosts}) {
 const cases=[
  ['initial-auth-timeout','auth','timeout'],['initial-auth-unmount','auth','unmount'],['initial-auth-account-switch','auth','account'],
  ['status-navigation','status','navigate'],['status-unmount','status','unmount'],
  ['status-account-switch','status','account'],['session-invalid','none','invalid'],
  ['status-disconnect','status','disconnect'],['status-timeout','status','timeout'],
  ['session-timeout','session','timeout'],['status-newer-record','status','newer'],
  ['finalize-navigation','finalize','navigate'],['finalize-account-switch','finalize','account'],
  ['finalize-newer-pending','finalize','pending'],['strict-double-operation','status','double'],
 ]
 let published=false
 for(const [name,phase,action] of cases) {
  const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true})
  const errors=[],calls=[]
  let release,feedRelease,feedDone,responseDone,completed=false,newRaw
  const responseFinished=new Promise(resolve=>{responseDone=resolve})
  page.on('pageerror',e=>errors.push(String(e)))
  try {
   if(action==='timeout')await page.clock.install()
   await page.addInitScript(({jwt,anon,path,hash,size,invalid,hang,strict,authHang})=>{
    window.__VIDEO_QA_JWT=jwt;window.__VIDEO_QA_ANON=anon;window.__VIDEO_QA_STRICT=strict
    const owner=JSON.parse(atob(jwt.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
    window.__BOUNDARY_OWNER=owner
    sessionStorage.setItem('poker-id-video-transfer-v1:'+owner,JSON.stringify({owner,path,sha256:hash,size,type:'video/webm',phase:'uploading',startedAt:Date.now()}))
    if(authHang){
     window.__BOUNDARY_AUTH_RELEASES=[]
     let first=true
     window.__VIDEO_QA_GET_USER=real=>{
      if(!first)return real()
      first=false
      return new Promise(resolve=>window.__BOUNDARY_AUTH_RELEASES.push(()=>real().then(resolve)))
     }
    }
    if(invalid)window.__VIDEO_QA_GET_SESSION=()=>({data:{session:null},error:null})
    if(hang){
     window.__BOUNDARY_SESSION_RESOLVERS=[]
     window.__VIDEO_QA_GET_SESSION=()=>new Promise(resolve=>window.__BOUNDARY_SESSION_RESOLVERS.push(()=>resolve({data:{session:{access_token:jwt,user:{id:owner}}},error:null})))
    }
   },{jwt,anon,path:boundaryPath,hash:createHash('sha256').update(bytes).digest('hex'),size:bytes.length,invalid:action==='invalid',hang:phase==='session',strict:action==='double',authHang:phase==='auth'})
   if(name==='status-account-switch'||name==='initial-auth-timeout') await page.route('**/rest/v1/posts*',async route=>{
    if(route.request().method()!=='GET')return route.continue()
    const response=await route.fetch()
    await new Promise(resolve=>{feedRelease=resolve})
    try{await route.fulfill({response})}finally{feedDone?.()}
   })
   await page.route('**/internal/video/finalize',async route=>{
    const body=route.request().postDataJSON();calls.push(body)
    const target=phase==='status'?'recovery_status':'recovery_finalize'
    if(phase==='auth'||phase==='session'||phase==='none'||body.action!==target)return route.continue()
    if(action==='disconnect'){completed=true;return route.abort('internetdisconnected')}
    const response=await route.fetch()
    assert.equal(response.status(),200,'real boundary response before interruption')
    if(phase==='finalize')published=true
    await new Promise(resolve=>{release=resolve})
    try{await route.fulfill({response})}catch{/* actual request cancelled */}
    completed=true;responseDone()
   })
   await page.goto(origin+'/tests/video/browser-real-timeline.html')
   const composer=page.getByRole('dialog',{name:'新しい投稿'})
   const original=await page.evaluate(()=>sessionStorage.getItem('poker-id-video-transfer-v1:'+window.__BOUNDARY_OWNER))
   const settle=()=>page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))))
   const idle=()=>page.waitForFunction(()=>![...document.querySelectorAll('[role="dialog"] button')].some(b=>b.textContent==='投稿中...'))
   if(phase==='auth') {
    await page.waitForFunction(()=>window.__BOUNDARY_AUTH_RELEASES?.length===1)
    if(action==='timeout') {
     await page.clock.fastForward(30001)
     await composer.getByText(/重複を防ぐため動画の再送信を停止/).first().waitFor()
     await composer.getByText('動画の復旧状態を確認できません。ログインと通信を確認して再読み込みしてください。',{exact:true}).waitFor()
     for(let wait=0;!feedRelease&&wait<1000;wait++)await page.waitForTimeout(20)
     assert.ok(feedRelease,'real owner feed response is held until after the stop notice')
     const feedFinished=new Promise(resolve=>{feedDone=resolve})
     feedRelease();feedRelease=undefined;await feedFinished
     await page.locator('article').first().waitFor()
     assert.equal(await composer.getByRole('status').getByText('動画の復旧状態を確認できません。ログインと通信を確認して再読み込みしてください。',{exact:true}).isVisible(),true,'a later successful feed refresh must not erase the recovery stop reason')
    } else if(action==='unmount')await page.evaluate(()=>window.__VIDEO_QA_UNMOUNT())
    else await page.evaluate(()=>window.__VIDEO_QA_TRIGGER_AUTH('SIGNED_IN','ffffffff-ffff-4fff-8fff-ffffffffffff'))
    await page.evaluate(()=>Promise.all(window.__BOUNDARY_AUTH_RELEASES.map(resolve=>resolve())))
    await settle()
    assert.equal(calls.length,0,'late initial auth cannot start inspection/finalize after timeout, disposal or identity change')
   } else if(action==='invalid'||action==='disconnect') {
    await composer.getByText(/重複を防ぐため動画の再送信を停止/).first().waitFor()
    await idle()
    assert.equal(calls.filter(c=>c.action==='recovery_finalize').length,0)
    if(action==='invalid')assert.equal(calls.length,0,'expired/missing session sends no authenticated request')
    else assert.ok(completed)
   } else if(phase==='session') {
    await composer.waitFor()
    await page.waitForFunction(()=>window.__BOUNDARY_SESSION_RESOLVERS?.length>0)
    await page.clock.fastForward(30001)
    await idle()
    await page.evaluate(()=>window.__BOUNDARY_SESSION_RESOLVERS.forEach(resolve=>resolve()))
    await settle()
    assert.equal(calls.length,0,'late session resolution after deadline cannot send recovery request')
    await composer.locator('textarea').fill('lock released after session timeout')
    assert.equal(await composer.getByRole('button',{name:'投稿する',exact:true}).isEnabled(),true)
   } else {
    for(let wait=0;!release&&wait<1000;wait++)await page.waitForTimeout(20)
    assert.ok(release,'must reach exact held response boundary')
    if(action==='navigate'||action==='unmount'||action==='account'||action==='timeout') {
     const aborted=page.waitForEvent('requestfailed',{predicate:r=>r.url().includes('/internal/video/finalize')})
     if(action==='navigate') {
      await page.waitForFunction(()=>Boolean(window.__VIDEO_QA_NAVIGATE))
      await page.evaluate(()=>window.__VIDEO_QA_NAVIGATE('/away'))
      await page.getByText('隔離別画面',{exact:true}).waitFor()
     } else if(action==='unmount')await page.evaluate(()=>window.__VIDEO_QA_UNMOUNT())
     else if(action==='account') {
      if(name==='status-account-switch'){
       for(let wait=0;!feedRelease&&wait<1000;wait++)await page.waitForTimeout(20)
       assert.ok(feedRelease,'initial owner feed is also in flight')
      }
      await page.evaluate(()=>window.__VIDEO_QA_TRIGGER_AUTH('SIGNED_IN','ffffffff-ffff-4fff-8fff-ffffffffffff'))
     } else await page.clock.fastForward(30001)
     await aborted
     release();release=undefined
     await responseFinished
     if(feedRelease){const done=new Promise(resolve=>{feedDone=resolve});feedRelease();feedRelease=undefined;await done}
     await settle()
     if(action==='account') {
      assert.equal(await page.locator('article').count(),0,'late owner feed cannot reappear for switched identity')
      await page.evaluate(()=>window.dispatchEvent(new Event('poker-id-open-compose')))
      await composer.locator('textarea').fill('new account lock is released')
      assert.equal(await composer.getByRole('button',{name:'投稿する',exact:true}).isEnabled(),true)
     }
     if(action==='timeout'){await idle();assert.ok(completed)}
    } else {
     if(action==='newer')newRaw=await page.evaluate(()=>{
      const key='poker-id-video-transfer-v1:'+window.__BOUNDARY_OWNER,r=JSON.parse(sessionStorage.getItem(key));r.sha256='0'.repeat(64)
      const raw=JSON.stringify(r);sessionStorage.setItem(key,raw);return raw
     })
     if(action==='pending')newRaw=await page.evaluate(path=>{
      const raw=JSON.stringify({owner:window.__BOUNDARY_OWNER,path,content:'newer pending draft must survive'})
      sessionStorage.setItem('poker-id-pending-video-v1',raw);return raw
     },boundaryPath)
     if(action==='double') {
      await composer.locator('textarea').fill('double operation must not publish this text')
      const activeSubmit=composer.getByRole('button',{name:'投稿中...',exact:true})
      assert.equal(await activeSubmit.isDisabled(),true)
      await activeSubmit.dispatchEvent('click')
      await activeSubmit.dispatchEvent('click')
     }
     release();release=undefined
     if(action==='newer') {
      await idle()
      assert.equal(calls.filter(c=>c.action==='recovery_finalize').length,0,'new intent stops old inspection before finalize')
     } else {
      await page.waitForFunction(()=>sessionStorage.getItem('poker-id-video-transfer-v1:'+window.__BOUNDARY_OWNER)===null)
      await assertBoundaryPosts(1)
      assert.equal(calls.filter(c=>c.action==='recovery_finalize').length,1,'single flight under delayed response/double operation')
     }
    }
   }
   if(!['pending','double'].includes(action)) {
    const remaining=await page.evaluate(()=>sessionStorage.getItem('poker-id-video-transfer-v1:'+window.__BOUNDARY_OWNER))
    assert.equal(remaining,newRaw??original,'unconfirmed/abandoned recovery preserves exact current record')
   }
   if(action==='pending')assert.equal(await page.evaluate(()=>sessionStorage.getItem('poker-id-pending-video-v1')),newRaw,'confirmed old response cannot erase newer pending content')
   if(phase!=='finalize'&&action!=='double')assert.equal(calls.filter(c=>c.action==='recovery_finalize').length,0)
   assert.equal(calls.filter(c=>c.action==='reserve'||c.action==='bind_recovery').length,0,'boundary interruption cannot create reservations')
   assert.equal(await page.locator('video:not(article video)').count(),0,'no attachment resurrection')
   await assertBoundaryPosts(published?1:0)
   assert.deepEqual(errors,[])
   console.log('PASS: actual Timeline recovery boundary '+name)
  } finally {release?.();feedRelease?.();await page.close()}
 }
 // Two independent tab stores are untrusted locators for the same already
 // published object. Both requests must still validate on the real server;
 // neither tab can create a second post or clear the other tab's newer intent.
 const tabs=await Promise.all([browser.newPage(),browser.newPage()])
 const releases=[],failures=[],requests=[[],[]]
 try {
  await Promise.all(tabs.map(async(page,index)=>{
   page.on('pageerror',error=>failures.push(String(error)))
   await page.addInitScript(({jwt,anon,path,hash,size})=>{
    window.__VIDEO_QA_JWT=jwt;window.__VIDEO_QA_ANON=anon
    const owner=JSON.parse(atob(jwt.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
    window.__BOUNDARY_OWNER=owner
    sessionStorage.setItem('poker-id-video-transfer-v1:'+owner,JSON.stringify({owner,path,sha256:hash,size,type:'video/webm',phase:'uploading',startedAt:Date.now()}))
   },{jwt,anon,path:boundaryPath,hash:createHash('sha256').update(bytes).digest('hex'),size:bytes.length})
   await page.route('**/internal/video/finalize',async route=>{
    const body=route.request().postDataJSON();requests[index].push(body.action)
    if(body.action!=='recovery_status')return route.continue()
    const response=await route.fetch();assert.equal(response.status(),200)
    await new Promise(resolve=>{releases[index]=resolve})
    await route.fulfill({response})
   })
   await page.goto(origin+'/tests/video/browser-real-timeline.html')
  }))
  for(let wait=0;releases.filter(Boolean).length!==2&&wait<1000;wait++)await tabs[0].waitForTimeout(20)
  assert.equal(releases.filter(Boolean).length,2,'both tabs have independently inspected the published object')
  releases.forEach(release=>release())
  await Promise.all(tabs.map(page=>page.waitForFunction(()=>sessionStorage.getItem('poker-id-video-transfer-v1:'+window.__BOUNDARY_OWNER)===null)))
  for(const calls of requests)assert.deepEqual(calls,['recovery_status','recovery_finalize'],'each tab performs exactly one verified idempotent recovery, without reserve/upload')
  await assertBoundaryPosts(1)
  assert.deepEqual(failures,[])
  console.log('PASS: actual Timeline simultaneous two-tab published recovery remains one post')
 } finally {releases.forEach(release=>release?.());await Promise.all(tabs.map(page=>page.close()))}
}
