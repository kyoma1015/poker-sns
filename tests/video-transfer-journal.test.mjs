import assert from 'node:assert/strict'
import test from 'node:test'
import {beginVideoTransfer, confirmVideoReservation, setVideoTransferPhase, handOffVideoTransfer, isVideoTransferBlocked, hasVideoTransferJournal, readVideoTransferHint, finishRecoveredVideoTransfer} from '../src/videoTransferJournal.ts'
const values=new Map()
Object.defineProperty(globalThis,'sessionStorage',{configurable:true,value:{getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value),removeItem:key=>values.delete(key)}})
const record=owner=>({owner,path:owner+'/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb.webm',sha256:'a'.repeat(64),size:100,type:'video/webm',startedAt:Date.now(),phase:'reserving'})

test('reserving/reloaded journal never authorizes operations, even if claiming an ACK',async()=>{
  const r=record('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
  beginVideoTransfer(r)
  assert.equal(isVideoTransferBlocked(r.owner),true)
  confirmVideoReservation(r)
  assert.equal(isVideoTransferBlocked(r.owner),false,'live confirmed retry remains available')
  const reloaded=await import('../src/videoTransferJournal.ts?reloaded')
  assert.equal(reloaded.isVideoTransferBlocked(r.owner),true,'module restart cannot trust saved confirmation')
  values.set('poker-id-video-transfer-v1:'+r.owner,JSON.stringify({...r,phase:'acknowledged',startedAt:Date.now()+999999999}))
  assert.equal(isVideoTransferBlocked(r.owner),true,'edited phase/time cannot authorize recovery')
  assert.throws(()=>handOffVideoTransfer(r.owner,r.path))
})

test('handoff requires matching live acknowledgment and preserves journal on mismatch',()=>{
  const r=record('cccccccc-cccc-4ccc-8ccc-cccccccccccc')
  beginVideoTransfer(r);confirmVideoReservation(r)
  assert.throws(()=>handOffVideoTransfer(r.owner,r.path))
  setVideoTransferPhase(r,'uploading');setVideoTransferPhase(r,'acknowledged')
  assert.throws(()=>handOffVideoTransfer(r.owner,'wrong-path'))
  assert.equal(hasVideoTransferJournal(r.owner),true)
  handOffVideoTransfer(r.owner,r.path)
  assert.equal(hasVideoTransferJournal(r.owner),false)
})

test('malformed and inaccessible storage fail closed; foreign journals are not loaded',()=>{
  values.set('poker-id-video-transfer-v1:malformed','{')
  assert.equal(isVideoTransferBlocked('malformed'),true)
  assert.equal(hasVideoTransferJournal('different-user'),false)
  const storage=globalThis.sessionStorage
  Object.defineProperty(globalThis,'sessionStorage',{configurable:true,value:{getItem(){throw Error('unavailable')},setItem(){throw Error('unavailable')}}})
  try {
    assert.equal(isVideoTransferBlocked('owner'),true)
    assert.equal(hasVideoTransferJournal('owner'),true)
    assert.throws(()=>beginVideoTransfer(record('owner')))
  } finally {Object.defineProperty(globalThis,'sessionStorage',{configurable:true,value:storage})}
})

test('recovery hints are owner-scoped and confirmed cleanup cannot erase a newer record',()=>{
 const owner='dddddddd-dddd-4ddd-8ddd-dddddddddddd',r=record(owner),key='poker-id-video-transfer-v1:'+owner
 values.set(key,JSON.stringify(r))
 const hint=readVideoTransferHint(owner)
 assert.equal(hint.path,r.path)
 values.set(key,JSON.stringify({...r,sha256:'b'.repeat(64)}))
 assert.throws(()=>finishRecoveredVideoTransfer(owner,hint.path,hint.raw))
 assert.equal(hasVideoTransferJournal(owner),true)
 values.set(key,hint.raw)
 finishRecoveredVideoTransfer(owner,hint.path,hint.raw)
 assert.equal(hasVideoTransferJournal(owner),false)
 values.set(key,JSON.stringify({...r,path:'different-owner/path.webm'}))
 assert.throws(()=>readVideoTransferHint(owner))
})
