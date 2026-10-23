import assert from 'node:assert/strict'
import { createClient } from '@supabase/supabase-js'
import { randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
const env=Object.fromEntries(readFileSync(process.env.VIDEO_QA_ENV,'utf8').split('\n').filter(x=>x.includes('=')).map(x=>{const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1).replace(/^["']|["']$/g,'')]}))
const url=env.API_URL||'http://127.0.0.1:56321'
const key=env.ANON_KEY||env.PUBLISHABLE_KEY
assert.match(url,/^http:\/\/(127\.0\.0\.1|localhost):56321\/?$/,'refuse remote Supabase API')
assert.ok(key,'missing local anon key')
const client=()=>createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}})
const owner=client(), viewer=client()
for(const [api,name] of [[owner,'owner'],[viewer,'viewer']]){
 const email=`video-${name}-${randomUUID()}@example.invalid`
 const {error}=await api.auth.signUp({email,password:'video-isolated-test-Password1!'})
 assert.ifError(error)
}
const ownerId=(await owner.auth.getUser()).data.user?.id
const viewerId=(await viewer.auth.getUser()).data.user?.id
assert.ok(ownerId&&viewerId&&ownerId!==viewerId)
const bucket='post-videos'
const path=`${ownerId}/${randomUUID()}.mp4`
const bytes=Buffer.from('isolated-storage-http-qa')
const upload=await owner.storage.from(bucket).upload(path,bytes,{contentType:'video/mp4',upsert:false})
assert.ifError(upload.error)
const read=await owner.storage.from(bucket).download(path)
assert.ifError(read.error)
assert.equal(Buffer.compare(Buffer.from(await read.data.arrayBuffer()),bytes),0)
const denied=await viewer.storage.from(bucket).download(path)
assert.ok(denied.error,'viewer downloaded private object')
const signDenied=await viewer.storage.from(bucket).createSignedUrl(path,300)
assert.ok(signDenied.error,'viewer signed owner object')
const sign=await owner.storage.from(bucket).createSignedUrl(path,300)
assert.ifError(sign.error)
assert.ok(sign.data?.signedUrl)
const signedFetch=await fetch(sign.data.signedUrl)
assert.equal(signedFetch.status,200)
assert.equal(Buffer.compare(Buffer.from(await signedFetch.arrayBuffer()),bytes),0)
const forbidden=await viewer.storage.from(bucket).upload(`${ownerId}/${randomUUID()}.mp4`,bytes,{contentType:'video/mp4'})
assert.ok(forbidden.error,'viewer wrote owner path')
const oversized=await owner.storage.from(bucket).upload(`${ownerId}/${randomUUID()}.mp4`,Buffer.alloc(20971521),{contentType:'video/mp4'})
assert.ok(oversized.error,'20MiB+1 upload was accepted')
const viewerDelete=await viewer.storage.from(bucket).remove([path])
// Storage may return an empty successful deletion list under RLS; verify persistence below.
if (!viewerDelete.error) assert.ok(!viewerDelete.data?.length,'viewer delete reported a deleted owner object')
const afterViewerDelete=await owner.storage.from(bucket).download(path)
assert.ifError(afterViewerDelete.error)
assert.equal(Buffer.compare(Buffer.from(await afterViewerDelete.data.arrayBuffer()),bytes),0,'viewer deleted owner object')
const removed=await owner.storage.from(bucket).remove([path])
assert.ifError(removed.error)
const afterDeleteSigned=await fetch(sign.data.signedUrl)
assert.notEqual(afterDeleteSigned.status,200,'signed URL still serves deleted object')
const gone=await owner.storage.from(bucket).download(path)
assert.ok(gone.error,'deleted object still available')
const orphan=`${ownerId}/${randomUUID()}.mp4`
assert.ifError((await owner.storage.from(bucket).upload(orphan,bytes,{contentType:'video/mp4'})).error)
// Simulated failed publication; cleanup is a test harness, not production behavior.
const failedPublish=true
if(failedPublish) assert.ifError((await owner.storage.from(bucket).remove([orphan])).error)
assert.ok((await owner.storage.from(bucket).download(orphan)).error)

const serviceKey=env.SERVICE_ROLE_KEY
assert.ok(serviceKey,'missing isolated service role key')
const server=createClient(url,serviceKey,{auth:{persistSession:false,autoRefreshToken:false}})
const publishPath=`${ownerId}/${randomUUID()}.mp4`
const videoBytes=Buffer.from('isolated-publish-object')
assert.ifError((await owner.storage.from(bucket).upload(publishPath,videoBytes,{contentType:'video/mp4'})).error)
const publishPayload={p_owner:ownerId,p_path:publishPath,p_content:'isolated idempotency E2E'}
const first=await server.rpc('video_qa_publish',publishPayload)
assert.ifError(first.error)
assert.ok(first.data)
const second=await server.rpc('video_qa_publish',publishPayload)
assert.ifError(second.error)
assert.equal(second.data,first.data,'duplicate publication created another post')
const conflicting=await server.rpc('video_qa_publish',{...publishPayload,p_content:'different'})
assert.ok(conflicting.error,'conflicting idempotency key was accepted')
const reconciled=await server.rpc('video_qa_reconcile',{p_owner:ownerId,p_path:publishPath})
assert.ifError(reconciled.error)
assert.equal(reconciled.data,first.data)
const viewerPosts=await viewer.from('posts').select('id').eq('video_path',publishPath)
assert.ifError(viewerPosts.error)
assert.equal(viewerPosts.data.length,0,'viewer read private owner post via RLS')
const enqueue=await server.from('video_cleanup_queue').insert({owner_id:ownerId,object_path:publishPath})
assert.ifError(enqueue.error)
const workerId=randomUUID()
const claim=await server.rpc('video_qa_claim_cleanup',{p_worker:workerId,p_lease_seconds:60})
assert.ifError(claim.error)
assert.equal(claim.data.length,1)
const otherClaim=await server.rpc('video_qa_claim_cleanup',{p_worker:randomUUID(),p_lease_seconds:60})
assert.ifError(otherClaim.error)
assert.equal(otherClaim.data.length,0,'cleanup job claimed twice')
const wrongFinish=await server.rpc('video_qa_finish_cleanup',{p_id:claim.data[0].id,p_worker:randomUUID(),p_success:true,p_reason:'wrong worker'})
assert.ifError(wrongFinish.error)
assert.equal(wrongFinish.data,false)
const retry=await server.rpc('video_qa_finish_cleanup',{p_id:claim.data[0].id,p_worker:workerId,p_success:false,p_reason:'post committed: retain'})
assert.ifError(retry.error)
assert.equal(retry.data,true)
const workerPath=`${ownerId}/${randomUUID()}.mp4`
assert.ifError((await server.rpc('video_qa_publish',{p_owner:ownerId,p_path:workerPath,p_content:'retained by cleanup worker'})).error)
assert.ifError((await server.from('video_cleanup_queue').insert({owner_id:ownerId,object_path:workerPath})).error)
const { spawnSync } = await import('node:child_process')
const worker = spawnSync('python3',['-m','tests.video.isolated_cleanup_worker_e2e'],{
 env:{...process.env,VIDEO_QA_ENV:process.env.VIDEO_QA_ENV},
 encoding:'utf8'
})
assert.equal(worker.status,0,worker.stderr)
assert.match(worker.stdout,/PASS: isolated durable cleanup worker retained posted object/)

assert.ifError((await owner.storage.from(bucket).remove([publishPath])).error)
console.log('PASS: isolated PostgREST publish idempotency, reconciliation, RLS, cleanup lease/fencing/retry')

console.log('PASS: isolated Supabase Storage HTTP owner upload/read, viewer upload/read/sign/delete deny, signed URL, 20MiB rejection, delete invalidates URL, simulated rollback')
