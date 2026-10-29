import test from 'node:test'
import assert from 'node:assert/strict'
import { readVideoResponse, MAX_PLAYBACK_BYTES } from '../src/videoMedia.ts'

function media(chunks, headers = {'content-type':'video/mp4'}) {
  let cancelled = false
  let reads = 0
  const body = new ReadableStream({
    pull(controller) { reads++; if(chunks.length) controller.enqueue(chunks.shift()); else controller.close() },
    cancel() { cancelled = true },
  }, {highWaterMark:0})
  return {response:new Response(body,{headers}),get cancelled(){return cancelled},get reads(){return reads}}
}
test('playback accepts bounded MP4/WebM/MOV and normalizes MIME parameters', async()=>{
  for(const mime of ['video/mp4','video/webm; charset=binary','video/quicktime']) {
    const m=media([new Uint8Array([1,2,3])],{'content-type':mime,'content-length':'3'})
    const blob=await readVideoResponse(m.response)
    assert.equal(blob.size,3)
    assert.equal(blob.type,mime.split(';')[0])
  }
})
test('bad headers cancel before reading authenticated bytes', async()=>{
  for(const headers of [
    {'content-type':'text/html'},
    {'content-type':'video/mp4','content-length':String(MAX_PLAYBACK_BYTES+1)},
    {'content-type':'video/mp4','content-length':'0'},
    {'content-type':'video/mp4','content-length':'1e2'},
  ]) {
    const m=media([new Uint8Array([1])],headers)
    await assert.rejects(readVideoResponse(m.response))
    assert.equal(m.reads,0)
    assert.equal(m.cancelled,true)
  }
})
test('chunked oversized playback stops before remaining chunks are read',async()=>{
  const m=media([new Uint8Array(MAX_PLAYBACK_BYTES),new Uint8Array(1),new Uint8Array(10)])
  await assert.rejects(readVideoResponse(m.response),/20MB/)
  assert.equal(m.reads,2)
  assert.equal(m.cancelled,true)
})
test('empty and truncated playback are rejected',async()=>{
  await assert.rejects(readVideoResponse(media([]).response))
  await assert.rejects(readVideoResponse(media([new Uint8Array(2)],{'content-type':'video/mp4','content-length':'3'}).response))
})
test('failed body releases reader and propagates failure',async()=>{
  const stream=new ReadableStream({pull(c){c.error(new Error('connection interrupted'))}})
  await assert.rejects(readVideoResponse(new Response(stream,{headers:{'content-type':'video/mp4'}})),/connection interrupted/)
  assert.equal(stream.locked,false)
})
