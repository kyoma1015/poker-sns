import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { sharePost } from '../src/sharePost.ts'

const data = { title: 'Poker ID', text: 'Public post', url: 'https://example.invalid/post/id' }
test('native share is awaited with the complete payload', async () => {
  let seen
  assert.equal(await sharePost(data, { share: async value => { seen = value } }), 'shared')
  assert.deepEqual(seen, data)
})
test('native cancellation stays silent and never writes clipboard', async () => {
  const calls = []
  assert.equal(await sharePost(data, { share: async () => { throw { name: 'AbortError' } }, clipboard: { writeText: async value => calls.push(value) } }), 'cancelled')
  assert.deepEqual(calls, [])
})
test('native failure falls back to the canonical post link only', async () => {
  const calls = []
  assert.equal(await sharePost(data, { share: async () => { throw new Error('unsupported') }, clipboard: { writeText: async value => calls.push(value) } }), 'copied')
  assert.deepEqual(calls, [data.url])
})
test('desktop clipboard copy is awaited', async () => {
  const calls = []
  assert.equal(await sharePost(data, { clipboard: { writeText: async value => calls.push(value) } }), 'copied')
  assert.deepEqual(calls, [data.url])
})
test('clipboard rejection becomes actionable guidance', async () => {
  await assert.rejects(sharePost(data, { clipboard: { writeText: async () => { throw new Error('denied') } } }), /リンクをコピーできませんでした/)
})
test('missing APIs fail explicitly instead of reporting copy success', async () => {
  await assert.rejects(sharePost(data, {}), /共有を利用できません/)
})
test('native success never also copies', async () => {
  const calls = []
  assert.equal(await sharePost(data, { share: async () => {}, clipboard: { writeText: async value => calls.push(value) } }), 'shared')
  assert.deepEqual(calls, [])
})
test('Timeline consumes share outcome and catches rejected operation', () => {
  const source = readFileSync(new URL('../src/Timeline.tsx', import.meta.url), 'utf8')
  assert.match(source, /const outcome = await sharePost/)
  assert.match(source, /if \(outcome === 'copied'\) setMessage/)
  assert.match(source, /共有に失敗しました/)
  assert.doesNotMatch(source, /navigator\.clipboard\?\.writeText/)
})
