// Real disposable local Supabase stack E2E. NOT mocked. NEVER remote.
import assert from 'node:assert/strict'
import { createClient } from '@supabase/supabase-js'
import { randomUUID } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createIsolatedSupabaseVideoAdapters } from '../../api/video-isolated-supabase-adapters.ts'
import { finalizeImmutableCandidate } from '../../api/video-finalize-core.ts'

const env=Object.fromEntries(readFileSync(process.env.VIDEO_QA_ENV,'utf8').split('\n')
  .filter(x=>x.includes('=')).map(x=>{const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1).replace(/^["']|["']$/g,'')]}))
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
const path=`${owner}/${randomUUID()}.mp4`
const dir=mkdtempSync(join(tmpdir(),'video-real-e2e-'))
let bytes
try {
 const output=join(dir,'video.mp4')
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=black:s=64x64:r=10',
   '-t','2','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart','-y',output],{timeout:30000})
 bytes=readFileSync(output)
} finally {rmSync(dir,{recursive:true,force:true})}
assert.ok(bytes.length>0&&bytes.length<20*1024*1024)
const storage=client.storage.from('post-videos')
assert.ifError((await storage.upload(path,bytes,{contentType:'video/mp4',upsert:false})).error)
const adapters=createIsolatedSupabaseVideoAdapters(url,anon,service,jwt)
const first=await finalizeImmutableCandidate(jwt,path,'real isolated end-to-end',adapters)
assert.match(first,/^[0-9a-f-]{36}$/)
const second=await finalizeImmutableCandidate(jwt,path,'real isolated end-to-end',adapters)
assert.equal(second,first,'repeat finalization must be idempotent')
await assert.rejects(finalizeImmutableCandidate(jwt,path,'conflicting text',adapters),
  /commit outcome unknown|conflicting/)
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
console.log('PASS: REAL isolated Supabase Auth JWT -> Storage HTTP immutable read -> ffprobe -> fenced PostgREST RPC -> idempotent timeline SELECT -> authorized video bytes; other user denied')
