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
import { probeVideoBytes } from '../../api/video-ffprobe.ts'
import { verifyRealBrowserPlayback } from './isolated_browser_playback.mjs'
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
const inspected=await probeVideoBytes(bytes,'webm')
assert.equal(inspected.size,bytes.length)
const content='isolated attested post', durationMs=Math.round(inspected.duration*1000)
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
// A published private video must remain accessible to its owner and invisible
// to another authenticated account, even after the PostgREST publication.
const {data:publishedVideo,error:publishedVideoError}=await ownerClient.storage.from('post-videos').download(path)
assert.ifError(publishedVideoError)
assert.deepEqual(Buffer.from(await publishedVideo.arrayBuffer()),bytes)
assert.ok((await attacker.storage.from('post-videos').download(path)).error,'published video must remain private')
const {data:foreignPosts,error:foreignPostsError}=await attacker.from('posts')
 .select('id,video_path').eq('video_path',path)
assert.ifError(foreignPostsError)
assert.equal(foreignPosts.length,0,'foreign viewer must not discover private post')
// The actual React PostVideo and Timeline components now consume the post
// created by the signed RPC, rather than a separately fenced QA publication.
// Service-role credentials are confined to the disposable browser test harness;
// media retrieval itself uses the real viewer JWT and posts/Storage RLS.
const {data:ownerSession,error:ownerSessionError}=await ownerClient.auth.getSession()
const {data:attackerSession,error:attackerSessionError}=await attacker.auth.getSession()
assert.ifError(ownerSessionError)
assert.ifError(attackerSessionError)
assert.ok(ownerSession.session?.access_token && attackerSession.session?.access_token)
process.env.VITE_SUPABASE_URL=url
process.env.VITE_SUPABASE_ANON_KEY=anon
process.env.SUPABASE_SERVICE_ROLE_KEY=env.SERVICE_ROLE_KEY
process.env.VIDEO_PRODUCTION_FENCED_READY='true'
await verifyRealBrowserPlayback({postId,jwt:ownerSession.session.access_token,
 deniedJwt:attackerSession.session.access_token,anon,service:env.SERVICE_ROLE_KEY,
 bytes,expectedContent:content})
// Same signed-publication pipeline: an uploaded but unfinalized reserved object
// must be recoverable without deleting or publishing it. The Storage backend
// has no proven atomic generation-aware delete, so recovery is quarantine-only.
const orphanPath=`${owner}/${randomUUID()}.webm`
assert.ifError((await ownerClient.rpc('video_reserve_object_key',{
 p_owner:owner,p_path:orphanPath})).error)
assert.ifError((await ownerClient.storage.from('post-videos').upload(orphanPath,bytes,{
 contentType:'video/webm',upsert:false})).error)
const {data:orphanGeneration,error:orphanGenerationError}=await ownerClient.rpc(
 'video_production_storage_generation',{p_owner:owner,p_path:orphanPath})
assert.ifError(orphanGenerationError)
assert.match(orphanGeneration,/^[0-9a-f-]{36}$/)
const {data:orphanPosts,error:orphanPostsError}=await ownerClient.from('posts')
 .select('id').eq('video_path',orphanPath)
assert.ifError(orphanPostsError)
assert.equal(orphanPosts.length,0,'unfinalized upload must never appear in feed')
assert.ok((await attacker.storage.from('post-videos').download(orphanPath)).error,
 'orphan must remain private')
assert.ok((await ownerClient.storage.from('post-videos').upload(orphanPath,bytes,{
 contentType:'video/webm',upsert:true})).error,
 'recovery must not permit orphan overwrite')
// Supabase Storage DELETE can return HTTP success with an empty deleted-row
// list when RLS matches no rows. Do not equate an absent error with deletion.
const {data:deleteResult,error:deleteError}=await ownerClient.storage
 .from('post-videos').remove([orphanPath])
assert.ok(deleteError || (Array.isArray(deleteResult) && deleteResult.length===0),
 'unsafe client-side delete must not remove any object')
const {data:recoveredBytes,error:recoveredError}=await ownerClient.storage
 .from('post-videos').download(orphanPath)
assert.ifError(recoveredError)
assert.deepEqual(Buffer.from(await recoveredBytes.arrayBuffer()),bytes)
const {data:stillOrphan,error:stillOrphanError}=await ownerClient.from('posts')
 .select('id').eq('video_path',orphanPath)
assert.ifError(stillOrphanError)
assert.equal(stillOrphan.length,0)
console.log('PASS: attested-path orphan quarantined without publish, overwrite or unsafe delete; original bytes preserved')
console.log('PASS: attested real JWT/RPC/nonce + private Storage RLS + Chromium React playback')
