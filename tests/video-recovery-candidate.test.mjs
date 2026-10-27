import assert from 'node:assert/strict'
import test from 'node:test'
import {createVideoFinalizeHandler} from '../api/video-finalize.ts'
import {readFileSync} from 'node:fs'

test('recovery candidate cannot be activated against production or by release flags',async()=>{
 const oldUrl=process.env.VITE_SUPABASE_URL,oldAnon=process.env.VITE_SUPABASE_ANON_KEY,original=globalThis.fetch
 let calls=0
 globalThis.fetch=async()=>{calls++;throw Error('network must not be reached')}
 try {
  for(const [url,isolated] of [['http://127.0.0.1:56321',false],['https://example.supabase.co',true]]) {
   process.env.VITE_SUPABASE_URL=url;process.env.VITE_SUPABASE_ANON_KEY='fixture-anon'
   for(const action of ['bind_recovery','recovery_status']) {
    const body={action,object_path:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb.webm'}
    let status
    const res={setHeader(){return res},status(n){status=n;return res},json(){return res},end(){return res}}
    await createVideoFinalizeHandler(undefined,{isolatedLocalOnly:isolated})({method:'POST',headers:{authorization:'Bearer fixture.jwt.token','content-type':'application/json','content-length':String(JSON.stringify(body).length)},body},res)
    assert.equal(status,503)
   }
  }
  assert.equal(calls,0)
 } finally {
  if(oldUrl===undefined)delete process.env.VITE_SUPABASE_URL;else process.env.VITE_SUPABASE_URL=oldUrl
  if(oldAnon===undefined)delete process.env.VITE_SUPABASE_ANON_KEY;else process.env.VITE_SUPABASE_ANON_KEY=oldAnon
  globalThis.fetch=original
 }
})
test('client recovery remains advisory and default-disabled without clearing journals',()=>{
 const source=readFileSync(new URL('../src/videoRecoveryCandidate.ts',import.meta.url),'utf8')
 assert.match(source,/VIDEO_RECOVERY_CANDIDATE_ENABLED = false/)
 assert.doesNotMatch(source,/sessionStorage|\.remove\(|finalizeUploadedVideo\(/)
})
