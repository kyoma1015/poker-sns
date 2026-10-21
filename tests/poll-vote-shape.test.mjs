import test from 'node:test'
import assert from 'node:assert/strict'
import { pollVoteRequest } from '../src/interactiveRequests.ts'
const now = Date.parse('2026-10-20T00:00:00Z')
const poll = { post_id:'fixture',kind:'poll',options:['A','B'],closes_at:'2026-10-20T01:00:00Z',is_anonymous:true }
for (const count of [0,1,5]) test(`vote rejects malformed ${count}-option server card`,()=> {
  assert.throws(()=>pollVoteRequest({...poll,options:Array.from({length:count},(_,i)=>String(i))},0,now))
})
