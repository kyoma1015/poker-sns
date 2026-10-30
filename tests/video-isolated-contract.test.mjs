import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'

const read = path => readFileSync(new URL(path, import.meta.url), 'utf8')
const timeline = read('../src/Timeline.tsx')
const detail = read('../src/PostDetail.tsx')
const playback = read('../src/PostVideo.tsx')
const upload = read('../src/videoUpload.ts')
const api = read('../src/videoApi.ts')
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
  assert.match(timeline, /if \(!VIDEO_SERVER_ENABLED\)/)
  assert.match(api, /VIDEO_SERVER_ENABLED = import\.meta\.env\.VITE_VIDEO_SERVER_ENABLED === 'true'/)
  assert.match(api, /if \(!VIDEO_SERVER_ENABLED\) throw new Error/)
})
test('playback is gated behind an authenticated server API', () => {
  assert.match(api, /VIDEO_SERVER_ENABLED = import\.meta\.env\.VITE_VIDEO_SERVER_ENABLED === 'true'/)
  assert.match(api, /loadAuthorizedVideo\(postId/)
  assert.match(api, /Authorization: await authHeader\(\)/)
  assert.doesNotMatch(upload, /getPublicUrl/)
  assert.match(playback, /loadAuthorizedVideo\(postId\)/)
  assert.match(timeline, /<PostVideo postId=\{post\.id\}/)
  assert.match(detail, /<PostVideo postId=\{post\.id\}/)
})
test('video cleanup validates owner path but fails closed without atomic delete', () => {
  assert.match(upload, /isOwnedVideoPath\(path, user\.id\)/)
  assert.doesNotMatch(upload, /\.remove\(\[path\]\)/)
  assert.match(upload, /throw new Error\('動画ファイルの削除は安全な条件付き削除/)
  const deleteStart = timeline.indexOf("const handleDelete = async")
  const deleteEnd = timeline.indexOf("\n  const ", deleteStart + 10)
  const deleteHandler = timeline.slice(deleteStart, deleteStart + 2400)
  assert.match(deleteHandler, /\.from\('posts'\)/)
  assert.match(deleteHandler, /await hideVideoPost\(postId\)/)
  assert.doesNotMatch(deleteHandler, /removePostVideo\(/)
})
test('client upload and finalize remain behind disabled server gate', () => {
  assert.match(timeline, /if \(!VIDEO_SERVER_ENABLED\)/)
  assert.match(timeline, /await uploadPostVideo\(user\.id, videoFile, requestController\.signal, content\.trim\(\)\)/)
  assert.match(timeline, /await finalizeUploadedVideo\(path, content\.trim\(\), requestController\.signal\)/)
  assert.match(api, /VIDEO_SERVER_ENABLED = import\.meta\.env\.VITE_VIDEO_SERVER_ENABLED === 'true'/)
  assert.match(sql, /server-side (?:duration|30s)/i)
})

test('Vercel media route enforces JWT, post RLS and private byte delivery', () => {
  const handler = read('../api/video-media.ts')
  const routing = read('../vercel.json')
  assert.ok(routing.includes('/internal/video/media/:post_id'))
  assert.ok(handler.includes('viewer.auth.getUser(token)'))
  assert.ok(handler.includes(".from('posts')"))
  assert.ok(handler.includes(".select('user_id,video_path')"))
  assert.ok(!handler.includes("video_path,is_public"), "production posts has no is_public column")
  assert.ok(handler.includes('await visible() !== path'))
  assert.match(handler, /Cache-Control', 'private, no-store, no-cache, max-age=0, must-revalidate'/)
  assert.match(handler, /Vary', 'Authorization'/)
  assert.match(handler, /Cross-Origin-Resource-Policy', 'same-origin'/)
  for (const unsafe of ['createSignedUrl', 'getPublicUrl', '.remove(']) {
    assert.ok(!handler.includes(unsafe), unsafe)
  }
})

test('finalize preserves live adapter authentication for post-ffprobe JWT revocation', () => {
  const handler = read('../api/video-finalize.ts')
  assert.match(handler, /finalizeImmutableCandidate\(\s*authorization\.slice\(7\), object_path, content, activeAdapters/)
  assert.doesNotMatch(handler, /authenticate:\s*async\s*\(\)\s*=>\s*data\.user/)
})

test('Vercel finalize boundary rejects unsafe requests and cannot publish', () => {
  const handler = read('../api/video-finalize.ts')
  const routing = read('../vercel.json')
  assert.ok(routing.includes('/internal/video/finalize'))
  assert.ok(routing.includes('/api/video-finalize'))
  assert.match(handler, /req.method !== 'POST'/)
  assert.match(handler, /MAX_BODY_BYTES = 12 \* 1024/)
  assert.match(handler, /viewer.auth.getUser\(authorization.slice\(7\)\)/)
  assert.match(handler, /match\[1\] !== data.user.id/)
  const uuidPattern = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
  assert.ok(handler.includes('(' + uuidPattern + ')\\/(' + uuidPattern + ')\\.(mp4|webm)'), 'video path requires two complete UUIDs')
  assert.match(handler, /video_finalize_not_enabled/)
  assert.match(handler, /Object.getPrototypeOf\(body\) !== Object.prototype/)
  assert.match(handler, /Buffer.byteLength\(JSON.stringify\(body\), 'utf8'\) > MAX_BODY_BYTES/)
  for (const unsafe of [".from('posts').insert", '.upload(', '.remove(', 'createSignedUrl']) {
    assert.ok(!handler.includes(unsafe), unsafe)
  }
  assert.match(api, /VIDEO_SERVER_ENABLED = import\.meta\.env\.VITE_VIDEO_SERVER_ENABLED === 'true'/)
})

test('media permission is checked after asynchronous byte materialization', () => {
  const handler = read('../api/video-media.ts')
  assert.match(handler, /const bytes = Buffer\.concat\(chunks, received\)/)
  assert.match(handler, /received > MAX_BYTES/)
  assert.match(handler, /const reader = media\.body\.getReader\(\)/)
  assert.match(handler, /finalIdentity\.user\?\.id !== identity\.user\.id/)
  assert.match(handler, /await visible\(\) !== path/)
  assert.match(handler, /return res\.status\(403\)\.end\(\)/)
})

test('server ffprobe adapter bounds resource use and rejects malformed streams', () => {
  const validator = read('../api/video-ffprobe.ts')
  assert.match(validator, /MAX_VIDEO_BYTES = 20 \* 1024 \* 1024/)
  assert.match(validator, /MAX_VIDEO_SECONDS = 30/)
  assert.match(validator, /spawn\(executable/)
  assert.match(validator, /shell: false/)
  assert.match(validator, /isAbsolute\(configured\)/)
  assert.match(validator, /mkdtemp\(join\(tmpdir\(\)/)
  assert.match(validator, /writeFile\(filename, bytes/)
  assert.match(validator, /await rm\(directory, \{ recursive: true, force: true \}\)/)
  assert.match(validator, /20000/)
  assert.match(validator, /256 \* 1024/)
  assert.match(validator, /videos.length !== 1/)
  assert.match(validator, /streams.length !== videos.length \+ audios.length/)
  assert.match(validator, /unsupported codec/)
  assert.match(validator, /invalid video duration/)
  assert.doesNotMatch(validator, /storage\.from|\.remove\(|\.insert\(/)
  assert.match(api, /VIDEO_SERVER_ENABLED = import\.meta\.env\.VITE_VIDEO_SERVER_ENABLED === 'true'/)
})

test('read-only preflight cannot publish or delete objects', () => {
  const preflight = read('../api/video-preflight.ts')
  assert.match(preflight, /probeVideoBytes\(bytes, extension\)/)
  assert.match(preflight, /createHash\('sha256'\)/)
  assert.match(preflight, /before !== after/)
  const executable = preflight.replace(/\/\*[\s\S]*?\*\/|\/\/[^\n]*/g, '')
  for (const unsafe of ['createClient(', '.insert(', '.delete(', '.remove(', '.upload(', 'service_role']) {
    assert.ok(!executable.includes(unsafe), unsafe)
  }
  assert.match(api, /VIDEO_SERVER_ENABLED = import\.meta\.env\.VITE_VIDEO_SERVER_ENABLED === 'true'/)
})

test('review-only immutable Storage policy requires full UUID and no delete grants', () => {
  const candidate = read('../sql/post_short_videos_immutable_review_only.sql')
  assert.ok(candidate.includes('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'))
  assert.match(candidate, /No orphan cleanup without proven atomic conditional delete/)
  assert.match(candidate, /ABA replacement/)
  assert.doesNotMatch(candidate, /create policy[^\n]*delete/i)
  assert.doesNotMatch(candidate, /create policy[^\n]*update/i)
})
