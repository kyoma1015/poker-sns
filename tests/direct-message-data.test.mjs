import test from 'node:test'
import assert from 'node:assert/strict'
import {isDirectMessageForConversation,conversationMessages} from '../src/directMessageData.ts'
const row=()=>({id:'row',sender_id:'me',receiver_id:'peer',content:'hello',created_at:'2026-10-28T00:00:00Z',read_at:null})
test('both directions and empty text stay valid without inventing content',()=>{
 const a=Object.freeze(row()),b=Object.freeze({...row(),id:'incoming',sender_id:'peer',receiver_id:'me',content:'',read_at:'2026-10-28T00:01:00Z'})
 assert.deepEqual(conversationMessages(Object.freeze([a,b]),'me','peer'),[a,b])
 assert.deepEqual(conversationMessages(null,'me','peer'),[])
})
for(const [name,value]of [
 ['null',null],['array',[]],['text','bad'],['boolean',true],['wrong pair',{...row(),sender_id:'someone'}],
 ['other peer',{...row(),receiver_id:'another'}],['empty ID',{...row(),id:' '}],
 ['object content',{...row(),content:{private:'not renderable'}}],['null content',{...row(),content:null}],
 ['invalid created time',{...row(),created_at:'not a date'}],['nonstring time',{...row(),created_at:2}],
 ['invalid read time',{...row(),read_at:false}],['missing read time',(({read_at,...rest})=>rest)(row())],
 ['inherited fields',Object.create(row())],
])test('invalid DM row refuses '+name,()=>{
 assert.equal(isDirectMessageForConversation(value,'me','peer'),false)
 assert.deepEqual(conversationMessages([value],'me','peer'),[])
})
test('non-array response rejects instead of producing zero verified messages',()=>{
 for(const value of [undefined,{},true,'bad',5])assert.throws(()=>conversationMessages(value,'me','peer'),/Invalid conversation/)
})
test('missing conversation identity cannot accept a message',()=>{
 assert.equal(isDirectMessageForConversation(row(),'me',undefined),false)
 assert.equal(isDirectMessageForConversation(row(),'','peer'),false)
})
