// Disposable local DB proof helpers. Never export credentials/claims to logs.
import assert from 'node:assert/strict'
import {spawn} from 'node:child_process'
import {createHash} from 'node:crypto'
import {signBinaryVideoAttestation,videoAttestationDigest} from '../../server/video-attestation.js'

export function createRecoveryMultitabFixture({owner,uid,url,path,bytes,sql,dbUrl}) {
 const claims=[]
 const realFetch=globalThis.fetch
 let baseline,initial,lock,lockExit,lockTimer,stopped=false
 const snapshot=()=>sql(`select jsonb_build_object(
 'reservation',(select to_jsonb(r) from public.video_reserved_object_keys r where object_path='${path}'),
 'manifest',(select to_jsonb(m) from video_private.recovery_manifests m where object_path='${path}'),
 'object',(select to_jsonb(o)-'last_accessed_at' from storage.objects o where bucket_id='post-videos' and name='${path}'),
 'reservations',(select count(*) from public.video_reserved_object_keys where owner_id='${uid}'),
 'objects',(select count(*) from storage.objects where bucket_id='post-videos' and owner_id='${uid}'))::text;`)
 const state=async()=>{const r=await owner.rpc('video_recovery_state_v1',{p_path:path});assert.ifError(r.error);return r.data}
 return {
  path,
  async prepare() {
   initial=await state();baseline=snapshot()
   assert.ok(Number(sql("select count(*) from pg_index where indrelid='public.posts'::regclass and indisunique and indisvalid and pg_get_indexdef(indexrelid) like '%(video_path)%';"))>=1,'real unique video_path index is required')
   assert.equal(initial.post_id,null);assert.equal(initial.active,true)
   globalThis.fetch=async(input,init)=>{
    const address=typeof input==='string'?input:input instanceof URL?input.href:input.url
    if(address!==url+'/rest/v1/rpc/video_publish_recovered_attested_v1')return realFetch(input,init)
    const body=init?.body??(input instanceof Request?await input.clone().text():undefined)
    const args=JSON.parse(body)
    if(args.p_path!==path)return realFetch(input,init)
    const item={args,completed:false};claims.push(item)
    const response=await realFetch(input,init)
    const result=await response.clone().json()
    item.ok=response.ok;item.id=typeof result==='string'?result:null;item.completed=true
    return response
   }
  },
  async acquireLock() {
   assert.equal(Boolean(lock),false)
   lock=spawn('psql',[dbUrl,'-v','ON_ERROR_STOP=1','-qAt'],{stdio:['pipe','pipe','pipe']})
   lockExit=new Promise(resolve=>lock.once('close',resolve))
   // A failed test must not leave a connection/row lock behind.
   lockTimer=setTimeout(()=>lock?.kill(),25000)
   await new Promise((resolve,reject)=>{
    let output=''
    const timer=setTimeout(()=>reject(Error('isolated reservation lock acquisition timeout')),10000)
    lock.stdout.on('data',data=>{output+=data.toString();if(output.includes('MULTITAB_LOCKED')){clearTimeout(timer);resolve()}})
    lock.once('error',()=>{clearTimeout(timer);reject(Error('isolated reservation lock unavailable'))})
    lock.once('close',()=>{clearTimeout(timer);reject(Error('isolated reservation lock ended early'))})
    lock.stdin.write(`begin; select 1 from public.video_reserved_object_keys where bucket_id='post-videos' and object_path='${path}' for update; select 'MULTITAB_LOCKED';\n`)
   })
  },
  async waitBlocked(expected) {
   const started=claims.length
   for(let n=0;n<200;n++) {
    const waiting=Number(sql("select count(*) from pg_stat_activity where wait_event_type='Lock' and query like '%video_publish_recovered_attested_v1%';"))
    if(waiting>=expected&&claims.filter(c=>!c.completed).length===expected){assert.ok(started>=expected||claims.length>=expected);return}
    await new Promise(resolve=>setTimeout(resolve,30))
   }
   throw Error('both real publication RPCs did not wait on the reservation row lock')
  },
  async releaseLock() {
   if(!lock)return
   clearTimeout(lockTimer)
   lock.stdin.end('commit;\n\\q\n')
   assert.equal(await lockExit,0,'isolated lock transaction commits cleanly')
   lock=null
  },
  async audit(expectedPosts,expectedClaims) {
   assert.equal(snapshot(),baseline,'reservation, manifest, Storage generation/metadata and owner counts must remain unchanged')
   const current=await state()
   assert.equal(current.owner,uid);assert.equal(current.sha256,createHash('sha256').update(bytes).digest('hex'))
   assert.equal(current.generation,initial.generation);assert.equal(current.expires,initial.expires);assert.equal(current.active,true)
   const posts=await owner.from('posts').select('id,user_id,video_path,video_generation,video_sha256,video_duration_seconds,content').eq('video_path',path)
   assert.ifError(posts.error);assert.equal(posts.data.length,expectedPosts)
   assert.equal(claims.length,expectedClaims,'exact number of signed publication attempts')
   const completed=claims.filter(c=>c.completed)
   const consumed=JSON.parse(sql(`select coalesce(jsonb_agg(jsonb_build_object('nonce',encode(nonce,'hex'),'owner',owner_id,'path',object_path)),'[]'::jsonb)::text from video_private.consumed_nonces where object_path='${path}';`))
   assert.equal(consumed.length,completed.length,'each successful retry consumes a fresh nonce, atomically')
   assert.equal(new Set(claims.map(c=>c.args.p_nonce)).size,claims.length,'no signed nonce reuse across tabs/retries')
   for(const item of claims) {
    const a=item.args
    assert.equal(a.p_owner,uid);assert.equal(a.p_path,path);assert.equal(a.p_generation,initial.generation)
    assert.equal(a.p_sha256,current.sha256);assert.equal(a.p_content,initial.content);assert.equal(a.p_duration_ms,2000)
    assert.ok(a.p_expires_at>Math.floor(Date.now()/1000)&&a.p_expires_at<=Math.floor(Date.now()/1000)+300)
    const signed=signBinaryVideoAttestation(Buffer.from('41'.repeat(32),'hex'),{owner:uid,path,generation:initial.generation,sha256:current.sha256,durationMs:2000,contentSha256:videoAttestationDigest(initial.content),expiresAt:a.p_expires_at,nonce:a.p_nonce})
    assert.equal(signed===a.p_signature,true,'server proof must cover the exact immutable claims')
    if(item.completed){assert.equal(item.ok,true);assert.equal(item.id,posts.data[0]?.id);assert.equal(consumed.filter(n=>n.nonce===a.p_nonce&&n.owner===uid&&n.path===path).length,1)}
   }
   if(expectedPosts) {
    const p=posts.data[0]
    assert.equal(p.user_id,uid);assert.equal(p.video_generation,initial.generation);assert.equal(p.video_sha256,current.sha256)
    assert.equal(p.content,initial.content);assert.equal(p.video_duration_seconds,2);assert.equal(p.id,current.post_id)
   }
   const download=await owner.storage.from('post-videos').download(path);assert.ifError(download.error)
   assert.equal(createHash('sha256').update(Buffer.from(await download.data.arrayBuffer())).digest('hex'),current.sha256)
   return posts.data[0]?.id
  },
  async stop() {
   if(stopped)return;stopped=true
   globalThis.fetch=realFetch
   clearTimeout(lockTimer)
   if(lock){lock.kill();await lockExit;lock=null}
  },
 }
}
