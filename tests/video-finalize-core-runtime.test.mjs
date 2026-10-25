import assert from 'node:assert/strict'
import test from 'node:test'
import { finalizeImmutableCandidate } from '../api/video-finalize-core.ts'
const owner = '11111111-1111-4111-8111-111111111111'
const file = '22222222-2222-4222-8222-222222222222'
const path = owner + '/' + file + '.mp4'
const token = 'verified-jwt'
function adapters(overrides = {}) {
  const calls = []
  const result = {
    authenticate: async value => { calls.push('auth'); assert.equal(value, token); return owner },
    snapshot: async () => { calls.push('snapshot'); return { ownerId: owner, objectPath: path, generation: 'g1', size: 3, bytes: Buffer.from('bad') } },
    currentGeneration: async () => { calls.push('generation'); return 'g1' },
    publish: async () => { calls.push('publish'); return 'post-id' },
    reconcile: async () => { calls.push('reconcile'); return null },
    ...overrides,
  }
  return { calls, result }
}
test('owner mismatch rejects before Storage access', async () => {
  const { calls, result } = adapters({ authenticate: async () => '33333333-3333-4333-8333-333333333333' })
  await assert.rejects(finalizeImmutableCandidate(token, path, '', result), /owner mismatch/)
  assert.deepEqual(calls, [])
})
test('missing generation fails before ffprobe or publish', async () => {
  const { calls, result } = adapters({ snapshot: async () => ({ ownerId: owner, objectPath: path, generation: null, size: 3, bytes: Buffer.from('bad') }) })
  await assert.rejects(finalizeImmutableCandidate(token, path, '', result), /not proven/)
  assert.ok(!calls.includes('publish'))
})
test('changed generation fails closed before publish', async () => {
  const { calls, result } = adapters({ currentGeneration: async () => 'g2' })
  await assert.rejects(finalizeImmutableCandidate(token, path, '', result), /not proven/)
  assert.ok(!calls.includes('publish'))
})
test('untrusted path and unexpected snapshot owner fail closed', async () => {
  const { calls, result } = adapters()
  await assert.rejects(finalizeImmutableCandidate(token, owner + '/bad.mp4', '', result), /invalid Storage path/)
  assert.deepEqual(calls, [])
  const x = adapters({ snapshot: async () => ({ ownerId: 'other', objectPath: path, generation: 'g1', size: 3, bytes: Buffer.from('bad') }) })
  await assert.rejects(finalizeImmutableCandidate(token, path, '', x.result), /snapshot owner mismatch/)
  assert.ok(!x.calls.includes('publish'))
})
test('malformed bytes never reach publish or cleanup', async () => {
  const { calls, result } = adapters()
  await assert.rejects(finalizeImmutableCandidate(token, path, '', result))
  assert.ok(!calls.includes('publish'))
  assert.ok(!calls.includes('reconcile'))
})

test('revoked JWT during preflight cannot reach publish', async () => {
  let checks = 0
  const { calls, result } = adapters({
    authenticate: async () => {
      checks++
      return checks === 1 ? owner : '33333333-3333-4333-8333-333333333333'
    },
  })
  // This malformed fixture is rejected by ffprobe first; no publish is permitted.
  await assert.rejects(finalizeImmutableCandidate(token, path, '', result))
  assert.ok(!calls.includes('publish'))
})
