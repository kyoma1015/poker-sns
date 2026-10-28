import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {execFileSync} from 'node:child_process'
import {randomUUID} from 'node:crypto'
import {createClient} from '@supabase/supabase-js'
const env=Object.fromEntries(readFileSync(process.env.VIDEO_QA_ENV,'utf8').split('\n').filter(x=>x.includes('=')).map(x=>{const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1).replace(/^["']|["']$/g,'')]}))
assert.equal(env.API_URL,'http://127.0.0.1:56321')
assert.ok(env.DB_URL.includes('127.0.0.1:56322'))
function sql(text){try{return execFileSync('psql',[env.DB_URL,'-X','-qAt','-v','ON_ERROR_STOP=1'],{input:text,stdio:['pipe','pipe','pipe']}).toString().trim()}catch{throw Error('cloud foundation SQL failed; raw diagnostic withheld')}}
sql("set video.cloud_test_project_ref='hbhyuotzginwysrineyo';\n"+readFileSync('sql/video_cloud_test_foundation.sql','utf8'))
sql("notify pgrst,'reload schema'")
await new Promise(r=>setTimeout(r,1500))
const key=env.ANON_KEY||env.PUBLISHABLE_KEY
const client=()=>createClient(env.API_URL,key,{auth:{persistSession:false,autoRefreshToken:false}})
const owner=client(),other=client(),anon=client()
for(const c of [owner,other])assert.ifError((await c.auth.signUp({email:randomUUID()+'@example.invalid',password:randomUUID()+'Aa1!'})).error)
const uid=(await owner.auth.getUser()).data.user.id
const deniedUid=(await other.auth.getUser()).data.user.id
assert.match(uid,/^[0-9a-f-]{36}$/)
sql("insert into video_cloud.allowed_users(user_id,enabled) values('"+uid+"',true)")
const path=uid+'/'+randomUUID()+'.mp4'
const manifest={p_path:path,p_sha256:'a'.repeat(64),p_size:4,p_mime:'video/mp4',p_content:'cloud test'}
for(const c of [owner,other,anon]){
 if(c===owner)continue
 assert.ok((await c.rpc('video_cloud_reserve',manifest)).error,'denied identity reserved')
}
assert.ok((await owner.rpc('video_cloud_reserve',{...manifest,p_path:deniedUid+'/'+randomUUID()+'.mp4'})).error)
const concurrent=await Promise.all([owner.rpc('video_cloud_reserve',manifest),owner.rpc('video_cloud_reserve',manifest)])
for(const r of concurrent)assert.ifError(r.error)
assert.equal(concurrent[0].data,concurrent[1].data)
assert.equal(sql("select count(*) from video_cloud.reservations"),'1')
assert.ok((await owner.rpc('video_cloud_reserve',{...manifest,p_sha256:'b'.repeat(64)})).error)
assert.ok((await owner.schema('video_cloud').from('reservations').insert({path})).error)
assert.ok((await owner.from('posts').insert({user_id:uid,content:'bypass'})).error)
const bytes=Buffer.from('test')
assert.ifError((await owner.storage.from('post-videos').upload(path,bytes,{contentType:'video/mp4',upsert:false})).error)
assert.ok((await owner.storage.from('post-videos').upload(path,bytes,{contentType:'video/mp4',upsert:true})).error)
assert.ok((await owner.storage.from('post-videos').update(path,bytes,{contentType:'video/mp4'})).error)
const removed=await owner.storage.from('post-videos').remove([path])
assert.ok(removed.error||!removed.data?.length)
assert.ok((await other.storage.from('post-videos').download(path)).error)
const read=await owner.storage.from('post-videos').download(path);assert.ifError(read.error)
assert.deepEqual(Buffer.from(await read.data.arrayBuffer()),bytes)
sql("update video_cloud.reservations set expires_at=clock_timestamp()-interval '1 second'")
assert.ok((await owner.rpc('video_cloud_reserve',manifest)).error)
console.log('PASS: cloud foundation real Auth/RPC/Storage: allowlist, anonymous/foreign denial, concurrent exact reservation, manifest tamper/expiry, direct write and Storage mutation denial')
