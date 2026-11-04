import { test,before,after } from 'node:test'
import assert from 'node:assert/strict'
import path from 'node:path'
import { preview } from 'vite'
import { chromium } from 'playwright-core'
let server,browser,base
before(async()=>{
 server=await preview({configFile:path.resolve('vite.first-release.config.ts'),preview:{host:'127.0.0.1',port:0}})
 base='http://127.0.0.1:'+server.httpServer.address().port
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']})
})
after(async()=>{
 await browser?.close()
 if(server){server.httpServer.closeAllConnections();await new Promise(resolve=>server.httpServer.close(resolve))}
})
for(const viewport of [{width:390,height:844},{width:1280,height:800}]){
 for(const [route,title] of [['/tda','初回公開対象外'],['/player-type?result=synthetic','初回公開対象外'],['/timeline','初回公開準備中']]){
  test(viewport.width+' built artifact '+route,{timeout:15000},async()=>{
   const page=await browser.newPage({viewport}),external=[],errors=[]
   page.on('pageerror',error=>errors.push(error.message))
   await page.route('**/*',r=>{
    const url=r.request().url()
    if(!url.startsWith(base+'/')){external.push('external');return r.abort()}
    if(/\/(?:rest|auth|storage|api)\//.test(new URL(url).pathname)){external.push('data-api');return r.abort()}
    return r.continue()
   })
   try{
    await page.goto(base+route);await page.getByRole('heading',{name:title,exact:true}).waitFor()
    assert.deepEqual(errors,[]);assert.deepEqual(external,[])
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true)
    assert.doesNotMatch(await page.getByRole('navigation').innerText(),/TDA|診断|動画|ツール/)
   }finally{await page.close()}
  })
 }
}
