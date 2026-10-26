// Disposable local Supabase only: authenticated PostgREST attacks and valid
// Node-signed attested publication. Never point this at a remote endpoint.
import assert from 'node:assert/strict'
import { createClient } from '@supabase/supabase-js'
import { createHash, randomUUID } from 'node:crypto'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { signBinaryVideoAttestation, videoAttestationDigest } from '../../api/video-attestation.ts'
const env=Object.fromEntries(readFileSync(process.env.VIDEO_QA_ENV,'utf8').split('\n')
 .filter(x=>x.includes('=')).map(x=>{const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1).replace(/^["']|["']$/g,'')]}))
assert.equal(env.API_URL,'http://127.0.0.1:56321','refuse remote Supabase')
const url=env.API_URL, anon=env.ANON_KEY||env.PUBLISHABLE_KEY
const ownerClient=createClient(url,anon,{auth:{persistSession:false,autoRefreshToken:false}})
const attacker=createClient(url,anon,{auth:{persistSession:false,autoRefreshToken:false}})
for(const [client,label] of [[ownerClient,'owner'],[attacker,'attacker']]) {
 const {error}=await client.auth.signUp({email:`attested-${label}-${randomUUID()}@example.invalid`,password:'Local-Video-Fixture-Password1!'})
 assert.ifError(error)
}
const owner=(await ownerClient.auth.getUser()).data.user.id
const path=`${owner}/${randomUUID()}.webm`
const dir=mkdtempSync(join(tmpdir(),'attested-real-http-'))
let bytes
try {
 const file=join(dir,'video.webm')
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-f','lavfi','-i',
  'color=c=black:s=64x64:r=10','-t','2','-c:v','libvpx','-b:v','150k',
  '-pix_fmt','yuv420p','-y',file],{timeout:30000})
 bytes=readFileSync(file)
} finally {rmSync(dir,{recursive:true,force:true})}
assert.ok(bytes.length>0 && bytes.length<20*1024*1024)
assert.ifError((await ownerClient.rpc('video_reserve_object_key',{p_owner:owner,p_path:path})).error)
assert.ifError((await ownerClient.storage.from('post-videos').upload(path,bytes,{contentType:'video/webm',upsert:false})).error)
const {data:gen,error:genError}=await ownerClient.rpc('video_production_storage_generation',{p_owner:owner,p_path:path})
assert.ifError(genError)
assert.match(gen,/^[0-9a-f-]{36}$/)
const {data:privateRead,error:readError}=await ownerClient.storage.from('post-videos').download(path)
assert.ifError(readError)
assert.deepEqual(Buffer.from(await privateRead.arrayBuffer()),bytes)
assert.ok((await attacker.storage.from('post-videos').download(path)).error,'other user cannot read private Storage')
const sha256=createHash('sha256').update(bytes).digest('hex')
const content='isolated attested post', durationMs=2000
const expiresAt=Math.floor(Date.now()/1000)+120,nonce=randomUUID().replaceAll('-','')
const signature=signBinaryVideoAttestation(Buffer.alloc(32,0x41),{
 owner,path,generation:gen,sha256,durationMs,
 contentSha256:videoAttestationDigest(content),expiresAt,nonce,
})
const params={p_owner:owner,p_path:path,p_generation:gen,p_sha256:sha256,
 p_duration_ms:durationMs,p_content:content,p_expires_at:expiresAt,
 p_nonce:nonce,p_signature:signature,p_key_id:1}
assert.ok((await attacker.rpc('video_publish_attested_v1',params)).error,'foreign real JWT rejected')
assert.ok((await ownerClient.rpc('video_publish_attested_v1',{...params,p_signature:'0'.repeat(64)})).error,'forged signature rejected')
assert.ok((await ownerClient.rpc('video_publish_attested_v1',{...params,p_duration_ms:3000})).error,'duration tampering rejected')
assert.ok((await ownerClient.rpc('video_publish_attested_v1',{...params,p_generation:randomUUID()})).error,'Storage generation tampering rejected')
const {data:postId,error:publishError}=await ownerClient.rpc('video_publish_attested_v1',params)
assert.ifError(publishError)
assert.match(postId,/^[0-9a-f-]{36}$/)
assert.ok((await ownerClient.rpc('video_publish_attested_v1',params)).error,'nonce replay rejected')
const {data:posts,error:postsError}=await ownerClient.from('posts').select('id,video_path,video_generation,content').eq('video_path',path)
assert.ifError(postsError)
assert.equal(posts.length,1)
assert.equal(posts[0].id,postId)
assert.equal(posts[0].video_generation,gen)
assert.equal(posts[0].content,content)
console.log('PASS: real local JWT/PostgREST attested RPC rejects attacks, publishes once, and private Storage RLS holds')
