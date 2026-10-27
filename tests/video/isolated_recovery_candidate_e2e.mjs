// Candidate inspection uses only owner JWT. Fixture SQL/signing keys below are
// disposable CI-only setup, never read from or applied to a production project.
import assert from 'node:assert/strict'
import {createClient} from '@supabase/supabase-js'
import {createHash,randomUUID} from 'node:crypto'
import {readFileSync,mkdtempSync,rmSync} from 'node:fs'
import {execFileSync,spawn} from 'node:child_process'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
import {createServer} from 'node:http'
import {verifyRealBrowserPlayback} from './isolated_browser_playback.mjs'
import {createVideoFinalizeHandler} from '../../api/video-finalize.ts'
import {signBinaryVideoAttestation,videoAttestationDigest} from '../../server/video-attestation.js'
const env=Object.fromEntries(readFileSync(process.env.VIDEO_QA_ENV,'utf8').split('\n').filter(x=>x.includes('=')).map(x=>{const n=x.indexOf('=');return[x.slice(0,n),x.slice(n+1).replace(/^["']|["']$/g,'')]}))
assert.equal(env.API_URL,'http://127.0.0.1:56321')
assert.match(env.DB_URL,/127\.0\.0\.1:56322\//)
const url=env.API_URL,anon=env.ANON_KEY||env.PUBLISHABLE_KEY
const client=()=>createClient(url,anon,{auth:{persistSession:false,autoRefreshToken:false}})
const owner=client(),foreign=client(),guest=client()
for(const c of [owner,foreign]) assert.ifError((await c.auth.signUp({email:`recovery-${randomUUID()}@example.invalid`,password:'Local-Recovery-Fixture-Password1!'})).error)
const uid=(await owner.auth.getUser()).data.user.id,jwt=(await owner.auth.getSession()).data.session.access_token
const foreignJwt=(await foreign.auth.getSession()).data.session.access_token
process.env.VITE_SUPABASE_URL=url;process.env.VITE_SUPABASE_ANON_KEY=anon
process.env.VIDEO_RECOVERY_ISOLATED_KEY_HEX='41'.repeat(32)
const handler=createVideoFinalizeHandler(undefined,{isolatedLocalOnly:true})
const server=createServer((req,res)=>{void(async()=>{
 const chunks=[];let size=0
 for await(const chunk of req){size+=chunk.length;if(size>12288){res.writeHead(413);res.end();return}chunks.push(chunk)}
 const raw=Buffer.concat(chunks);let body
 try{body=JSON.parse(raw.toString())}catch{res.writeHead(400);res.end();return}
 const reply={setHeader:(n,v)=>{res.setHeader(n,v);return reply},status:n=>{res.statusCode=n;return reply},json:v=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(v));return reply},end:()=>res.end()}
 await handler({method:req.method,headers:req.headers,body},reply)
})().catch(()=>{if(!res.headersSent)res.statusCode=503;res.end()})})
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve))
const endpoint='http://127.0.0.1:'+server.address().port
const call=(body,token=jwt)=>fetch(endpoint,{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify(body)})
const status=path=>call({action:'recovery_status',object_path:path})
const hash=bytes=>createHash('sha256').update(bytes).digest('hex')
const sql=text=>{try{return execFileSync('psql',[env.DB_URL,'-v','ON_ERROR_STOP=1','-qAt'],{input:text,encoding:'utf8',stdio:['pipe','pipe','pipe']}).trim()}catch{throw Error('isolated recovery SQL fixture failed; raw connection diagnostics withheld')}}
const dir=mkdtempSync(join(tmpdir(),'recovery-fixture-'))
try {
 const file=join(dir,'clip.webm')
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=black:s=64x64:r=10','-t','2','-c:v','libvpx','-b:v','150k','-y',file],{timeout:30000})
 const bytes=readFileSync(file)
 const reserve=async()=>{const path=uid+'/'+randomUUID()+'.webm';assert.ifError((await owner.rpc('video_reserve_object_key',{p_owner:uid,p_path:path})).error);return path}
 const bind=(path,sha=hash(bytes),size=bytes.length,content='recovery race fixture')=>call({action:'bind_recovery',object_path:path,sha256:sha,size,type:'video/webm',content})
 const upload=async(path,data=bytes)=>{assert.ifError((await owner.storage.from('post-videos').upload(path,data,{contentType:'video/webm',upsert:false})).error)}
 const path=await reserve()
 assert.equal((await bind(path)).status,200)
 const duplicate=await Promise.all([bind(path),bind(path)])
 assert.ok(duplicate.every(r=>r.status===200),'identical concurrent binding is idempotent')
 const conflict=await Promise.all([bind(path,'b'.repeat(64)),bind(path)])
 assert.deepEqual(conflict.map(r=>r.status),[409,200],'conflicting claims never overwrite manifest')
 const waiting=await status(path);assert.equal(waiting.status,200);assert.equal((await waiting.json()).state,'waiting_for_upload')
 assert.equal((await call({action:'recovery_status',object_path:path},foreignJwt)).status,403)
 assert.ok((await foreign.rpc('video_recovery_state_v1',{p_path:path})).error)
 assert.ok((await guest.rpc('video_recovery_state_v1',{p_path:path})).error)
 assert.ok((await owner.schema('video_private').from('recovery_manifests').select('*')).error,'private manifest inaccessible')
 assert.equal((await call({action:'recovery_status',object_path:path},'invalid.jwt.token')).status,409)
 await upload(path)
 assert.ok((await owner.storage.from('post-videos').update(path,bytes,{contentType:'video/webm'})).error,'RLS forbids overwrite')
 let result=await status(path);assert.equal(result.status,200)
 const ready=await result.json();assert.equal(ready.state,'verified_ready');assert.equal(ready.ffprobe_verified,true);assert.equal(ready.sha256,hash(bytes));assert.equal(ready.allow_resume,false)
 assert.equal((await status(path)).status,200,'inspection is read-only and repeatable')
 const foreignWrite=await foreign.rpc('video_bind_recovery_manifest_v1',{p_path:path,p_sha256:hash(bytes),p_size:bytes.length,p_type:'video/webm'});assert.ok(foreignWrite.error)
 const tampered=await reserve();assert.equal((await bind(tampered,'c'.repeat(64))).status,200);await upload(tampered)
 assert.equal((await status(tampered)).status,409,'downloaded bytes must match original commitment')
 const corrupt=await reserve();const bad=Buffer.from([0,1,2,3]);assert.equal((await bind(corrupt,hash(bad),bad.length)).status,200);await upload(corrupt,bad)
 assert.equal((await status(corrupt)).status,409,'matching hash cannot replace ffprobe validation')
 const expired=await reserve();assert.equal((await bind(expired)).status,200)
 sql(`update video_private.recovery_manifests set expires_at=clock_timestamp()-interval '1 second' where object_path='${expired}';`)
 assert.equal((await status(expired)).status,410,'server clock expiry stops recovery')
 const late=await reserve();await upload(late);assert.equal((await bind(late)).status,409,'cannot invent original identity after upload')
 // Race an independently verified attested publication against a real bounded
 // Storage read. The first inspection must reject its changed snapshot.
 let release,reached,held=false
 const reachedPromise=new Promise(resolve=>{reached=resolve}),originalFetch=globalThis.fetch
 globalThis.fetch=async(input,init)=>{
  const response=await originalFetch(input,init)
  if(String(input)===url+'/storage/v1/object/authenticated/post-videos/'+path && !held){held=true;reached();await new Promise(resolve=>{release=resolve})}
  return response
 }
 try {
  const race=status(path);await reachedPromise
  const published=await call({action:'recovery_finalize',object_path:path,content:'recovery race fixture'})
  assert.equal(published.status,200,'actual recovered-finalize API must commit via attested recovery RPC')
  release();assert.equal((await race).status,409,'concurrent publish invalidates inspection snapshot')
 } finally {release?.();globalThis.fetch=originalFetch}
 result=await status(path);assert.equal(result.status,200);assert.equal((await result.json()).state,'published')
 assert.equal((await call({action:'recovery_finalize',object_path:path,content:'recovery race fixture'})).status,200,'same HTTP recovery is idempotent')
 assert.equal((await call({action:'recovery_finalize',object_path:path,content:'changed content'})).status,409,'changed retry content cannot reconcile to an old post')
 const posts=await owner.from('posts').select('id').eq('video_path',path);assert.ifError(posts.error);assert.equal(posts.data.length,1)
 // Reusing the original signed nonce must fail even through the recovery wrapper.
 const {data:currentGeneration}=await owner.rpc('video_production_storage_generation',{p_owner:uid,p_path:path})
 const recoveryClaims={p_owner:uid,p_path:path,p_generation:currentGeneration,p_sha256:hash(bytes),p_duration_ms:2000,p_content:'recovery race fixture',p_expires_at:Math.floor(Date.now()/1000)+120,p_nonce:randomUUID().replaceAll('-',''),p_key_id:1}
 recoveryClaims.p_signature=signBinaryVideoAttestation(Buffer.from('41'.repeat(32),'hex'),{owner:uid,path,generation:currentGeneration,sha256:hash(bytes),durationMs:2000,contentSha256:videoAttestationDigest(recoveryClaims.p_content),expiresAt:recoveryClaims.p_expires_at,nonce:recoveryClaims.p_nonce})
 assert.ifError((await owner.rpc('video_publish_recovered_attested_v1',recoveryClaims)).error)
 assert.ok((await owner.rpc('video_publish_recovered_attested_v1',recoveryClaims)).error,'nonce replay rejected by atomic recovery wrapper')
 assert.ok((await foreign.rpc('video_publish_recovered_attested_v1',recoveryClaims)).error,'foreign identity cannot reuse signed owner proof')
 sql(`update video_private.recovery_manifests set expires_at=clock_timestamp()-interval '1 second' where object_path='${path}';`)
 const newNonce=randomUUID().replaceAll('-','')
 recoveryClaims.p_nonce=newNonce
 recoveryClaims.p_signature=signBinaryVideoAttestation(Buffer.from('41'.repeat(32),'hex'),{owner:uid,path,generation:currentGeneration,sha256:hash(bytes),durationMs:2000,contentSha256:videoAttestationDigest(recoveryClaims.p_content),expiresAt:recoveryClaims.p_expires_at,nonce:newNonce})
 assert.ok((await owner.rpc('video_publish_recovered_attested_v1',recoveryClaims)).error,'expiry after successful status rejects publication in DB transaction')
 assert.equal(sql(`select count(*) from video_private.consumed_nonces where nonce=decode('${newNonce}','hex');`),'0','rejected recovery must not consume nonce')
 assert.equal((await owner.from('posts').select('id').eq('video_path',path)).data.length,1)
 assert.equal(sql(`select count(*) from video_private.recovery_manifests where object_path='${path}';`),'1')
 // Hold Storage's row past the recovery deadline. Parent publication can
 // only proceed after the lock releases; the wrapper's final clock check
 // must roll back BOTH its post and newly consumed nonce.
 const delayed=await reserve();assert.equal((await bind(delayed,hash(bytes),bytes.length,'late lock fixture')).status,200);await upload(delayed)
 const {data:delayedGeneration}=await owner.rpc('video_production_storage_generation',{p_owner:uid,p_path:delayed})
 const delayedNonce=randomUUID().replaceAll('-',''),delayedExpiry=Math.floor(Date.now()/1000)+120
 const delayedClaims={p_owner:uid,p_path:delayed,p_generation:delayedGeneration,p_sha256:hash(bytes),p_duration_ms:2000,p_content:'late lock fixture',p_expires_at:delayedExpiry,p_nonce:delayedNonce,p_key_id:1}
 delayedClaims.p_signature=signBinaryVideoAttestation(Buffer.from('41'.repeat(32),'hex'),{owner:uid,path:delayed,generation:delayedGeneration,sha256:hash(bytes),durationMs:2000,contentSha256:videoAttestationDigest(delayedClaims.p_content),expiresAt:delayedExpiry,nonce:delayedNonce})
 sql(`update video_private.recovery_manifests set expires_at=clock_timestamp()+interval '2 seconds' where object_path='${delayed}';`)
 const locker=spawn('psql',[env.DB_URL,'-v','ON_ERROR_STOP=1','-qAt'],{stdio:['pipe','pipe','pipe']})
 let lockOutput=''
 const readyLock=new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{locker.kill();reject(Error('isolated row-lock fixture timeout'))},15000)
  locker.stdout.on('data',data=>{lockOutput+=data.toString();if(lockOutput.includes('LOCKED')){clearTimeout(timer);resolve()}})
  locker.on('error',()=>{clearTimeout(timer);reject(Error('isolated row-lock fixture unavailable'))})
  locker.on('close',code=>{clearTimeout(timer);if(code!==0)reject(Error('isolated row-lock fixture failed; raw connection diagnostics withheld'))})
 })
 locker.stdin.end(`begin; select 1 from storage.objects where bucket_id='post-videos' and name='${delayed}' for update; select 'LOCKED'; select pg_sleep(3); commit;`)
 await readyLock
 const delayedResult=await owner.rpc('video_publish_recovered_attested_v1',delayedClaims)
 assert.ok(delayedResult.error)
 assert.match(delayedResult.error.message,/recovery expired during publication/,'deadline must be rechecked after the blocking parent call')
 assert.equal(sql(`select count(*) from video_private.consumed_nonces where nonce=decode('${delayedNonce}','hex');`),'0')
 assert.equal((await owner.from('posts').select('id').eq('video_path',delayed)).data.length,0)
 await verifyRealBrowserPlayback({postId:posts.data[0].id,jwt,deniedJwt:foreignJwt,anon,service:env.SERVICE_ROLE_KEY||env.SECRET_KEY,bytes,recoveryOnly:true,recoveryFixtures:{legacyPath:late,expire:path=>sql(`update video_private.recovery_manifests set expires_at=clock_timestamp()-interval '1 second' where object_path='${path}';`)}})
 console.log('PASS: recovery atomic publication rejects nonce replay/foreign owner and rolls back post+nonce after expiry during real Storage row-lock wait')
 console.log('PASS: real recovery candidate JWT/auth.uid owner, private manifest RLS, immutable concurrent bind, server expiry, SHA256/ffprobe, missing/late object, overwrite rejection, published state and concurrent publication race')
} finally {await new Promise(resolve=>server.close(resolve));rmSync(dir,{recursive:true,force:true})}
