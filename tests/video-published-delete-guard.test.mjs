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
