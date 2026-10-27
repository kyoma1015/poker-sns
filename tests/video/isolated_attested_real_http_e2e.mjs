// Disposable local Supabase only: authenticated PostgREST attacks and valid
// Node-signed attested publication. Never point this at a remote endpoint.
import assert from 'node:assert/strict'
import { createClient } from '@supabase/supabase-js'
import { createHash, randomUUID } from 'node:crypto'
import { createServer } from 'node:http'
import { createVideoFinalizeHandler } from '../../api/video-finalize.ts'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { signBinaryVideoAttestation, videoAttestationDigest } from '../../server/video-attestation.js'
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
// Exercise the actual Vercel reservation handler over HTTP, rather than
// bypassing its bearer-token, owner-path and request-size checks with SDK RPC.
process.env.VITE_SUPABASE_URL=url
process.env.VITE_SUPABASE_ANON_KEY=anon
const reservationHandler=createVideoFinalizeHandler(undefined,{isolatedLocalOnly:true})
const reservationServer=createServer((req,res)=>{
 void (async()=>{
  const chunks=[]
  for await(const chunk of req) chunks.push(chunk)
  const raw=Buffer.concat(chunks)
  let body
  try {body=JSON.parse(raw.toString('utf8'))} catch {res.writeHead(400);res.end();return}
  const response={
   setHeader:(name,value)=>{res.setHeader(name,value);return response},
   status:code=>{res.statusCode=code;return response},
   json:value=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(value));return response},
   end:()=>{res.end();return response},
  }
  await reservationHandler({method:req.method,headers:req.headers,body},response)
 })().catch(()=>{if(!res.headersSent)res.statusCode=503;if(!res.writableEnded)res.end()})
})
await new Promise(resolve=>reservationServer.listen(0,'127.0.0.1',resolve))
try {
 const address=reservationServer.address()
 assert.ok(address && typeof address!=='string')
 const endpoint='http://127.0.0.1:'+address.port
 const {data:{session},error:sessionError}=await ownerClient.auth.getSession()
 assert.ifError(sessionError)
 assert.ok(session?.access_token)
 const reserve=async(jwt,objectPath)=>fetch(endpoint,{
  method:'POST',headers:{Authorization:'Bearer '+jwt,'Content-Type':'application/json'},
  body:JSON.stringify({action:'reserve',object_path:objectPath}),
 })
 const foreignSession=(await attacker.auth.getSession()).data.session
 assert.ok(foreignSession?.access_token)
 // A valid owner JWT cannot reserve an object under another account's path.
 const foreignOwner=(await attacker.auth.getUser()).data.user.id
 assert.equal((await reserve(session.access_token,`${foreignOwner}/${randomUUID()}.webm`)).status,403,
  'owner JWT must not reserve another account Storage path')
 assert.equal((await reserve(foreignSession.access_token,path)).status,403,
  'foreign JWT must not reserve owner Storage key')
 assert.equal((await reserve('invalid.jwt.token',path)).status,401,
  'invalid bearer token must not reserve Storage key')
 const reserved=await reserve(session.access_token,path)
 assert.equal(reserved.status,201,'real HTTP owner reservation must succeed')
 assert.deepEqual(await reserved.json(),{reserved:true})
} finally {
 await new Promise((resolve,reject)=>reservationServer.close(error=>error?reject(error):resolve()))
}
console.log('PASS: actual HTTP JWT owner reservation, foreign-user and invalid-token denial')
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
const anonymous=createClient(url,anon,{auth:{persistSession:false,autoRefreshToken:false}})
assert.ok((await anonymous.rpc('video_publish_attested_v1',params)).error,
 'anonymous PostgREST role must not execute attested publication RPC')
assert.ok((await anonymous.storage.from('post-videos').download(path)).error,
 'anonymous viewer must not read owner private Storage')
for (const [client,label] of [[ownerClient,'owner'],[attacker,'attacker'],[anonymous,'anonymous']]) {
 for (const table of ['attestation_keys','consumed_nonces']) {
  const {error}=await client.schema('video_private').from(table).select('*').limit(1)
  assert.ok(error, `${label} must not query private ${table} via PostgREST`)
 }
}

