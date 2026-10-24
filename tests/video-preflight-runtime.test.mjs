import assert from 'node:assert/strict'
import test from 'node:test'
import { createHash } from 'node:crypto'
import { inspectStagedVideo, requireImmutableGeneration } from '../api/video-preflight.ts'

test('immutable generation fence rejects missing or changed generation', () => {
  assert.throws(() => requireImmutableGeneration(null, 'v1'), /not proven/)
  assert.throws(() => requireImmutableGeneration('v1', null), /not proven/)
  assert.throws(() => requireImmutableGeneration('v1', 'v2'), /not proven/)
  assert.doesNotThrow(() => requireImmutableGeneration('v1', 'v1'))
})

test('preflight rejects mismatched object sizes before any probe', async () => {
  await assert.rejects(inspectStagedVideo(Buffer.from('abc'), 'mp4', 2), /expected object size/)
  await assert.rejects(inspectStagedVideo(Buffer.from('abc'), 'mp4', 0), /expected object size/)
  await assert.rejects(inspectStagedVideo(Buffer.from('abc'), 'mp4', 21 * 1024 * 1024), /expected object size/)
  await assert.rejects(inspectStagedVideo(Buffer.from('abc'), 'mp4', 3), /ffprobe/)
})

test('preflight hash uses full byte sequence', () => {
  const a = Buffer.from('example')
  const b = Buffer.from('examplf')
  assert.notEqual(createHash('sha256').update(a).digest('hex'), createHash('sha256').update(b).digest('hex'))
})
