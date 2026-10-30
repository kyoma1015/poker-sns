// Actual Timeline handlers with explicitly synthetic social RPC/table data.
// Video and feed still use the disposable local Auth/Storage/PostgREST stack.
import assert from 'node:assert/strict'

export async function verifyAttachmentRequestRaces({browser,origin,jwt,anon,bytes}) {
  const cases=[
    {kind:'diagnosis',key:'get_my_latest_player_type_v2',label:/自己診断を添付/,selected:'隔離診断',data:[{result_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',animal_name_ja:'隔離診断',catchphrase:'隔離テスト',result_type_key:'L01',completed_at:'2026-01-01'}]},
    {kind:'result',key:'poker_results',label:/戦績を添付/,selected:'隔離戦績',data:[{id:'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',tournament_name:'隔離戦績',played_at:'2026-01-01',entry_count:null,rank:null,rank_unknown:true,is_itm:false,total_entry_fee:0,prize_amount:0}]},
    {kind:'rating',key:'get_my_post_style_snapshot',label:/自分への他者評価を添付/,selected:'他者評価 · プレイスタイル',data:[{count:3,aggression:50,looseness:50}]},
  ]
  for(const c of cases) {
    for(const order of ['attachment-wins','video-wins','request-throws']) {
      const page=await browser.newPage()
      const errors=[]
      page.on('pageerror',e=>errors.push(String(e)))
      try {
        await page.addInitScript(({jwt,anon})=>{window.__VIDEO_QA_JWT=jwt;window.__VIDEO_QA_ANON=anon},{jwt,anon})
        await page.goto(origin+'/tests/video/browser-real-timeline.html')
        await page.locator('article video').first().waitFor({timeout:20000})
        await page.waitForFunction(()=>![...document.querySelectorAll('article')].some(a=>a.textContent?.includes('動画を読み込み中')))
        await page.evaluate(()=>window.dispatchEvent(new Event('poker-id-open-compose')))
        const composer=page.getByRole('dialog',{name:'新しい投稿'})
        await composer.waitFor()
        const picker=page.locator('input[type="file"][accept*="video/mp4"]')
        const beginRequest=async()=>{
          await composer.getByRole('button',{name:'＋ 添付',exact:true}).click()
          await composer.getByRole('button',{name:c.label}).click()
          if(c.kind==='result') await composer.getByRole('button',{name:/トーナメント戦績/}).click()
        }
        const chooseLoaded=async()=>{
          if(c.kind==='diagnosis') await composer.getByRole('button',{name:/隔離診断/}).click()
          if(c.kind==='result') await composer.getByRole('button',{name:/トーナメント · 隔離戦績/}).click()
        }
        await page.evaluate(({key,data,throws})=>{
          window.__VIDEO_QA_SOCIAL={}
          window.__SOCIAL_STARTED=false
          window.__VIDEO_QA_SOCIAL[key]=()=>{
            window.__SOCIAL_STARTED=true
            if(throws) throw new Error('PRIVATE-ATTACHMENT-ERROR')
            return new Promise(resolve=>{window.__SOCIAL_RELEASE=()=>resolve({data,error:null})})
          }
        },{key:c.key,data:c.data,throws:order==='request-throws'})
        if(order==='attachment-wins') {
          await page.evaluate(()=>{
            const create=document.createElement.bind(document)
            document.createElement=(tag,...args)=>{
              if(tag!=='video') return create(tag,...args)
              document.createElement=create
              const fake={duration:2,preload:'',src:'',onloadedmetadata:null,onerror:null,removeAttribute(){},load(){}}
              window.__SOCIAL_VIDEO_METADATA=fake
              return fake
            }
          })
          await picker.setInputFiles({name:'pending.webm',mimeType:'video/webm',buffer:bytes})
          await page.waitForFunction(()=>Boolean(window.__SOCIAL_VIDEO_METADATA?.onloadedmetadata))
          await beginRequest()
          await page.waitForFunction(()=>window.__SOCIAL_STARTED)
          await page.evaluate(()=>window.__SOCIAL_RELEASE())
          await chooseLoaded()
          await composer.getByText(c.selected,{exact:false}).first().waitFor()
          await page.evaluate(()=>window.__SOCIAL_VIDEO_METADATA.onloadedmetadata())
          await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))
          assert.equal(await composer.locator('video').count(),0,c.kind+' must suppress older video validation')
          assert.equal(await composer.getByRole('button',{name:'投稿する',exact:true}).isEnabled(),true,c.kind+' remains submittable')
        } else if(order==='video-wins') {
          await beginRequest()
          await page.waitForFunction(()=>window.__SOCIAL_STARTED)
          await picker.setInputFiles({name:'newer-video.webm',mimeType:'video/webm',buffer:bytes})
          const video=composer.locator('video')
          await video.waitFor()
          const url=await video.getAttribute('src')
          await page.evaluate(()=>window.__SOCIAL_RELEASE())
          await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))
          assert.equal(await video.getAttribute('src'),url,'late '+c.kind+' cannot replace current video')
          assert.equal(await composer.getByText(c.selected,{exact:false}).count(),0,'late '+c.kind+' cannot show stale data')
          assert.equal(await composer.getByRole('button',{name:'投稿する',exact:true}).isEnabled(),true,'video remains submittable')
        } else {
          await beginRequest()
          await composer.getByText(/取得できませんでした。もう一度お試しください。/).waitFor()
          assert.equal(await page.getByText('PRIVATE-ATTACHMENT-ERROR',{exact:false}).count(),0,'raw exception must stay private')
          await page.evaluate(({key,data})=>{window.__VIDEO_QA_SOCIAL[key]=()=>({data,error:null})},{key:c.key,data:c.data})
          // Result loader stays on its category screen, so go back to menu first.
          if(c.kind==='result') {
            await composer.getByRole('button',{name:'‹ 戻る',exact:true}).click()
            await composer.getByRole('button',{name:'‹ 戻る',exact:true}).click()
          }
          await composer.getByRole('button',{name:c.label}).click()
          if(c.kind==='result') await composer.getByRole('button',{name:/トーナメント戦績/}).click()
          await chooseLoaded()
          await composer.getByText(c.selected,{exact:false}).first().waitFor()
          assert.equal(await composer.getByRole('button',{name:'投稿する',exact:true}).isEnabled(),true,'failed '+c.kind+' request can recover')
        }
        assert.deepEqual(errors,[],'no unhandled Timeline errors for '+c.kind+'/'+order)
        console.log('PASS: actual Timeline social attachment '+c.kind+' '+order)
      } finally {await page.close()}
    }
  }
}

