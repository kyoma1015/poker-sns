import { test,before,after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { createServer } from 'vite'
import { chromium } from 'playwright-core'
const root=process.cwd()
let server,browser,cacheDir,base
const deferred=['/tda','/tda?mode=quiz','/player-type','/player-type?result=synthetic','/tools','/results','/profile/card','/player/synthetic/card','/profile/results/new','/profile/amusement-ring/new','/profile/cash-game/new','/player/synthetic/rate','/videos','/unknown/feature']
before(async()=>{
 cacheDir=await fs.mkdtemp(path.join(os.tmpdir(),'first-release-'))
 const app=await fs.readFile('src/App.tsx','utf8')
 const names=new Set([...app.matchAll(/^import (\w+) from '\.\/(\w+)'/gm)].map(m=>m[2]))
 server=await createServer({root,cacheDir,configFile:false,esbuild:{jsx:'automatic'},server:{host:'127.0.0.1',port:0},
 plugins:[{name:'isolated-first-release',enforce:'pre',
 resolveId(source,importer){
  if(importer?.includes('/src/') && source==='./supabase')return '\0first-release-auth'
  if(importer?.includes('/src/') && names.has(source.replace(/^\.\//,'')))return '\0first-release-component:'+source
 },
 load(id){
  if(id==='\0first-release-auth')return 'export const supabase={auth:{getSession:async()=>({data:{session:null}}),getUser:async()=>({data:{user:null}}),signOut:async()=>({error:null})}}'
  if(id.startsWith('\0first-release-component:'))return 'import {useEffect,createElement} from "react";export default function Fixture(){useEffect(()=>{window.firstReleaseStats.mounts.push('+JSON.stringify(id)+')},[]);return createElement("h1",null,"legacy component fixture")}'
 },
 configureServer(s){s.middlewares.use((req,res,next)=>{
  const p=new URL(req.url,'http://fixture').pathname
  if(!p.startsWith('/@')&&!p.startsWith('/src/')&&!p.startsWith('/tests/')&&!p.startsWith('/node_modules/')&&!p.includes('.')){
   res.setHeader('Content-Type','text/html');res.end('<div id="root"></div><script type="module" src="/tests/browser/first-release-entry.tsx"></script>')
  }else next()
 })}
 }]})
 await server.listen();base='http://127.0.0.1:'+server.httpServer.address().port
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']})
})
after(async()=>{await browser?.close();await server?.close();if(cacheDir)await fs.rm(cacheDir,{recursive:true,force:true})})
async function pageFor(viewport){
 const page=await browser.newPage({viewport})
 await page.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort())
 return page
}
for(const viewport of [{width:390,height:844},{width:1280,height:800}]){
 for(const route of deferred)test(viewport.width+' deferred '+route,{timeout:12000},async()=>{
  const page=await pageFor(viewport)
  try{
   await page.goto(base+route);await page.getByRole('heading',{name:'初回公開対象外',exact:true}).waitFor({timeout:1500})
   assert.deepEqual(await page.evaluate(()=>window.firstReleaseStats.mounts),[])
   assert.doesNotMatch(await page.getByRole('navigation').innerText(),/TDA|診断|動画|ツール/)
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true)
  }finally{await page.close()}
 })
 test(viewport.width+' candidate navigation and back never activate unapproved modules',{timeout:12000},async()=>{
  const page=await pageFor(viewport)
  try{
   await page.goto(base+'/timeline');await page.getByRole('heading',{name:'初回公開準備中',exact:true}).waitFor({timeout:1500})
   await page.getByRole('link',{name:'DM',exact:true}).click();await page.waitForURL(base+'/dm')
   await page.goto(base+'/tda');await page.getByRole('heading',{name:'初回公開対象外',exact:true}).waitFor()
   await page.goBack();await page.getByRole('heading',{name:'初回公開準備中',exact:true}).waitFor()
   assert.deepEqual(await page.evaluate(()=>window.firstReleaseStats.mounts),[])
  }finally{await page.close()}
 })
}
