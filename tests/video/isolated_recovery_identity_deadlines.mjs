import assert from 'node:assert/strict'
import {createHash} from 'node:crypto'

// All sessions, revocation, row locks and wall-clock deadlines below are real
// disposable services. Browser response holding only fixes the race ordering.
export async function verifyRecoveryIdentityDeadlines({browser,origin,anon,bytes,createIdentityFixture}) {
 const fixture=await createIdentityFixture()
 const contexts=await Promise.all([browser.newContext(),browser.newContext()])
 const pages=await Promise.all(contexts.map(c=>c.newPage()))
 const holds=[],finished=[],calls=[[],[]],errors=[]
 let gates=[null,null],round=0,expectedStatus=[409,200]
 const wait=async(test,label)=>{for(let n=0;n<700;n++){if(test())return;await new Promise(r=>setTimeout(r,20))}throw Error(label)}
 const hint=page=>page.evaluate(()=>sessionStorage.getItem('poker-id-video-transfer-v1:'+window.__IDENTITY_OWNER))
 const idle=page=>page.waitForFunction(()=>![...document.querySelectorAll('[role="dialog"] button')].some(b=>b.textContent==='投稿中...'))
 const cleared=page=>page.waitForFunction(()=>sessionStorage.getItem('poker-id-video-transfer-v1:'+window.__IDENTITY_OWNER)===null)
 const seed=async(page,jwt,version)=>page.evaluate(({jwt,path,sha,size,version})=>{
  sessionStorage.setItem('__identity_jwt',jwt)
  const raw=JSON.stringify({owner:window.__IDENTITY_OWNER,path,sha256:sha,size,type:'video/webm',phase:'uploading',startedAt:Date.now()+version})
  sessionStorage.setItem('poker-id-video-transfer-v1:'+window.__IDENTITY_OWNER,raw);return raw
 },{jwt,path:fixture.path,sha:createHash('sha256').update(bytes).digest('hex'),size:bytes.length,version})
 try {
  await fixture.prepare()
  await fixture.acquireLock()
  await Promise.all(pages.map(async(page,index)=>{
   page.on('pageerror',error=>errors.push(String(error)))
   await page.addInitScript(({jwt,anon,path,sha,size})=>{
    const token=sessionStorage.getItem('__identity_jwt')||jwt
    window.__VIDEO_QA_JWT=token;window.__VIDEO_QA_ANON=anon
    const owner=JSON.parse(atob(token.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
    window.__IDENTITY_OWNER=owner
    if(!sessionStorage.getItem('__identity_seeded')) {
     sessionStorage.setItem('__identity_seeded','true')
     sessionStorage.setItem('poker-id-video-transfer-v1:'+owner,JSON.stringify({owner,path,sha256:sha,size,type:'video/webm',phase:'uploading',startedAt:Date.now()}))
    }
   },{jwt:fixture.tokens[index],anon,path:fixture.path,sha:createHash('sha256').update(bytes).digest('hex'),size:bytes.length})
   await page.route('**/storage/v1/object/post-videos/**',route=>{
    if(['POST','PUT','DELETE'].includes(route.request().method())){errors.push('unexpected recovery Storage mutation');return route.abort()}
    return route.continue()
   })
   await page.route('**/internal/video/finalize',async route=>{
    let done
    finished.push(new Promise(resolve=>{done=resolve}))
    const body=route.request().postDataJSON(),thisRound=round
    calls[index].push(body.action)
    try {
     assert.ok(['recovery_status','recovery_finalize'].includes(body.action));assert.equal(body.object_path,fixture.path)
     const response=await route.fetch({timeout:20000})
     if(body.action==='recovery_status') {
      assert.equal(response.status(),200)
      const state=await response.json();assert.equal(state.ffprobe_verified,true)
      assert.equal(state.state,thisRound===0?'verified_ready':'published')
      await new Promise(resolve=>{gates[index]=resolve;holds.push(resolve)})
     } else assert.equal(response.status(),expectedStatus[index],'exact real API denial/success at the blocked publication boundary')
     try{await route.fulfill({response})}catch{/* deliberately obsolete component */}
    } catch(error){errors.push(String(error));try{await route.abort()}catch{/* disposed */}}
    finally{done()}
   })
   await page.goto(origin+'/tests/video/browser-real-timeline.html')
  }))
  await wait(()=>gates.every(Boolean),'two sessions must both inspect before revocation')
  const firstRaw=await hint(pages[0])
  gates.forEach(release=>release());gates=[null,null]
  await fixture.waitBlocked(2)
  await fixture.revokeLosingSession()
  await fixture.releaseLock()
  await cleared(pages[1]);await idle(pages[0]);await Promise.all(finished)
  fixture.assertRevokedRejected()
  assert.equal(await hint(pages[0]),firstRaw,'revoked session cannot erase its uncertain recovery locator')
  const postId=await fixture.auditRevocation()
  console.log('PASS: actual two-tab recovery revokes only one real Auth session during reservation lock; denied attempt leaves no nonce, valid session publishes one immutable post')

  // A new real session replaces the revoked one. Only its trusted server
  // attestation is shortened (and correctly re-signed after real ffprobe).
  round=1
  const replacement=await fixture.newLosingSession()
  fixture.shortenAttestation(replacement)
  const newer=await seed(pages[0],replacement,1)
  await seed(pages[1],fixture.tokens[1],2)
  await fixture.acquireLock()
  await Promise.all(pages.map(page=>page.reload()))
  await wait(()=>gates.every(Boolean),'both retry sessions independently inspect the same publication')
  gates.forEach(release=>release());gates=[null,null]
  await fixture.waitBlocked(2)
  await fixture.waitLosingExpiry()
  await fixture.releaseLock()
  await cleared(pages[1]);await idle(pages[0]);await Promise.all(finished)
  fixture.assertLosingExpiryRejected()
  assert.equal(await hint(pages[0]),newer,'expired attestation reply cannot clear its current record')
  assert.equal(await fixture.auditExpiry(),postId)
  console.log('PASS: real reservation wait crosses one trusted attestation deadline; expired attempt rolls back nonce, valid competing retry keeps the same single post')

  // Shared manifest expiry means BOTH attempts must stop. An existing valid
  // publication must survive; no fixture extends an expired reservation.
  round=2;expectedStatus=[409,409]
  fixture.stopShortening()
  await seed(pages[0],replacement,3);await seed(pages[1],fixture.tokens[1],4)
  await fixture.acquireLock()
  await Promise.all(pages.map(page=>page.reload()))
  await wait(()=>gates.every(Boolean),'both sessions inspect before the shared server deadline')
  const originals=await Promise.all(pages.map(hint))
  gates.forEach(release=>release());gates=[null,null]
  await fixture.waitBlocked(2)
  await fixture.expireManifestWhileBlocked()
  await fixture.releaseLock()
  await Promise.all(pages.map(idle));await Promise.all(finished)
  assert.deepEqual(await Promise.all(pages.map(hint)),originals,'expired shared manifest cannot clear either locator')
  assert.equal(await fixture.auditManifestExpiry(),postId)
  for(const page of pages) {
   const composer=page.getByRole('dialog',{name:'新しい投稿'})
   await composer.locator('textarea').fill('independent lock released after denied recovery')
   assert.equal(await composer.getByRole('button',{name:'投稿する',exact:true}).isEnabled(),true,'denial releases only its own UI lock')
  }
  assert.deepEqual(calls.map(tab=>tab.filter(action=>action==='recovery_finalize').length),[3,3])
  assert.deepEqual(errors,[])
  console.log('PASS: shared manifest expires while both RPCs wait in PostgreSQL; both rejected with no new nonce/post, existing single publication and both journals retained')
 } finally {
  holds.forEach(release=>release())
  await fixture.stop()
  await Promise.all(contexts.map(context=>context.close()))
 }
}
