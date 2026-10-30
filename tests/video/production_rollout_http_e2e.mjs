// Disposable local stack only. No production credentials or QA mutation policies.
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {execFileSync} from 'node:child_process'
import {randomBytes,createHash,createHmac,randomUUID} from 'node:crypto'
import {createClient} from '@supabase/supabase-js'
import {signBinaryVideoAttestation,videoAttestationDigest} from '../../server/video-attestation.js'
const env=Object.fromEntries(readFileSync(process.env.VIDEO_QA_ENV,'utf8').split('\n').filter(x=>x.includes('=')).map(x=>{const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1).replace(/^["']|["']$/g,'')]}))
assert.equal(env.API_URL,'http://127.0.0.1:56321')
assert.ok(env.DB_URL.includes('127.0.0.1:56322'))
function sql(text){try{return execFileSync('psql',[env.DB_URL,'-X','-qAt','-v','ON_ERROR_STOP=1'],{input:text,stdio:['pipe','pipe','pipe']}).toString().trim()}catch{throw Error('production rollout isolated SQL failed; raw diagnostic withheld')}}
sql(`create table public.posts(id uuid primary key default gen_random_uuid(),user_id uuid not null,content text,post_type text,image_urls text[]); alter table public.posts enable row level security;
create policy normal_read on public.posts for select to authenticated using(true);
create policy normal_insert on public.posts for insert to authenticated with check(user_id=auth.uid());
create policy normal_update on public.posts for update to authenticated using(user_id=auth.uid()) with check(user_id=auth.uid());
create policy normal_delete on public.posts for delete to authenticated using(user_id=auth.uid());
grant select,insert,update,delete on public.posts to authenticated;
insert into public.posts(user_id,content,post_type,image_urls) values('99999999-9999-4999-8999-999999999999','preserved existing image fixture','normal',array['https://example.invalid/preserved.png']);`)
sql(readFileSync('sql/video_production_limited_rollout.sql','utf8'))
const signingKey=randomBytes(32)
sql("insert into video_private.attestation_keys(key_id,secret,active) values(7,decode('"+signingKey.toString('hex')+"','hex'),true); notify pgrst,'reload schema'")
await new Promise(r=>setTimeout(r,1500))
const key=env.ANON_KEY||env.PUBLISHABLE_KEY
const client=()=>createClient(env.API_URL,key,{auth:{persistSession:false,autoRefreshToken:false}})
const owner=client(),other=client(),anon=client()
for(const c of [owner,other])assert.ifError((await c.auth.signUp({email:randomUUID()+'@example.invalid',password:randomUUID()+'Aa1!'})).error)
const uid=(await owner.auth.getUser()).data.user.id
assert.match(uid,/^[0-9a-f-]{36}$/)
sql("insert into video_private.allowed_publishers values('"+uid+"',true)")
const path=uid+'/'+randomUUID()+'.mp4'
const reserve={p_owner:uid,p_path:path}
assert.ok((await owner.rpc('video_reserve_object_key',reserve)).error,'default off')
sql('update video_private.rollout_settings set enabled=true')
for(const c of [other,anon])assert.ok((await c.rpc('video_reserve_object_key',reserve)).error)
assert.ifError((await owner.rpc('video_reserve_object_key',reserve)).error)
assert.ok((await owner.rpc('video_reserve_object_key',reserve)).error,'reservation must not overwrite')
const bytes=execFileSync('ffmpeg',['-v','error','-f','lavfi','-i','color=c=black:s=32x32:d=1','-c:v','libx264','-movflags','frag_keyframe+empty_moov','-f','mp4','pipe:1'],{stdio:['ignore','pipe','pipe']})
const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-show_entries','format=duration','-of','json','-i','pipe:0'],{input:bytes,stdio:['pipe','pipe','pipe']}).toString())
const durationMs=Math.round(Number(probe.format.duration)*1000);assert.ok(durationMs>0&&durationMs<=30000)
assert.ifError((await owner.storage.from('post-videos').upload(path,bytes,{contentType:'video/mp4',upsert:false})).error)
assert.ok((await owner.storage.from('post-videos').upload(path,bytes,{contentType:'video/mp4',upsert:true})).error)
assert.ok((await owner.storage.from('post-videos').update(path,bytes,{contentType:'video/mp4'})).error)
const removed=await owner.storage.from('post-videos').remove([path]);assert.ok(removed.error||!removed.data?.length)
assert.ok((await other.storage.from('post-videos').download(path)).error)
const read=await owner.storage.from('post-videos').download(path);assert.ifError(read.error);assert.deepEqual(Buffer.from(await read.data.arrayBuffer()),bytes)
const generation=sql("select id from storage.objects where bucket_id='post-videos' and name='"+path+"'")
const content='production rollout isolated fixture'
const claims={owner:uid,path,generation,sha256:createHash('sha256').update(bytes).digest('hex'),durationMs,contentSha256:videoAttestationDigest(content),expiresAt:Math.floor(Date.now()/1000)+120,nonce:randomBytes(16).toString('hex')}
const params=c=>({p_owner:c.owner,p_path:c.path,p_generation:c.generation,p_sha256:c.sha256,p_duration_ms:c.durationMs,p_content:content,p_expires_at:c.expiresAt,p_nonce:c.nonce,p_signature:signBinaryVideoAttestation(signingKey,c),p_key_id:7})
assert.ok((await owner.from('posts').insert({user_id:uid,video_path:path})).error)
assert.ok((await other.rpc('video_publish_attested_v1',params(claims))).error)
assert.ok((await owner.rpc('video_publish_attested_v1',{...params(claims),p_content:'tamper'})).error)
const results=await Promise.all([owner.rpc('video_publish_attested_v1',params(claims)),owner.rpc('video_publish_attested_v1',params({...claims,nonce:randomBytes(16).toString('hex')}))])
for(const r of results)assert.ifError(r.error)
assert.equal(results[0].data,results[1].data)
assert.equal(sql('select count(*) from public.posts where video_path is not null'),'1')
assert.ok((await owner.rpc('video_publish_attested_v1',params(claims))).error)
assert.equal((await other.from('posts').select('id').not('video_path','is',null)).data.length,0)
assert.ok((await other.rpc('video_hide_own',{p_post_id:results[0].data})).error)
// Tampering the signature must be refused by real PostgREST/Storage authentication.
const bad=createClient(env.API_URL,key,{global:{headers:{Authorization:'Bearer invalid.invalid.invalid'}},auth:{persistSession:false,autoRefreshToken:false}})
assert.ok((await bad.rpc('video_rollout_allowed')).error)
assert.ok((await bad.storage.from('post-videos').download(path)).error)
assert.ok(env.JWT_SECRET,'local JWT signing fixture required')
const token=(await owner.auth.getSession()).data.session.access_token.split('.')
const expiredClaims={...JSON.parse(Buffer.from(token[1],'base64url').toString()),exp:Math.floor(Date.now()/1000)-60}
const unsigned=token[0]+'.'+Buffer.from(JSON.stringify(expiredClaims)).toString('base64url')
const expiredToken=unsigned+'.'+createHmac('sha256',env.JWT_SECRET).update(unsigned).digest('base64url')
const expired=createClient(env.API_URL,key,{global:{headers:{Authorization:'Bearer '+expiredToken}},auth:{persistSession:false,autoRefreshToken:false}})
assert.ok((await expired.rpc('video_rollout_allowed')).error)
assert.ok((await expired.storage.from('post-videos').download(path)).error)
sql('update video_private.rollout_settings set enabled=false')
assert.equal((await owner.rpc('video_rollout_allowed')).data,false)
assert.ifError((await owner.rpc('video_hide_own',{p_post_id:results[0].data})).error)
assert.equal((await owner.from('posts').select('id').not('video_path','is',null)).data.length,0)
assert.ok((await owner.storage.from('post-videos').download(path)).error)
assert.equal(sql('select count(*) from public.posts where video_path is not null'),'1')
assert.equal(sql("select count(*) from storage.objects where bucket_id='post-videos'"),'1')
assert.equal(sql("select count(*) from public.posts where content='preserved existing image fixture' and image_urls=array['https://example.invalid/preserved.png']"),'1')
signingKey.fill(0)
console.log('PASS: new production SQL real Auth/PostgREST/Storage, default-off, owner allowlist, direct video INSERT denial, immutable upload, actual ffprobe/SHA256/HMAC, concurrent one-post finalize, nonce/tamper/foreign/invalid-JWT rejection, stop and non-destructive hide')
