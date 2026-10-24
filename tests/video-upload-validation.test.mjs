import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'
const source = readFileSync(new URL('../src/videoUpload.ts', import.meta.url), 'utf8')
const sql = readFileSync(new URL('../sql/post_short_videos_candidate.sql', import.meta.url), 'utf8')
const timeline = readFileSync(new URL('../src/Timeline.tsx', import.meta.url), 'utf8')
test('video candidate declares required limits and MIME types', () => {
  assert.match(source, /20 \* 1024 \* 1024/)
  assert.match(source, /MAX_VIDEO_SECONDS = 30/)
  assert.match(source, /video\/mp4/)
  assert.match(source, /video\/webm/)
  assert.match(source, /URL\.revokeObjectURL\(url\)/)
})
test('posting remains blocked until server-side duration validation exists', () => {
  assert.match(timeline, /if \(videoFile\) \{ setMessage\('動画投稿は安全な保存・配信の実装待ちです/)
})
test('staged storage is private, limited, and not readable by every authenticated user', () => {
  assert.match(sql, /'post-videos', 'post-videos', false, 20971520/)
  assert.match(sql, /post_videos_read_own/)
  assert.doesNotMatch(sql, /^create policy "post_videos_read_post_viewers"/m)
  assert.match(sql, /BLOCKED/)
})
test('path validation is strict before deleting storage objects', () => {
  assert.match(source, /isOwnedVideoPath\(path, user\.id\)/)
  assert.match(source, /path\.split\('\/'\)\[0\] === userId/)
})
