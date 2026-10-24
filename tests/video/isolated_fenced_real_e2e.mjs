// Real disposable local Supabase stack E2E. NOT mocked. NEVER remote.
import assert from 'node:assert/strict'
import { createClient } from '@supabase/supabase-js'
import { randomUUID } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createIsolatedSupabaseVideoAdapters } from '../../api/video-isolated-supabase-adapters.ts'
import { createProductionSupabaseVideoAdapters } from '../../api/video-production-supabase-adapters.ts'
import { finalizeImmutableCandidate } from '../../api/video-finalize-core.ts'
import { createVideoMediaHandler } from '../../api/video-media.ts'
import { createVideoFinalizeHandler } from '../../api/video-finalize.ts'
import { verifyRealBrowserPlayback } from './isolated_browser_playback.mjs'

const env=Object.fromEntries(readFileSync(process.env.VIDEO_QA_ENV,'utf8').split('\n')
  .filter(x=>x.includes('=')).map(x=>{const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1).replace(/^["']|["']$/g,'')]}))
assert.throws(() => createProductionSupabaseVideoAdapters(
  'https://example.supabase.co','anon-test','service-test','jwt-test',
), /production video fenced release gate disabled/,
'production adapter must fail closed without an explicit release gate')
console.log('PASS: production video adapter remains fail-closed without audited release gate')
const url=env.API_URL
assert.equal(url,'http://127.0.0.1:56321','NEVER contact production')
const anon=env.ANON_KEY||env.PUBLISHABLE_KEY
const service=env.SERVICE_ROLE_KEY
assert.ok(anon&&service)
const client=createClient(url,anon,{auth:{persistSession:false,autoRefreshToken:false}})
const other=createClient(url,anon,{auth:{persistSession:false,autoRefreshToken:false}})
for(const [api,label] of [[client,'owner'],[other,'other']]){
  const {error}=await api.auth.signUp({email:`fenced-${label}-${randomUUID()}@example.invalid`,password:'isolated-Video-Password1!'})
  assert.ifError(error)
}
const owner=(await client.auth.getUser()).data.user.id
const otherId=(await other.auth.getUser()).data.user.id
assert.notEqual(owner,otherId)
const jwt=(await client.auth.getSession()).data.session.access_token
// Chromium on Linux runners may lack proprietary H.264 decoders; use supported VP8/WebM.
const path=`${owner}/${randomUUID()}.webm`
const dir=mkdtempSync(join(tmpdir(),'video-real-e2e-'))
let bytes
try {
 const output=join(dir,'video.webm')
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=black:s=64x64:r=10',
   '-t','2','-c:v','libvpx','-b:v','150k','-pix_fmt','yuv420p','-y',output],{timeout:30000})
 bytes=readFileSync(output)
} finally {rmSync(dir,{recursive:true,force:true})}
assert.ok(bytes.length>0&&bytes.length<20*1024*1024)
const storage=client.storage.from('post-videos')
assert.ifError((await storage.upload(path,bytes,{contentType:'video/webm',upsert:false})).error)
const adapters=createIsolatedSupabaseVideoAdapters(url,anon,service,jwt)
const first=await finalizeImmutableCandidate(jwt,path,'real isolated end-to-end',adapters)
assert.match(first,/^[0-9a-f-]{36}$/)
const second=await finalizeImmutableCandidate(jwt,path,'real isolated end-to-end',adapters)
assert.equal(second,first,'repeat finalization must be idempotent')
await assert.rejects(finalizeImmutableCandidate(jwt,path,'conflicting text',adapters),
  /fenced publication rejected/)
const admin=createClient(url,service,{auth:{persistSession:false,autoRefreshToken:false}})
const {data:post,error:postError}=await admin.from('posts')
  .select('id,user_id,video_path,video_generation,video_sha256,video_duration_seconds')
  .eq('id',first).single()
assert.ifError(postError)
assert.equal(post.user_id,owner)
assert.equal(post.video_path,path)
assert.match(post.video_sha256,/^[0-9a-f]{64}$/)
assert.ok(post.video_duration_seconds>0&&post.video_duration_seconds<=30)
const {data:generation,error:gError}=await admin.rpc('video_qa_storage_generation',
  {p_owner:owner,p_path:path})
assert.ifError(gError)
assert.equal(post.video_generation,generation)
const {data:reconciled,error:recError}=await admin.rpc('video_qa_reconcile_fenced',
  {p_owner:owner,p_path:path,p_generation:generation})
assert.ifError(recError)
assert.equal(reconciled,first)
const {error:clientPublish}=await client.rpc('video_qa_publish_fenced',{
 p_owner:owner,p_path:path,p_generation:generation,p_sha256:post.video_sha256,
 p_duration:post.video_duration_seconds,p_content:'forged client publish',
})
assert.ok(clientPublish,'authenticated browser must not execute trusted publish RPC')
const {error:badGeneration}=await admin.rpc('video_qa_publish_fenced',{
 p_owner:owner,p_path:path,p_generation:randomUUID(),p_sha256:post.video_sha256,
 p_duration:post.video_duration_seconds,p_content:'real isolated end-to-end',
})
assert.ok(badGeneration,'trusted RPC must reject stale or forged generation')
const {data:wrong,error:wrongError}=await admin.rpc('video_qa_reconcile_fenced',
  {p_owner:owner,p_path:path,p_generation:randomUUID()})
assert.ifError(wrongError)
assert.equal(wrong,null,'ABA mismatched generation must not reconcile')
const {error:overwritten}=await storage.update(path,Buffer.from('overwrite'),{contentType:'video/mp4'})
assert.ok(overwritten,'owner must not overwrite immutable staged media')
const deletion=await storage.remove([path])
assert.ok(deletion.error||!deletion.data?.length,'owner delete must be blocked')
const {data:ownerMedia,error:mediaError}=await storage.download(path)
assert.ifError(mediaError)
assert.deepEqual(Buffer.from(await ownerMedia.arrayBuffer()),bytes)
const {error:otherMedia}=await other.storage.from('post-videos').download(path)
assert.ok(otherMedia,'other user must not read owner private video')
const {data:visible,error:visibleError}=await client.from('posts')
 .select('id,video_path').eq('id',first).single()
assert.ifError(visibleError)
assert.equal(visible.id,first)
const {data:hidden,error:hiddenError}=await other.from('posts').select('id').eq('id',first)
assert.ifError(hiddenError)
assert.equal(hidden.length,0,'other user must not see private post')
// Execute the actual server media handler with a Vercel-compatible response
// recorder, backed by the real local Supabase Auth, PostgREST and Storage.
process.env.VITE_SUPABASE_URL=url
process.env.VITE_SUPABASE_ANON_KEY=anon
process.env.SUPABASE_SERVICE_ROLE_KEY=service
const finalizeHandler=createVideoFinalizeHandler(adapters,{isolatedLocalOnly:true})
async function invokeFinalize(token, body) {
 const headers={}
 const res={
   statusCode:200,body:null,
   setHeader(name,value){headers[name.toLowerCase()]=value;return this},
   status(code){this.statusCode=code;return this},
   json(data){this.body=data;return this},
   end(){return this},
 }
 const encoded=JSON.stringify(body)
 await finalizeHandler({method:'POST',
   headers:{authorization:'Bearer '+token,'content-length':String(Buffer.byteLength(encoded)),
     'content-type':'application/json'},body},res)
 return {status:res.statusCode,body:res.body,headers}
}
const viaHttp=await invokeFinalize(jwt,{object_path:path,content:'real isolated end-to-end'})
assert.equal(viaHttp.status,201,'actual finalize API boundary must succeed')
assert.equal(viaHttp.body.post_id,first)
const unauthorizedFinalize=await invokeFinalize(
 (await other.auth.getSession()).data.session.access_token,
 {object_path:path,content:'real isolated end-to-end'})
assert.equal(unauthorizedFinalize.status,403,'other user must not finalize owner media')
const mediaHandler=createVideoMediaHandler({isolatedLocalOnly:true})
async function invokeMedia(token) {
 const headers={}
 const res={
   statusCode:200, body:null,
   setHeader(name,value){headers[name.toLowerCase()]=value;return this},
   status(code){this.statusCode=code;return this},
   send(data){this.body=data;return this},
   end(){return this},
 }
 await mediaHandler({method:'GET',headers:{authorization:'Bearer '+token},
   query:{post_id:first}},res)
 return {status:res.statusCode,body:res.body,headers}
}
const ownerPlayback=await invokeMedia(jwt)
assert.equal(ownerPlayback.status,200,'authorized server media handler')
assert.deepEqual(ownerPlayback.body,bytes)
assert.equal(ownerPlayback.headers['content-type'],'video/webm')
const otherJwt=(await other.auth.getSession()).data.session.access_token
const deniedPlayback=await invokeMedia(otherJwt)
assert.equal(deniedPlayback.status,404,'unauthorized server media handler')
// Query the same real PostgREST posts feed used by Timeline.loadPosts.
// This is an actual RLS-protected feed read, not a mocked timeline query.
const {data:feed,error:feedError}=await client.from('posts').select('*')
  .order('created_at',{ascending:false})
assert.ifError(feedError)
const feedPost=feed.find(row=>row.id===first)
assert.ok(feedPost,'real timeline feed must contain published video')
assert.equal(feedPost.video_path,path)
assert.equal(feedPost.content,'real isolated end-to-end')
const {data:otherFeed,error:otherFeedError}=await other.from('posts').select('*')
  .order('created_at',{ascending:false})
assert.ifError(otherFeedError)
assert.ok(!otherFeed.some(row=>row.id===first),'RLS must exclude video from other user feed')
await verifyRealBrowserPlayback({postId:feedPost.id,jwt,deniedJwt:otherJwt,anon,service,bytes})
console.log('PASS: REAL PostgREST Timeline posts feed includes video for owner and excludes it for other user')
console.log('PASS: REAL isolated Supabase Auth JWT -> Storage HTTP immutable read -> ffprobe -> fenced PostgREST RPC -> idempotent timeline SELECT -> authorized video bytes; other user denied')
