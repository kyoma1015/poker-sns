import assert from 'node:assert/strict'
import test from 'node:test'
import { videoStorageFetch, withVideoUploadRequest, VIDEO_UPLOAD_TIMEOUT_MS } from '../src/videoUploadTransport.ts'

const path='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb.webm'
const url='http://127.0.0.1:56321/storage/v1/object/post-videos/'+path

test('private upload forwards lifecycle cancellation and refuses redirects',async()=>{
  const original=globalThis.fetch
  const controller=new AbortController()
  let observed
  globalThis.fetch=async(_input,init)=>{observed=init;return new Response('{}')}
  try {
    await withVideoUploadRequest(path,controller.signal,()=>videoStorageFetch(url,{method:'POST'}))
    assert.equal(observed.redirect,'error')
    assert.equal(observed.signal.aborted,false)
    controller.abort()
    assert.equal(observed.signal.aborted,true)
    // A finished upload must not leak its cancellation context to other calls.
    await videoStorageFetch(url,{method:'POST'})
    assert.equal(observed.signal,undefined)
  } finally {globalThis.fetch=original}
})

test('deadline aborts the underlying upload and releases its context',async()=>{
  assert.equal(VIDEO_UPLOAD_TIMEOUT_MS,90000)
  const originalFetch=globalThis.fetch, originalTimer=globalThis.setTimeout
  let expire, observed
  globalThis.setTimeout=fn=>{expire=fn;return originalTimer(()=>{},100000)}
  globalThis.fetch=(_input,init)=>new Promise((_resolve,reject)=>{
    observed=init.signal
    init.signal.addEventListener('abort',()=>reject(new Error('aborted')),{once:true})
    queueMicrotask(()=>expire())
  })
  try {
    await assert.rejects(withVideoUploadRequest(path,undefined,()=>videoStorageFetch(url,{method:'POST'})),/aborted/)
    assert.equal(observed.aborted,true)
  } finally {globalThis.fetch=originalFetch;globalThis.setTimeout=originalTimer}
})

test('unrelated SDK requests are passed through and aborted work sends nothing',async()=>{
  const original=globalThis.fetch
  let calls=0, observed
  globalThis.fetch=async(_input,init)=>{calls++;observed=init;return new Response('{}')}
  try {
    const controller=new AbortController();controller.abort()
    await assert.rejects(withVideoUploadRequest(path,controller.signal,()=>videoStorageFetch(url,{method:'POST'})))
    assert.equal(calls,0)
    const init={method:'POST',redirect:'follow'}
    await withVideoUploadRequest(path,undefined,()=>videoStorageFetch('http://127.0.0.1:56321/rest/v1/posts',init))
    assert.equal(observed,init)
  } finally {globalThis.fetch=original}
})
