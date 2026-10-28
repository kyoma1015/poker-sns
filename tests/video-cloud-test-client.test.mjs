import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {assertVideoCloudTestClient as check} from '../src/videoCloudTestGuard.ts'
const origin='https://poker-id-video-test-fixture.vercel.app'
const valid=()=>({PROD:true,VITE_VIDEO_CLOUD_TEST_ENABLED:'true',VITE_SUPABASE_URL:'https://hbhyuotzginwysrineyo.supabase.co',VITE_VIDEO_CLOUD_TEST_ORIGIN:origin})
test('dedicated client config accepts without enabling existing video release',()=>{check(valid(),origin);check({VITE_SUPABASE_URL:'https://example.supabase.co'})})
test('misconfigured cloud client rejects production mix and origins',()=>{
 for(const patch of [{VITE_SUPABASE_URL:'https://ephptepeuespnxtzdqby.supabase.co'},{PROD:false},{VITE_VIDEO_SERVER_ENABLED:'true'},{VITE_VIDEO_CLOUD_TEST_ENABLED:'false'},{VITE_VIDEO_CLOUD_TEST_ORIGIN:'https://poker-sns-vert.vercel.app'},{VITE_SUPABASE_SERVICE_ROLE_KEY:'fixture'}]){
 assert.throws(()=>check({...valid(),...patch},origin))
 }
 assert.throws(()=>check(valid(),'https://poker-sns-vert.vercel.app'))
 assert.throws(()=>check({VITE_SUPABASE_URL:valid().VITE_SUPABASE_URL},origin))
})
test('startup fence and upload/API gates precede outbound client IO',()=>{
 const source=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8')
 const startup=source('src/supabase.ts')
 assert.ok(startup.indexOf('assertCurrentVideoCloudTestClient()')<startup.indexOf('export const supabase = createClient'))
 const upload=source('src/videoUpload.ts')
 const start=upload.indexOf('export async function uploadPostVideo')
 assert.ok(upload.indexOf('assertCurrentVideoCloudTestClient()',start)<upload.indexOf('await supabase.auth.getUser()',start))
 assert.ok(upload.includes('assertCurrentVideoCloudTestClient()\n    const { error } = await withVideoUploadRequest'))
 const api=source('src/videoApi.ts')
 for(const name of ['finalizeUploadedVideo','reserveVideoObjectPath','loadAuthorizedVideo']){
 const s=api.slice(api.indexOf('export async function '+name))
 assert.ok(s.indexOf('assertCurrentVideoCloudTestClient()')<s.indexOf('await fetch('))
 }
})
