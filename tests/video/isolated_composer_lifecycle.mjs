import assert from 'node:assert/strict'

// Actual Timeline, real local feed/auth; lifecycle notifications and delayed
// metadata/social response are controlled explicitly, with no production IO.
export async function verifyComposerLifecycle({browser,origin,jwt,anon,bytes}) {
  for (const scenario of ['close-validation','switch-social','signout-preview','unmount-submit']) {
    const page=await browser.newPage()
    const errors=[]
    page.on('pageerror',e=>errors.push(String(e)))
    let writes=0
    await page.route('**/internal/video/finalize',route=>{writes++;return route.abort()})
    try {
      await page.addInitScript(({jwt,anon})=>{window.__VIDEO_QA_JWT=jwt;window.__VIDEO_QA_ANON=anon},{jwt,anon})
      await page.goto(origin+'/tests/video/browser-real-timeline.html')
      await page.locator('article video').first().waitFor({timeout:20000})
      await page.evaluate(()=>window.dispatchEvent(new Event('poker-id-open-compose')))
      const composer=page.getByRole('dialog',{name:'新しい投稿'})
      await composer.waitFor()
      const picker=page.locator('input[accept="video/mp4,video/webm"]')
      const holdMetadata=()=>page.evaluate(()=>{
        const create=document.createElement.bind(document)
        document.createElement=(tag,...args)=>{
          if(tag!=='video') return create(tag,...args)
          document.createElement=create
          const fake={duration:2,preload:'',src:'',onloadedmetadata:null,onerror:null,removeAttribute(){},load(){}}
          window.__LIFECYCLE_METADATA=fake
          return fake
        }
      })
      const settle=()=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))
      if(scenario==='switch-social') {
        await composer.locator('textarea').fill('旧アカウントの下書き')
        await page.evaluate(()=>{
          window.__VIDEO_QA_SOCIAL={get_my_post_style_snapshot:()=>new Promise(resolve=>{
            window.__LIFECYCLE_RELEASE=()=>resolve({data:[{count:3,aggression:50,looseness:50}],error:null})
          })}
        })
        await composer.getByRole('button',{name:'＋ 添付',exact:true}).click()
        await composer.getByRole('button',{name:/自分への他者評価を添付/}).click()
        await page.waitForFunction(()=>Boolean(window.__LIFECYCLE_RELEASE))
        await page.evaluate(()=>window.__VIDEO_QA_TRIGGER_AUTH('SIGNED_IN','cccccccc-cccc-4ccc-8ccc-cccccccccccc'))
        await page.evaluate(()=>window.__LIFECYCLE_RELEASE())
        await settle()
        await page.evaluate(()=>window.dispatchEvent(new Event('poker-id-open-compose')))
        await composer.waitFor()
        assert.equal(await composer.locator('textarea').inputValue(),'','old account draft cleared')
        assert.equal(await composer.getByText('他者評価 · プレイスタイル',{exact:false}).count(),0,'late prior-account attachment discarded')
      } else if(scenario==='close-validation') {
        await holdMetadata()
        await picker.setInputFiles({name:'held.webm',mimeType:'video/webm',buffer:bytes})
        await page.waitForFunction(()=>Boolean(window.__LIFECYCLE_METADATA?.onloadedmetadata))
        await composer.getByRole('button',{name:'×',exact:true}).click()
        await page.evaluate(()=>window.__LIFECYCLE_METADATA.onloadedmetadata())
        await settle()
        await page.evaluate(()=>window.dispatchEvent(new Event('poker-id-open-compose')))
        await composer.waitFor()
        assert.equal(await composer.locator('video').count(),0,'closed validation cannot resurrect preview')
      } else {
        await picker.setInputFiles({name:'accepted.webm',mimeType:'video/webm',buffer:bytes})
        await composer.locator('video').waitFor()
        const url=await composer.locator('video').getAttribute('src')
        await page.evaluate(()=>{
          window.__LIFECYCLE_REVOKED=[]
          const revoke=URL.revokeObjectURL.bind(URL)
          URL.revokeObjectURL=url=>{window.__LIFECYCLE_REVOKED.push(url);revoke(url)}
        })
        if(scenario==='signout-preview') {
          await page.evaluate(()=>window.__VIDEO_QA_TRIGGER_SIGN_OUT())
          await settle()
          await page.evaluate(()=>window.dispatchEvent(new Event('poker-id-open-compose')))
          await composer.waitFor()
          assert.equal(await composer.locator('video').count(),0,'signed-out draft discarded')
        } else {
          await holdMetadata()
          // Two synchronous submissions while metadata is held must share a lock.
          await composer.getByRole('button',{name:'投稿する',exact:true}).evaluate(button=>{button.click();button.click()})
          await page.waitForFunction(()=>Boolean(window.__LIFECYCLE_METADATA?.onloadedmetadata))
          const authCalls=await page.evaluate(()=>window.__VIDEO_QA_GET_USER_CALLS)
          await page.evaluate(()=>window.__VIDEO_QA_UNMOUNT())
          await page.evaluate(()=>window.__LIFECYCLE_METADATA.onloadedmetadata())
          await settle()
          assert.equal(await page.evaluate(()=>window.__VIDEO_QA_GET_USER_CALLS),authCalls,'unmounted validation cannot begin upload authentication')
          assert.equal(writes,0,'unmounted submission must never reserve/finalize')
        }
        assert.ok((await page.evaluate(()=>window.__LIFECYCLE_REVOKED)).includes(url),'draft Blob released')
      }
      assert.deepEqual(errors,[],'no unhandled lifecycle errors')
      console.log('PASS: actual Timeline composer lifecycle '+scenario)
    } finally { await page.close() }
  }
}
