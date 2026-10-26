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
}
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