assert.ok((await attacker.rpc('video_publish_attested_v1',params)).error,'foreign real JWT rejected')
assert.ok((await ownerClient.rpc('video_publish_attested_v1',{...params,p_signature:'0'.repeat(64)})).error,'forged signature rejected')
const mismatchedSignature=signBinaryVideoAttestation(Buffer.alloc(32,0x42),{
 owner,path,generation:gen,sha256,durationMs,
 contentSha256:videoAttestationDigest(content),expiresAt,nonce,
})
assert.ok((await ownerClient.rpc('video_publish_attested_v1',{
 ...params,p_signature:mismatchedSignature,
})).error,'real authenticated RPC must reject a correctly formatted HMAC signed with the wrong key')
assert.ok((await ownerClient.rpc('video_publish_attested_v1',{
 ...params,p_key_id:32767,
})).error,'real authenticated RPC must reject an unknown key ID')
// Exercise live PostgREST key rotation against a disposable database: the
// signature for key 1 must not authenticate under the independently provisioned
// key 2, even while that second key is active.
assert.ok((await ownerClient.rpc('video_publish_attested_v1',{
 ...params,p_key_id:2,
})).error,'real authenticated RPC must reject cross-key rotation signatures')

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
// Viewer RLS parity: a foreign user may download only while the linked post
// is visible to that same user. Staging and private posts remain inaccessible.
const qaAdmin=createClient(url,env.SERVICE_ROLE_KEY,{auth:{persistSession:false,autoRefreshToken:false}})
assert.ok((await attacker.storage.from('post-videos').download(path)).error,
 'private published post must not expose video bytes')
assert.ifError((await qaAdmin.from('posts').update({is_public:true}).eq('id',postId)).error)
const {data:visiblePost,error:visiblePostError}=await attacker.from('posts')
 .select('id,video_path').eq('id',postId).maybeSingle()
assert.ifError(visiblePostError)
assert.equal(visiblePost?.video_path,path,'foreign JWT should see public post')
const {data:visibleVideo,error:visibleVideoError}=await attacker.storage.from('post-videos').download(path)
assert.ifError(visibleVideoError)
assert.deepEqual(Buffer.from(await visibleVideo.arrayBuffer()),bytes,
 'foreign JWT must read RLS-visible published video')
assert.ifError((await qaAdmin.from('posts').update({is_public:false}).eq('id',postId)).error)
assert.ok((await attacker.storage.from('post-videos').download(path)).error,
 'revoking post visibility must revoke private Storage read')
console.log('PASS: foreign JWT published-video playback follows posts SELECT RLS; private and staging remain denied')
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
// Live key rotation: the independent active key 2 must successfully sign a
// NEW object, while key 1 signatures cannot be replayed under key ID 2.
const rotatedPath=`${owner}/${randomUUID()}.webm`
assert.ifError((await ownerClient.rpc('video_reserve_object_key',{
 p_owner:owner,p_path:rotatedPath})).error)
assert.ifError((await ownerClient.storage.from('post-videos').upload(rotatedPath,bytes,{
 contentType:'video/webm',upsert:false})).error)
const {data:rotatedGeneration,error:rotatedGenerationError}=await ownerClient.rpc(
 'video_production_storage_generation',{p_owner:owner,p_path:rotatedPath})
assert.ifError(rotatedGenerationError)
const rotatedContent='independent key 2 signed post'
const rotatedClaims={owner,path:rotatedPath,generation:rotatedGeneration,sha256,
 durationMs,contentSha256:videoAttestationDigest(rotatedContent),
 expiresAt:Math.floor(Date.now()/1000)+120,nonce:randomUUID().replaceAll('-','')}
const rotatedSignature=signBinaryVideoAttestation(Buffer.alloc(32,0x42),rotatedClaims)
const rotatedParams={p_owner:owner,p_path:rotatedPath,p_generation:rotatedGeneration,
 p_sha256:sha256,p_duration_ms:durationMs,p_content:rotatedContent,
 p_expires_at:rotatedClaims.expiresAt,p_nonce:rotatedClaims.nonce,
 p_signature:rotatedSignature,p_key_id:2}
assert.ok((await ownerClient.rpc('video_publish_attested_v1',{
 ...rotatedParams,p_key_id:1})).error,'rotated signature must fail under prior key')
const {data:rotatedPostId,error:rotatedPublishError}=await ownerClient.rpc(
 'video_publish_attested_v1',rotatedParams)
assert.ifError(rotatedPublishError)
assert.match(rotatedPostId,/^[0-9a-f-]{36}$/)
assert.ok((await ownerClient.rpc('video_publish_attested_v1',rotatedParams)).error,
 'rotated key nonce replay must fail')
assert.ok((await attacker.from('posts').select('id').eq('id',rotatedPostId)).data?.length===0,
 'rotated key publication must retain private RLS')
console.log('PASS: independently provisioned key 2 publishes through authenticated HTTP RPC; cross-key and nonce replay rejected')

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
