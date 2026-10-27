// Disposable local DB proof helpers. Never export credentials/claims to logs.
import assert from 'node:assert/strict'
import {spawn} from 'node:child_process'
import {createHash} from 'node:crypto'
import {signBinaryVideoAttestation,videoAttestationDigest} from '../../server/video-attestation.js'

export function createRecoveryMultitabFixture({owner,uid,url,path,bytes,sql,dbUrl,transformPublication}) {
 assert.equal(url,'http://127.0.0.1:56321')
 assert.match(dbUrl,/127\.0\.0\.1:56322\//)
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
    let args=JSON.parse(body)
    if(args.p_path!==path)return realFetch(input,init)
    if(transformPublication){args=transformPublication(args,new Headers(init?.headers));init={...init,body:JSON.stringify(args)}}
    const item={args,completed:false,issuedAt:Math.floor(Date.now()/1000)};claims.push(item)
    const response=await realFetch(input,init)
    const result=await response.clone().json()
    item.ok=response.ok;item.id=typeof result==='string'?result:null;item.error=result?.message??'';item.completed=true
    return response
   }
  },
  async acquireLock({storage=false}={}) {
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
    const row=storage?`storage.objects where bucket_id='post-videos' and name='${path}'`:`public.video_reserved_object_keys where bucket_id='post-videos' and object_path='${path}'`
    lock.stdin.write(`begin; select 1 from ${row} for update; select 'MULTITAB_LOCKED';\n`)
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
  async ageReservation(seconds=2) {
   assert.ok(seconds>0&&seconds<=10)
   const before=JSON.parse(snapshot())
   sql(`update public.video_reserved_object_keys set created_at=clock_timestamp()-interval '1 hour'+make_interval(secs=>${seconds}) where bucket_id='post-videos' and object_path='${path}';`)
   const after=JSON.parse(snapshot())
   assert.deepEqual({...after.reservation,created_at:before.reservation.created_at},before.reservation,'only the disposable reservation age may change')
   assert.deepEqual({...after,reservation:before.reservation},before,'reservation age control preserves manifest/Storage and counts')
   assert.ok(Date.parse(after.manifest.expires_at)>Date.now()+60000,'manifest must remain independently unexpired')
   baseline=snapshot()
   assert.equal((await state()).active,true,'aged reservation is still active before the real wait')
  },
  async waitReservationExpiry() {
   for(let n=0;n<200;n++) {
    if(sql(`select (created_at+interval '1 hour'<=clock_timestamp())::text from public.video_reserved_object_keys where object_path='${path}';`)==='true')return
    await new Promise(resolve=>setTimeout(resolve,20))
   }
   throw Error('reservation one-hour deadline did not expire on the real DB clock')
  },
  async waitClaimExpiry(index) {
   assert.ok(claims[index])
   for(let n=0;n<200;n++) {
    if(sql(`select (${claims[index].args.p_expires_at}::numeric <= extract(epoch from clock_timestamp()))::text;`)==='true')return
    await new Promise(resolve=>setTimeout(resolve,20))
   }
   throw Error('trusted attestation did not expire on the real server clock')
  },
  rejectionMessages(){return claims.filter(item=>item.completed&&!item.ok).map(item=>item.error)},
  assertRejected(index,pattern) {assert.equal(claims[index]?.ok,false);assert.match(claims[index].error,pattern)},
  async expireManifestWhileBlocked() {
   const before=JSON.parse(snapshot())
   sql(`update video_private.recovery_manifests set expires_at=clock_timestamp()+interval '250 milliseconds' where object_path='${path}';`)
   const after=JSON.parse(snapshot())
   assert.deepEqual({...after.manifest,expires_at:before.manifest.expires_at},before.manifest,'only the controlled manifest deadline may change')
   assert.deepEqual({...after,manifest:before.manifest},before,'deadline fixture must preserve every other invariant')
   baseline=snapshot();initial.expires=(await state()).expires
   for(let n=0;n<100;n++) {
    if(sql(`select (expires_at<=clock_timestamp())::text from video_private.recovery_manifests where object_path='${path}';`)==='true')return
    await new Promise(resolve=>setTimeout(resolve,20))
   }
   throw Error('manifest deadline did not cross on real server clock')
  },
  async audit(expectedPosts,expectedClaims,{rejected=[],active=true}={}) {
   assert.equal(snapshot(),baseline,'reservation, manifest, Storage generation/metadata and owner counts must remain unchanged')
   const current=await state()
   assert.equal(current.owner,uid);assert.equal(current.sha256,createHash('sha256').update(bytes).digest('hex'))
   assert.equal(current.generation,initial.generation);assert.equal(current.expires,initial.expires);assert.equal(current.active,active)
   const posts=await owner.from('posts').select('id,user_id,video_path,video_generation,video_sha256,video_duration_seconds,content').eq('video_path',path)
   assert.ifError(posts.error);assert.equal(posts.data.length,expectedPosts)
   assert.equal(claims.length,expectedClaims,'exact number of signed publication attempts')
   const completed=claims.filter(c=>c.completed)
   const consumed=JSON.parse(sql(`select coalesce(jsonb_agg(jsonb_build_object('nonce',encode(nonce,'hex'),'owner',owner_id,'path',object_path)),'[]'::jsonb)::text from video_private.consumed_nonces where object_path='${path}';`))
   assert.equal(consumed.length,completed.filter(c=>c.ok).length,'only successful retries consume fresh nonces atomically')
   assert.equal(new Set(claims.map(c=>c.args.p_nonce)).size,claims.length,'no signed nonce reuse across tabs/retries')
   for(const [index,item] of claims.entries()) {
    const a=item.args
    assert.equal(a.p_owner,uid);assert.equal(a.p_path,path);assert.equal(a.p_generation,initial.generation)
    assert.equal(a.p_sha256,current.sha256);assert.equal(a.p_content,initial.content);assert.equal(a.p_duration_ms,2000)
    assert.ok(a.p_expires_at>item.issuedAt&&a.p_expires_at<=item.issuedAt+300)
    const signed=signBinaryVideoAttestation(Buffer.from('41'.repeat(32),'hex'),{owner:uid,path,generation:initial.generation,sha256:current.sha256,durationMs:2000,contentSha256:videoAttestationDigest(initial.content),expiresAt:a.p_expires_at,nonce:a.p_nonce})
    assert.equal(signed===a.p_signature,true,'server proof must cover the exact immutable claims')
    if(item.completed){
     if(rejected.includes(index)){assert.equal(item.ok,false);assert.equal(consumed.some(n=>n.nonce===a.p_nonce),false,'rejected proof must leave no nonce')}
     else{assert.equal(item.ok,true);assert.equal(item.id,posts.data[0]?.id);assert.equal(consumed.filter(n=>n.nonce===a.p_nonce&&n.owner===uid&&n.path===path).length,1)}
    }
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
