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
const removed=await owner.storage.from(bucket).remove([path])
assert.ifError(removed.error)
const gone=await owner.storage.from(bucket).download(path)
assert.ok(gone.error,'deleted object still available')
const orphan=`${ownerId}/${randomUUID()}.mp4`
assert.ifError((await owner.storage.from(bucket).upload(orphan,bytes,{contentType:'video/mp4'})).error)
// Simulated failed publication; cleanup is a test harness, not production behavior.
const failedPublish=true
if(failedPublish) assert.ifError((await owner.storage.from(bucket).remove([orphan])).error)
assert.ok((await owner.storage.from(bucket).download(orphan)).error)
console.log('PASS: isolated Supabase Storage HTTP owner upload/read, viewer deny, signed URL, 20MiB rejection, delete, simulated rollback')
