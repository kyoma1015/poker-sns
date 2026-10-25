// Real local Supabase Storage HTTP checks; no production network.
import assert from 'node:assert/strict'
import {createClient} from '@supabase/supabase-js'
import {randomUUID} from 'node:crypto'
import {readFileSync} from 'node:fs'
const env=Object.fromEntries(readFileSync(process.env.VIDEO_QA_ENV,'utf8')
  .split('\n').filter(x=>x.includes('=')).map(x=>{
    const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1).replace(/^["']|["']$/g,'')]
  }))
assert.equal(env.API_URL,'http://127.0.0.1:56321')
const anon=env.ANON_KEY||env.PUBLISHABLE_KEY
const owner=createClient(env.API_URL,anon,{auth:{persistSession:false,autoRefreshToken:false}})
const other=createClient(env.API_URL,anon,{auth:{persistSession:false,autoRefreshToken:false}})
const admin=createClient(env.API_URL,env.SERVICE_ROLE_KEY,{auth:{persistSession:false,autoRefreshToken:false}})
for(const [client,label] of [[owner,'owner'],[other,'other']]){
  assert.ifError((await client.auth.signUp({email:`writer-${label}-${randomUUID()}@example.invalid`,password:'Isolated-Writer-Password1!'})).error)
}
const ownerId=(await owner.auth.getUser()).data.user.id
const path=`${ownerId}/${randomUUID()}.webm`
const bytes=Buffer.from('reserved-key-writer-check')
const unreserved=await owner.storage.from('post-videos').upload(path,bytes,{contentType:'video/webm',upsert:false})
assert.ok(unreserved.error,'unreserved Storage INSERT must be rejected')
const forged=await other.storage.from('post-videos').upload(path,bytes,{contentType:'video/webm',upsert:false})
assert.ok(forged.error,'foreign Storage writer must be rejected')
const {data:reservation,error:reservationError}=await admin.rpc('video_reserve_object_key',{p_owner:ownerId,p_path:path})
assert.ifError(reservationError)
assert.ok(reservation,'trusted server must reserve permanent key')
assert.ifError((await owner.storage.from('post-videos').upload(path,bytes,{contentType:'video/webm',upsert:false})).error)
assert.ok((await owner.storage.from('post-videos').upload(path,bytes,{contentType:'video/webm',upsert:true})).error,'upsert must fail')
assert.ok((await owner.storage.from('post-videos').update(path,bytes,{contentType:'video/webm'})).error,'UPDATE must fail')
const remove=await owner.storage.from('post-videos').remove([path])
assert.ok(remove.error||!remove.data?.length,'DELETE must not remove object')
const download=await owner.storage.from('post-videos').download(path)
assert.ifError(download.error)
assert.equal(Buffer.compare(Buffer.from(await download.data.arrayBuffer()),bytes),0)
console.log('PASS: real isolated HTTP unreserved/foreign rejected, reserved owner allowed, overwrite/delete denied')
