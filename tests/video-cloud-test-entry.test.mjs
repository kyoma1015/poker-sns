import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {assertCloudTestRequestConfiguration as check} from '../server/video-cloud-test-target.mjs'
test('normal disabled release does not opt into cloud mode',()=>assert.equal(check({}),null))
test('test target without complete opt-in fails before IO',()=>{
 for(const env of [{VITE_SUPABASE_URL:'https://hbhyuotzginwysrineyo.supabase.co'},{VIDEO_CLOUD_TEST_ENABLED:'false'},{VIDEO_CLOUD_TEST_PROJECT_REF:'wrong'}]){
  assert.throws(()=>check(env),/configuration rejected/)
 }
})
test('real finalize and media entrypoints guard before all outbound IO',()=>{
 for(const file of ['api/video-finalize.ts','api/video-media.ts']){
 const source=readFileSync(new URL('../'+file,import.meta.url),'utf8')
 const guard=source.indexOf('try { assertCloudTestRequestConfiguration(process.env) }')
 assert.ok(guard>0)
 for(const marker of ['createClient(url','await viewer.','await fetch(','spawn(executable']){
  const pos=source.indexOf(marker)
  if(pos>=0)assert.ok(guard<pos,file+': guard precedes '+marker)
 }
 assert.match(source.slice(guard,guard+150),/status\(503\)/)
 }
})
