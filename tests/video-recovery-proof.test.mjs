import test from 'node:test'
import assert from 'node:assert/strict'
import { isProvenPublishedVideoRecovery, matchesPendingVideoRecovery } from '../src/videoRecoveryProof.ts'

const owner = '11111111-1111-4111-8111-111111111111'
const path = owner + '/22222222-2222-4222-8222-222222222222.mp4'
const sha256 = 'a'.repeat(64)
const hint = { sha256, size: 1024 }
const proof = { state: 'published', allow_resume: false, storage_present: true,
  sha256, size: 1024, post_id: '33333333-3333-4333-8333-333333333333' }

test('published recovery requires complete server proof and matching immutable file identity', () => {
  assert.equal(isProvenPublishedVideoRecovery(proof, hint), true)
  for (const mutation of [
    { state: 'stored_unpublished' }, { allow_resume: true }, { storage_present: false },
    { sha256: 'b'.repeat(64) }, { size: 1025 }, { post_id: null }, { post_id: 'invalid' },
  ]) assert.equal(isProvenPublishedVideoRecovery({ ...proof, ...mutation }, hint), false)
})

test('pending recovery rejects malformed, unrelated, and mismatched local drafts', () => {
  assert.equal(matchesPendingVideoRecovery(null, owner, path), true)
  assert.equal(matchesPendingVideoRecovery(JSON.stringify({ owner, path, content: 'draft' }), owner, path), true)
  for (const raw of [
    '{', 'null', '[]', '{}',
    JSON.stringify({ owner: '44444444-4444-4444-8444-444444444444', path }),
    JSON.stringify({ owner, path: owner + '/other.mp4' }),
  ]) assert.equal(matchesPendingVideoRecovery(raw, owner, path), false)
})
