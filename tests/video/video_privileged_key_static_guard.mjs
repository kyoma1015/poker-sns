// Static release fence: privileged Supabase credentials must never be wired
// into the video request handlers or browser video upload path.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const runtime=[
 'api/video-finalize.ts',
 'api/video-media.ts',
 'api/video-production-supabase-adapters.ts',
 'src/Timeline.tsx',
 'src/PostVideo.tsx',
 'src/videoApi.ts',
 'src/videoUpload.ts',
 'api/video-supabase-adapters.ts',
 'api/video-isolated-supabase-adapters.ts',
]
for (const file of runtime) {
 const code=readFileSync(file,'utf8')
 assert.doesNotMatch(code,/process\.env\.(?:SUPABASE_SERVICE_ROLE_KEY|SUPABASE_SECRET_KEY)|import\.meta\.env\.VITE_.*SERVICE_ROLE|service_role\s*:/i,
  file+' must not access privileged Supabase credentials')
 // Dot notation is not the only way to read process.env or import.meta.env.
 assert.doesNotMatch(code,/(?:process\.env|import\.meta\.env)\s*\[\s*['"`](?:SUPABASE_SERVICE_ROLE_KEY|SUPABASE_SECRET_KEY|VITE_[^'"`]*(?:SERVICE_ROLE|SECRET_KEY)[^'"`]*)['"`]\s*\]/i,
  file+' must not access privileged credentials through bracket notation')
}
// Signed Storage URLs remain valid until expiry even after post visibility
// changes. Video runtime must serve media through per-request JWT/RLS checks,
// never issue a persistent signed/public Storage URL.
for (const file of runtime) {
 const code=readFileSync(file,'utf8')
 assert.doesNotMatch(code,/\.\s*(?:createSignedUrl|createSignedUrls)\s*\(/,
  file+' must not issue signed Storage URLs for revocable video')
 if (file !== 'src/Timeline.tsx') {
  assert.doesNotMatch(code,/\.\s*getPublicUrl\s*\(/,
   file+' must not issue public Storage URLs for revocable video')
 } else {
  // Existing image posts use a public post-images bucket; do not break that
  // unrelated feature while prohibiting public URLs for the video bucket.
  const publicCalls=[...code.matchAll(/storage\.from\(['"]([^'"]+)['"]\)\.getPublicUrl\s*\(/g)]
  assert.equal((code.match(/\.getPublicUrl\s*\(/g)||[]).length,publicCalls.length,
   'Timeline public Storage URLs must have an explicit literal bucket')
  assert.ok(publicCalls.every(m=>m[1]==='post-images'),
   'Timeline video Storage must never issue public URLs')
 }
}
// Authenticated Storage reads must not follow redirects with caller JWT headers.
for (const file of ['api/video-media.ts', 'api/video-production-supabase-adapters.ts']) {
 const code=readFileSync(file,'utf8')
 assert.match(code,/redirect:\\s*'error'/,
  file+' must reject redirects during authenticated Storage reads')
}
const mediaHandler=readFileSync('api/video-media.ts','utf8')
assert.match(mediaHandler,/Cache-Control', 'private, no-store/,
 'video media must not be cacheable across authorization changes')
assert.match(mediaHandler,/viewer\.auth\.getUser\(token\)/,
 'video media must revalidate viewer JWT per request')
assert.match(mediaHandler,/await visible\(\) !== path/,
 'video media must recheck RLS visibility after reading bytes')

// Verify the detector itself rejects known privileged-key access forms.
const bracketKeyPattern=/(?:process\.env|import\.meta\.env)\s*\[\s*['"`](?:SUPABASE_SERVICE_ROLE_KEY|SUPABASE_SECRET_KEY|VITE_[^'"`]*(?:SERVICE_ROLE|SECRET_KEY)[^'"`]*)['"`]\s*\]/i
for (const forbidden of [
 "process.env['SUPABASE_SERVICE_ROLE_KEY']",
 'process.env["SUPABASE_SECRET_KEY"]',
 "import.meta.env['VITE_SUPABASE_SERVICE_ROLE_KEY']",
]) {
 assert.match(forbidden,bracketKeyPattern,'bracket-notation privileged key must be detected')
}

// Detect accidental removal of the reservation fence or introduction of
// mutable policies in the review-only Storage candidate.
const storagePolicy=readFileSync('sql/post_short_videos_immutable_review_only.sql','utf8')
assert.match(storagePolicy,/public\.video_reserved_key_is_owned\(name, \(select auth\.uid\(\)\)\)/,
 'Storage INSERT must require durable owner reservation')
assert.doesNotMatch(storagePolicy,/^create policy[^\n]*\n\s*for (?:update|delete|all)\b/gim,
 'review-only Storage policy must not create mutation grants')
const videoApi=readFileSync('src/videoApi.ts','utf8')
assert.match(videoApi,/VITE_VIDEO_SERVER_ENABLED === 'true'/,
 'browser video feature must be explicit opt-in')
const videoUpload=readFileSync('src/videoUpload.ts','utf8')
assert.match(videoUpload,/if \(!VIDEO_SERVER_ENABLED\) throw new Error/,
 'browser Storage upload must remain disabled before release')
assert.match(videoUpload,/upsert: false/,
 'browser video upload must never overwrite existing Storage object')
const adapter=readFileSync('api/video-production-supabase-adapters.ts','utf8')
assert.match(adapter,/assertServerAttestationAvailable\(\)/,'production attestation hard stop must remain')
assert.match(adapter,/throw new Error\('production video publish requires server-attested database authorization'\)/,
 'hard stop must throw until production fence is proven')
const finalize=readFileSync('api/video-finalize.ts','utf8')
assert.match(finalize,/!isolatedReservation/,'production reservation must remain disabled')
console.log('PASS: video runtime privileged-key isolation and production fail-closed gates')
