import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'
const source = readFileSync(new URL('../src/videoUpload.ts', import.meta.url), 'utf8')
test('video candidate declares required limits and MIME types', () => {
  assert.match(source, /20 \* 1024 \* 1024/)
  assert.match(source, /MAX_VIDEO_SECONDS = 30/)
  assert.match(source, /video\/mp4/)
  assert.match(source, /video\/webm/)
  assert.match(source, /URL\.revokeObjectURL\(url\)/)
})
