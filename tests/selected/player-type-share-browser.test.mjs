import test, { before, after } from 'node:test'
import assert from 'node:assert/strict'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import { chromium } from 'playwright-core'
const root = fileURLToPath(new URL('../../', import.meta.url))
let server, browser, base
before(async () => {
  server = await createServer({ root, configFile: false, server: {host:'127.0.0.1',port:0}, plugins:[{name:'diagnosis-fixture-only',enforce:'pre',resolveId(source,importer){if(source==='./supabase' && importer?.includes('/src/'))return path.join(root,'tests/browser/player-type-share-supabase.ts')},configureServer(s){s.middlewares.use('/__qa-d',(req,res)=>{res.setHeader('Content-Type','text/html');res.end('<div id="root"></div><script type="module" src="/tests/browser/player-type-share-entry.tsx"></script>')})}}],esbuild:{jsx:'automatic'} })
  await server.listen(); base=`http://127.0.0.1:${server.httpServer.address().port}`
  browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',headless:true,args:['--no-sandbox']})
})
after(async()=>{await browser?.close();await server?.close()})
async function fixture(mode='normal'){
 const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true})
 await page.route('**/*',route=>route.request().url().startsWith(base+'/')?route.continue():route.abort())
 await page.addInitScript(mode=>{
  window.qaImageMode=mode;window.qaCreatedImages=0;window.qaDownloads=[];window.qaEncodingDone=false
  const Original=window.Image
  window.Image=class extends Original {set src(value){window.qaCreatedImages++;if(window.qaImageMode==='hang'){window.qaPendingImage=this;return}if(window.qaImageMode==='error'){queueMicrotask(()=>this.onerror?.(new Event('error')));return}super.src=value}get src(){return super.src}}
  const originalBlob=HTMLCanvasElement.prototype.toBlob
  HTMLCanvasElement.prototype.toBlob=function(...args){if(window.qaImageMode==='encode-hang')return;const [callback,...rest]=args;return originalBlob.call(this,value=>{callback(value);window.qaEncodingDone=true},...rest)}
  const originalGet=HTMLCanvasElement.prototype.getContext
  HTMLCanvasElement.prototype.getContext=function(...args){if(window.qaImageMode==='canvas-error')throw new Error('qa-private-path-and-token');return originalGet.apply(this,args)}
  const originalClick=HTMLAnchorElement.prototype.click
  HTMLAnchorElement.prototype.click=function(){window.qaDownloads.push(this.download);return originalClick.call(this)}
 },mode)
 await page.clock.install()
 await page.goto(base+'/__qa-d')
 await page.getByRole('button',{name:'画像を保存',exact:false}).waitFor()
 return page
}
const save=page=>page.getByRole('button',{name:'画像を保存',exact:false})
test('mobile real canvas exports a nonempty PNG with the existing filename',async()=>{
 const p=await fixture();try{const download=p.waitForEvent('download');await save(p).click();const d=await download;assert.equal(d.suggestedFilename(),'PokerID_lion_qa-resul.png');const file=await d.createReadStream();let size=0;for await(const c of file)size+=c.length;assert.ok(size>1000);await save(p).waitFor();assert.equal(await save(p).isEnabled(),true)}finally{await p.close()}
})
test('image failures redact details and allow the same result to retry successfully',async()=>{
 const p=await fixture('canvas-error');try{await save(p).click();await p.getByRole('alert').getByText('画像の保存に失敗しました。もう一度お試しください。',{exact:true}).waitFor({timeout:2000});assert.doesNotMatch(await p.locator('body').innerText(),/qa-private/);await p.evaluate(()=>window.qaImageMode='normal');const d=p.waitForEvent('download');await save(p).click();await d;assert.equal(await p.getByRole('alert').count(),0)}finally{await p.close()}
})
for(const mode of ['hang','encode-hang'])test(`${mode} reaches a finite deadline and enables retry`,async()=>{
 const p=await fixture(mode);try{await save(p).click();await p.waitForFunction(()=>window.qaCreatedImages===1);if(mode==='encode-hang')await p.waitForTimeout(100);await p.clock.runFor(15001);await p.getByRole('alert').waitFor({timeout:2000});assert.equal(await save(p).isEnabled(),true);await p.evaluate(()=>window.qaImageMode='normal');const d=p.waitForEvent('download');await save(p).click();await d}finally{await p.close()}
})
test('an old pending image cannot download after restarting diagnosis',async()=>{
 const p=await fixture('hang');try{await save(p).click();await p.getByRole('button',{name:'もう一度診断する',exact:false}).click();await p.getByText('QUESTION 1',{exact:true}).waitFor();await p.evaluate(()=>Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src').set.call(window.qaPendingImage,'/animals/lion.png'));await p.waitForFunction(()=>window.qaEncodingDone);assert.deepEqual(await p.evaluate(()=>window.qaDownloads),[])}finally{await p.close()}
})
test('two synchronous save activations start only one image operation',async()=>{
 const p=await fixture('hang');try{await save(p).evaluate(button=>{button.click();button.click()});assert.equal(await p.evaluate(()=>window.qaCreatedImages),1)}finally{await p.close()}
})

test('changing to another saved result invalidates a pending PNG operation',async()=>{
 const p=await fixture('hang');try{await save(p).click();await p.getByRole('button',{name:'QA別の結果',exact:true}).click();await p.getByRole('heading',{name:'QA次のライオン',exact:true}).waitFor();await p.evaluate(()=>Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src').set.call(window.qaPendingImage,'/animals/lion.png'));await p.waitForFunction(()=>window.qaEncodingDone);assert.deepEqual(await p.evaluate(()=>window.qaDownloads),[]);assert.equal(await save(p).isEnabled(),true)}finally{await p.close()}
})
