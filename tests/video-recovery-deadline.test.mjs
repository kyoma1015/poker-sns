import assert from 'node:assert/strict'
import test from 'node:test'
import {withVideoRecoveryDeadline,RECOVERY_REQUEST_TIMEOUT_MS} from '../src/videoRecoveryDeadline.ts'

test('abort releases a hung session request and prevents late IO',async()=>{
 const controller=new AbortController()
 let release,io=0
 const gate=new Promise(resolve=>{release=resolve})
 const pending=withVideoRecoveryDeadline(controller.signal,async signal=>{await gate;signal.throwIfAborted();io++})
 controller.abort()
 await assert.rejects(pending)
 release();await new Promise(resolve=>setImmediate(resolve))
 assert.equal(io,0)
})
test('deadline includes session initialization and rejects before it resolves',async()=>{
 assert.equal(RECOVERY_REQUEST_TIMEOUT_MS,30000)
 const timer=globalThis.setTimeout
 let expire,release,io=0
 globalThis.setTimeout=fn=>{expire=fn;return timer(()=>{},100000)}
 try {
  const gate=new Promise(resolve=>{release=resolve})
  const pending=withVideoRecoveryDeadline(undefined,async signal=>{await gate;signal.throwIfAborted();io++})
  expire();await assert.rejects(pending)
  release();await new Promise(resolve=>setImmediate(resolve))
  assert.equal(io,0)
 } finally {globalThis.setTimeout=timer}
})
test('already-aborted request starts no work; completed requests clear their timer',async()=>{
 const controller=new AbortController();controller.abort()
 let calls=0
 await assert.rejects(withVideoRecoveryDeadline(controller.signal,async()=>{calls++}))
 assert.equal(calls,0)
 assert.equal(await withVideoRecoveryDeadline(undefined,async signal=>{assert.equal(signal.aborted,false);return 7}),7)
})
