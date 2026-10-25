import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const timeline=readFileSync(new URL('../src/Timeline.tsx',import.meta.url),'utf8')
const videoApi=readFileSync(new URL('../src/videoApi.ts',import.meta.url),'utf8')

test('published video deletion remains blocked before legacy unversioned Storage removal',()=>{
  const guard=timeline.indexOf("if (target.video_path) {\n        setMessage('動画付き投稿の削除は安全な回収処理の検証待ちです。')")
  const deleteCall=timeline.indexOf(".from('posts')\n        .delete()",guard)
  assert.ok(guard>0 && deleteCall>guard)
  assert.match(timeline.slice(guard,deleteCall),/return/)
})
test('video upload is opt-in and remains disabled without the release flag',()=>{
  assert.match(videoApi,/VIDEO_SERVER_ENABLED = import\.meta\.env\.VITE_VIDEO_SERVER_ENABLED === 'true'/)
  assert.match(timeline,/if \(!VIDEO_SERVER_ENABLED\)/)
})

test('legacy direct signed playback URLs and unfenced client deletes stay disabled',()=>{
  const upload=readFileSync(new URL('../src/videoUpload.ts',import.meta.url),'utf8')
  assert.doesNotMatch(upload,/\.createSignedUrl\(/)
  assert.doesNotMatch(upload,/\.storage\.from\(VIDEO_BUCKET\)\.remove\(/)
  assert.match(upload,/export async function removePostVideo[\s\S]*?throw new Error\('動画ファイルの削除は安全な条件付き削除が実装されるまで停止しています。'\)/)
  assert.match(upload,/export async function createPostVideoPlaybackUrl[\s\S]*?throw new Error/)
})
test('authorized media uses server JWT and RLS, never redirects to signed URLs',()=>{
  const media=readFileSync(new URL('../api/video-media.ts',import.meta.url),'utf8')
  assert.match(media,/viewer\.auth\.getUser\(token\)/)
  assert.match(media,/viewer\.from\('posts'\)/)
  assert.match(media,/VIDEO_PRODUCTION_FENCED_READY !== 'true'/)
  assert.match(media,/Cache-Control', 'no-store, private'/)
  assert.doesNotMatch(media,/\.createSignedUrl\(/)
  assert.doesNotMatch(media,/res\.redirect\(/)
})
