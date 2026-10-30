import assert from 'node:assert/strict'

// Actual Timeline, real local feed/auth; lifecycle notifications and delayed
// metadata/social response are controlled explicitly, with no production IO.
export async function verifyComposerLifecycle({browser,origin,jwt,anon,bytes}) {
  for (const scenario of ['close-validation','switch-social','signout-preview','unmount-submit','double-text','auth-network-retry','early-foreign-restore']) {
    const page=await browser.newPage()
    const errors=[]
    page.on('pageerror',e=>errors.push(String(e)))
    let writes=0
    await page.route('**/internal/video/finalize',route=>{writes++;return route.abort()})
    try {
      await page.addInitScript(({jwt,anon,scenario})=>{
        window.__VIDEO_QA_JWT=jwt;window.__VIDEO_QA_ANON=anon
        if(scenario==='early-foreign-restore') {
          const id=JSON.parse(atob(jwt.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
          window.__VIDEO_QA_INITIAL_AUTH_ID='cccccccc-cccc-4ccc-8ccc-cccccccccccc'
          sessionStorage.setItem('poker-id-pending-video-v1',JSON.stringify({owner:id,path:id+'/dddddddd-dddd-4ddd-8ddd-dddddddddddd.webm',content:'PRIVATE-RESTORED-DRAFT'}))
          const replies=[]
          window.__VIDEO_QA_GET_USER=()=>new Promise(resolve=>{
            replies.push(resolve)
            window.__LIFECYCLE_RESTORE_RELEASE=()=>{for(const reply of replies) reply({data:{user:{id}},error:null})}
          })
        }
      },{jwt,anon,scenario})
      await page.goto(origin+'/tests/video/browser-real-timeline.html')
      if(scenario==='early-foreign-restore') {
        await page.waitForFunction(()=>Boolean(window.__LIFECYCLE_RESTORE_RELEASE))
        await page.evaluate(()=>window.__LIFECYCLE_RESTORE_RELEASE())
        await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))
        assert.equal(await page.getByRole('dialog',{name:'新しい投稿'}).count(),0,'early foreign identity blocks stale restore')
        assert.equal(await page.getByText('PRIVATE-RESTORED-DRAFT',{exact:false}).count(),0,'prior-owner content stays hidden')
        assert.deepEqual(errors,[])
        console.log('PASS: actual Timeline composer lifecycle '+scenario)
        continue
      }
      await page.locator('article video').first().waitFor({timeout:20000})
      await page.evaluate(()=>window.dispatchEvent(new Event('poker-id-open-compose')))
      const composer=page.getByRole('dialog',{name:'新しい投稿'})
      await composer.waitFor()
      const picker=page.locator('input[type="file"][accept*="video/mp4"]')
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
      if(scenario==='double-text' || scenario==='auth-network-retry') {
        await composer.locator('textarea').fill('isolated single-flight text')
        let inserts=0
        await page.route('**/rest/v1/posts*',route=>{
          if(route.request().method()!=='POST') return route.continue()
          inserts++
          return route.fulfill({status:503,contentType:'application/json',body:'{"message":"PRIVATE-INSERT-ERROR"}'})
        })
        await page.evaluate(throws=>{
          window.__LIFECYCLE_AUTH_STARTED=0
          window.__VIDEO_QA_GET_USER=()=>{
            window.__LIFECYCLE_AUTH_STARTED++
            if(throws) throw new Error('PRIVATE-AUTH-NETWORK-ERROR')
            return new Promise(resolve=>{
              window.__LIFECYCLE_AUTH_RELEASE=()=>{
                const jwt=window.__VIDEO_QA_JWT
                const id=JSON.parse(atob(jwt.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
                resolve({data:{user:{id}},error:null})
              }
            })
          }
        },scenario==='auth-network-retry')
        await composer.getByRole('button',{name:'投稿する',exact:true}).evaluate(button=>{button.click();button.click()})
        await page.waitForFunction(()=>window.__LIFECYCLE_AUTH_STARTED>0)
        assert.equal(await page.evaluate(()=>window.__LIFECYCLE_AUTH_STARTED),1,'one authentication for synchronous double submit')
        if(scenario==='double-text') {
          await page.evaluate(()=>window.__LIFECYCLE_AUTH_RELEASE())
          await composer.getByText(/投稿できませんでした/).waitFor()
          assert.equal(inserts,1,'one INSERT for double text submission')
        } else {
          await composer.getByText(/通信とログイン状態を確認/).waitFor()
          assert.equal(await page.getByText('PRIVATE-AUTH-NETWORK-ERROR',{exact:false}).count(),0)
          await page.evaluate(()=>{delete window.__VIDEO_QA_GET_USER})
          await Promise.all([
            page.waitForResponse(response=>response.url().includes('/rest/v1/posts') && response.request().method()==='POST'),
            composer.getByRole('button',{name:'投稿する',exact:true}).click(),
          ])
          await page.waitForFunction(()=>[...document.querySelectorAll('[role="dialog"] button')].some(button=>button.textContent==='投稿する' && !button.disabled))
          await composer.getByText(/通信とログイン状態を確認/).waitFor()
          assert.equal(inserts,1,'retry reaches one INSERT after thrown auth request')
        }
        assert.equal(await composer.getByRole('button',{name:'投稿する',exact:true}).isEnabled(),true,'failed publication releases lock')
        assert.equal(await page.getByText('PRIVATE-INSERT-ERROR',{exact:false}).count(),0,'provider error stays private')
      } else if(scenario==='switch-social') {
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
          await page.evaluate(()=>{
            const id=JSON.parse(atob(window.__VIDEO_QA_JWT.split('.')[1].replaceAll('-','+').replaceAll('_','/'))).sub
            window.__VIDEO_QA_TRIGGER_AUTH('TOKEN_REFRESHED',id)
          })
          await settle()
          assert.equal(await composer.locator('video').getAttribute('src'),url,'same-user refresh preserves draft')
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

