import assert from 'node:assert/strict'
import { pollVoteRequest } from '../src/interactiveRequests.ts'
const now=Date.parse('2026-10-21T00:00:00Z')
const poll={post_id:'synthetic-poll',kind:'poll',options:['A','B'],closes_at:'2099-01-01T00:00:00Z',is_anonymous:true}
for(const count of [2,3,4]) assert.equal(pollVoteRequest({...poll,options:Array.from({length:count},(_,i)=>String(i))},0,now).p_option_index,0)
for(const options of [['A'],['A','B','C','D','E']]) assert.throws(()=>pollVoteRequest({...poll,options},0,now),'malformed option count must fail closed')
assert.throws(()=>pollVoteRequest({...poll,kind:'question'},0,now))
console.log('PASS A immutable poll-boundary acceptance')
