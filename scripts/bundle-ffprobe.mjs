// Pinned upstream release archive; no npm dependency or lockfile change required.
// Fail closed if the upstream asset changes or download/extraction fails.
import { createHash } from 'node:crypto'
import { createWriteStream, mkdirSync, mkdtempSync, readdirSync, copyFileSync, chmodSync, rmSync, statSync, renameSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { spawnSync } from 'node:child_process'
import { Readable } from 'node:stream'
import { pipeline } from 'node:stream/promises'
import { createReadStream } from 'node:fs'

// Immutable GitHub release asset ID; the mutable /latest URL is never used.
const url = 'https://api.github.com/repos/yt-dlp/FFmpeg-Builds/releases/assets/675690310'
const sha256 = 'f9c52a05bb4e51b44c7e7b52937b38d1fe28bfaa319bb291e6020a5cd9574f17'
const expectedBytes = 156579068
if (process.platform !== 'linux' || process.arch !== 'x64') {
  console.log('ffprobe bundle: skipped non-Linux-x64 build')
  process.exit(0)
}
const work = mkdtempSync(join(tmpdir(), 'poker-ffprobe-build-'))
const MAX_ARCHIVE_BYTES = expectedBytes
try {
  const archive = join(work, 'ffmpeg.tar.xz')
  const response = await fetch(url, { redirect: 'follow', headers: { Accept: 'application/octet-stream', 'User-Agent': 'poker-id-ffprobe-build' }, signal: AbortSignal.timeout(180000) })
  if (!response.ok || !response.body) throw new Error('pinned ffprobe archive download failed')
  // Redirects and intermediary compression can report a different HTTP
  // Content-Length than the decoded stream. Never trust that header for
  // integrity or safety; enforce the pinned limit on actual received bytes.
  let downloaded = 0
  const bounded = Readable.fromWeb(response.body).map(chunk => {
    downloaded += chunk.byteLength
    if (downloaded > MAX_ARCHIVE_BYTES) throw new Error('ffprobe archive exceeds pinned byte limit')
    return chunk
  })
  await pipeline(bounded, createWriteStream(archive))
  if (downloaded !== expectedBytes) throw new Error('ffprobe archive truncated')
  if (statSync(archive).size !== expectedBytes) throw new Error('ffprobe archive length mismatch')
  const digest = await new Promise((resolve, reject) => {
    const hash = createHash('sha256')
    const stream = createReadStream(archive)
    stream.on('data', chunk => hash.update(chunk))
    stream.on('error', reject)
    stream.on('end', () => resolve(hash.digest('hex')))
  })
  if (digest !== sha256) throw new Error('ffprobe archive SHA256 mismatch')
  const listing = spawnSync('tar', ['-tJf', archive], { encoding: 'utf8', maxBuffer: 1024 * 1024 })
  if (listing.status !== 0) throw new Error('ffprobe archive listing failed')
  const entries = listing.stdout.trim().split(String.fromCharCode(10))
  const probes = entries.filter(p => p.endsWith('/bin/ffprobe') && !p.includes('..') && p.split('/').length <= 5)
  if (probes.length !== 1) throw new Error('ffprobe archive layout changed')
  const extracted = spawnSync('tar', ['-xJf', archive, '-C', work, probes[0]], { timeout: 120000 })
  if (extracted.status !== 0) throw new Error('ffprobe extraction failed')
  const dest = join(process.cwd(), 'api', 'bin')
  mkdirSync(dest, { recursive: true })
  const target = join(dest, 'ffprobe')
  // Verify a temporary executable before atomically replacing the build
  // artifact. A failed download, extraction or exec must never leave a
  // partially copied ffprobe at the path included by Vercel.
  const staged = join(dest, '.ffprobe-' + process.pid + '.tmp')
  try {
    copyFileSync(join(work, probes[0]), staged)
    chmodSync(staged, 0o755)
    const verify = spawnSync(staged, ['-version'], { timeout: 10000, stdio: 'ignore' })
    if (verify.status !== 0) throw new Error('bundled ffprobe execution failed')
    renameSync(staged, target)
  } finally {
    rmSync(staged, { force: true })
  }
  console.log('Pinned ffprobe executable verified')
} finally {
  rmSync(work, { recursive: true, force: true })
}
