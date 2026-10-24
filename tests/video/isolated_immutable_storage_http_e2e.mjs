import assert from 'node:assert/strict'
import {createClient} from '@supabase/supabase-js'
import {randomUUID} from 'node:crypto'
import {readFileSync} from 'node:fs'
const env=Object.fromEntries(readFileSync(process.env.VIDEO_QA_ENV,'utf8').split('\n').filter(x=>x.includes('=')).map(x=>{const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1).replace(/^["']|["']$/g,'')]}))
const url=env.API_URL
assert.equal(url,'http://127.0.0.1:56321','isolated local Supabase only')
const key=env.ANON_KEY||env.PUBLISHABLE_KEY
const client=createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}})
assert.ifError((await client.auth.signUp({email:`immutable-${randomUUID()}@example.invalid`,password:'isolated-Immutable-Pass1!'})).error)
const user=(await client.auth.getUser()).data.user
assert.ok(user?.id)
const path=`${user.id}/${randomUUID()}.mp4`
const bucket=client.storage.from('post-videos')
const original=Buffer.from('immutable-storage-e2e')
assert.ifError((await bucket.upload(path,original,{contentType:'video/mp4',upsert:false})).error)
const read=await bucket.download(path)
assert.ifError(read.error)
assert.equal(Buffer.compare(Buffer.from(await read.data.arrayBuffer()),original),0)
const overwrite=await bucket.upload(path,Buffer.from('overwrite'),{contentType:'video/mp4',upsert:false})
assert.ok(overwrite.error,'collision must fail')
const update=await bucket.update(path,Buffer.from('overwrite'),{contentType:'video/mp4'})
assert.ok(update.error,'owner UPDATE must fail')
const remove=await bucket.remove([path])
assert.ok(remove.error || !remove.data?.length,'owner DELETE reported deletion')
const after=await bucket.download(path)
assert.ifError(after.error)
assert.equal(Buffer.compare(Buffer.from(await after.data.arrayBuffer()),original),0)
console.log('PASS: isolated immutable Storage guard owner upload/read, no-upsert collision, UPDATE and DELETE denied, bytes retained')
