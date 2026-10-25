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
test('posting is gated by explicit default-off production readiness', () => {
  assert.match(timeline, /if \(!VIDEO_SERVER_ENABLED\)/)
  assert.match(timeline, /videoFile \? await uploadPostVideo\(user\.id, videoFile\) : ''/)
  const api = readFileSync(new URL('../src/videoApi.ts', import.meta.url), 'utf8')
  assert.match(api, /VIDEO_SERVER_ENABLED = import\.meta\.env\.VITE_VIDEO_SERVER_ENABLED === 'true'/)
  assert.match(api, /if \(!VIDEO_SERVER_ENABLED\) throw new Error/)
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

test('reload recovery retains immutable owner/path/content and reopens composer', () => {
  assert.match(timeline, /sessionStorage\.getItem\('poker-id-pending-video-v1'\)/)
  assert.match(timeline, /pendingVideoRef\.current = staged[\s\S]*?setPendingVideo\(staged\)[\s\S]*?setContent\(staged\.content\)[\s\S]*?setComposeOpen\(true\)/)
  assert.match(timeline, /pendingVideoRef\.current\?\.path \?\? \(videoFile \? await uploadPostVideo/)
  assert.match(timeline, /sessionStorage\.removeItem\('poker-id-pending-video-v1'\)/)
})
test('pending finalize rejects owner/content changes and async video selection races', () => {
  assert.match(timeline, /pendingVideoRef\.current\.owner !== user\.id \|\| pendingVideoRef\.current\.content !== content\.trim\(\)/)
  assert.match(timeline, /videoSubmitInFlightRef\.current = true/)
  assert.match(timeline, /if \(pendingVideoRef\.current \|\| videoSubmitInFlightRef\.current\)/)
  assert.match(timeline, /if \(videoFile \|\| pendingVideoRef\.current\)/)
})
test('direct signed Storage playback URLs are blocked', () => {
  assert.doesNotMatch(source, /\.createSignedUrl\(/)
  assert.match(source, /createPostVideoPlaybackUrl\(_path: string\): Promise<string>[\s\S]*?throw new Error/)
})

test('pending draft restore verifies current authenticated account before showing content', () => {
  const restoreStart = timeline.indexOf("sessionStorage.getItem('poker-id-pending-video-v1')")
  const authStart = timeline.lastIndexOf('await supabase.auth.getUser()', restoreStart)
  const ownerCheck = timeline.indexOf('record.owner !== user.id', restoreStart)
  const renderDraft = timeline.indexOf('setContent(staged.content)', restoreStart)
  assert.ok(authStart >= 0 && authStart < restoreStart, 'authenticate before reading cached draft')
  assert.ok(ownerCheck > restoreStart && ownerCheck < renderDraft,
    'reject foreign owner before rendering private draft content')
  assert.match(timeline.slice(authStart, renderDraft), /cancelled \|\| error \|\| !user/)
  assert.match(timeline.slice(authStart, renderDraft), /cancelled \|\| record\.owner !== user\.id/)
})
