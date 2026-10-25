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
const duplicate=await admin.rpc('video_reserve_object_key',{p_owner:ownerId,p_path:path})
assert.ok(duplicate.error,'permanent key must never be reserved twice')
const unauthorized=await owner.rpc('video_reserve_object_key',{p_owner:ownerId,p_path:`${ownerId}/${randomUUID()}.webm`})
assert.ok(unauthorized.error,'authenticated client must not invoke privileged reservation RPC')
const {data:foreignReservation,error:foreignReservationError}=await admin.rpc('video_reserve_object_key',{
  p_owner:ownerId,p_path:`${(await other.auth.getUser()).data.user.id}/${randomUUID()}.webm`,
})
assert.ok(foreignReservationError,'privileged RPC must reject mismatched owner and path')
assert.equal(foreignReservation,null)
const {data:ledger,error:ledgerError}=await admin.from('video_reserved_object_keys')
  .select('reservation_id,owner_id,object_path').eq('object_path',path)
assert.ifError(ledgerError)
assert.equal(ledger.length,1,'reservation ledger must remain append-only and unique')
assert.equal(ledger[0].reservation_id,reservation)
assert.equal(ledger[0].owner_id,ownerId)
const clientDelete=await owner.from('video_reserved_object_keys').delete().eq('object_path',path)
assert.ok(clientDelete.error || !clientDelete.data?.length,
  'authenticated client must not erase permanent key reservation')
const {data:afterDelete,error:afterDeleteError}=await admin.from('video_reserved_object_keys')
  .select('reservation_id').eq('object_path',path)
assert.ifError(afterDeleteError)
assert.equal(afterDelete.length,1,'reservation must survive attempted client delete')
assert.equal(afterDelete[0].reservation_id,reservation)
assert.ifError((await owner.storage.from('post-videos').upload(path,bytes,{contentType:'video/webm',upsert:false})).error)
assert.ok((await owner.storage.from('post-videos').upload(path,bytes,{contentType:'video/webm',upsert:true})).error,'upsert must fail')
assert.ok((await owner.storage.from('post-videos').update(path,bytes,{contentType:'video/webm'})).error,'UPDATE must fail')
const remove=await owner.storage.from('post-videos').remove([path])
assert.ok(remove.error||!remove.data?.length,'DELETE must not remove object')
const download=await owner.storage.from('post-videos').download(path)
assert.ifError(download.error)
assert.equal(Buffer.compare(Buffer.from(await download.data.arrayBuffer()),bytes),0)
// A leaked global service_role key can still bypass authenticated RLS through
// the Storage management API. Record the observed capability without writing
// or deleting a production object. This is an explicit release blocker, not
// an assertion that application-level fetch guards revoke that key's power.
const adminStorageRead=await admin.storage.from('post-videos').download(path)
assert.ifError(adminStorageRead.error)
assert.equal(Buffer.compare(Buffer.from(await adminStorageRead.data.arrayBuffer()),bytes),0)
console.log('NO-GO CAPABILITY: global service_role can access video Storage outside application RPC fetch guards')
console.log('PASS: real isolated HTTP unreserved/foreign rejected, reserved owner allowed, overwrite/delete denied')
