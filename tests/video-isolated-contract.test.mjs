import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'

const read = path => readFileSync(new URL(path, import.meta.url), 'utf8')
const timeline = read('../src/Timeline.tsx')
const detail = read('../src/PostDetail.tsx')
const playback = read('../src/PostVideo.tsx')
const upload = read('../src/videoUpload.ts')
const sql = read('../sql/post_short_videos_candidate.sql')

test('video schema is staged and storage bucket is private with 20MiB cap', () => {
  assert.match(sql, /alter table public\.posts add column if not exists video_path text/)
  assert.match(sql, /'post-videos', 'post-videos', false, 20971520/)
  assert.match(sql, /create policy "post_videos_insert_own"/)
  assert.match(sql, /create policy "post_videos_delete_own"/)
  assert.match(sql, /create policy "post_videos_read_own"/)
  assert.doesNotMatch(sql, /^create policy "post_videos_read_post_viewers"/m)
  assert.match(sql, /video_path ~ '[^']+'\);/)
})
test('client validates duration and type but does not enable publishing', () => {
  assert.match(upload, /MAX_VIDEO_SECONDS = 30/)
  assert.match(upload, /MAX_VIDEO_BYTES = 20 \* 1024 \* 1024/)
  assert.match(upload, /video\/mp4/)
  assert.match(upload, /video\/webm/)
  assert.match(timeline, /if \(videoFile\) \{ setMessage\('動画投稿は安全な保存・配信の実装待ちです/)
})
test('playback is a short-lived private signed URL and not a public URL', () => {
  assert.match(upload, /createSignedUrl\(path, 300\)/)
  assert.doesNotMatch(upload, /getPublicUrl/)
  assert.match(playback, /createPostVideoPlaybackUrl\(path\)/)
  assert.match(timeline, /<PostVideo path=\{post\.video_path\}/)
  assert.match(detail, /<PostVideo path=\{post\.video_path\}/)
})
test('video cleanup validates owner path but fails closed without atomic delete', () => {
  assert.match(upload, /isOwnedVideoPath\(path, user\.id\)/)
  assert.doesNotMatch(upload, /\.remove\(\[path\]\)/)
  assert.match(upload, /throw new Error\('動画ファイルの削除は安全な条件付き削除/)
  const deleteStart = timeline.indexOf("const handleDelete = async")
  const deleteEnd = timeline.indexOf("\n  const ", deleteStart + 10)
  const deleteHandler = timeline.slice(deleteStart, deleteStart + 2400)
  assert.match(deleteHandler, /\.from\('posts'\)/)
  assert.match(deleteHandler, /removePostVideo\(user\.id, target\.video_path\)/)
})
test('end-to-end publishing and server duration enforcement are not claimed', () => {
  assert.doesNotMatch(timeline, /await uploadPostVideo\(/)
  assert.match(sql, /server-side (?:duration|30s)/i)
})
