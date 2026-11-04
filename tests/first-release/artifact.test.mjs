import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync,readFileSync,readdirSync } from 'node:fs'
import path from 'node:path'
const out='dist-first-release'
test('candidate artifact has exactly the canonical root HTML',()=>{
 assert(existsSync(path.join(out,'index.html')),'missing canonical index.html')
 assert(!existsSync(path.join(out,'first-release.html')),'old candidate HTML must not remain as another entry')
 const htmls=readdirSync(out).filter(x=>x.endsWith('.html'))
 assert.deepEqual(htmls,['index.html'])
})
test('canonical HTML references built local assets, never source/dev entry',()=>{
 const html=readFileSync(path.join(out,'index.html'),'utf8')
 assert(!html.includes('/src/'))
 const scripts=[...html.matchAll(/<script[^>]+src="([^"]+)"/g)].map(m=>m[1])
 assert(scripts.length>0)
 for(const src of scripts){
  assert(src.startsWith('/assets/')||src.startsWith('./assets/'))
  assert(existsSync(path.join(out,src.replace(/^\//,''))))
 }
})
test('compiled candidate retains the locked and deferred UI messages',()=>{
 const js=readdirSync(out,{recursive:true}).filter(x=>x.endsWith('.js')).map(x=>readFileSync(path.join(out,x),'utf8')).join('\n')
 assert(js.includes('初回公開準備中'));assert(js.includes('初回公開対象外'))
})
