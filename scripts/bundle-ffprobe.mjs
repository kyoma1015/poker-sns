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

const url = 'https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz'
const sha256 = '3ce69353d40c9cfedbabbc9de5d6f4f225457d0eb0003995695f29af81fed0c0'
const expectedBytes = 156576080
if (process.platform !== 'linux' || process.arch !== 'x64') {
  console.log('ffprobe bundle: skipped non-Linux-x64 build')
  process.exit(0)
}
const work = mkdtempSync(join(tmpdir(), 'poker-ffprobe-build-'))
const MAX_ARCHIVE_BYTES = expectedBytes
try {
  const archive = join(work, 'ffmpeg.tar.xz')
  const response = await fetch(url, { redirect: 'follow', signal: AbortSignal.timeout(180000) })
  if (!response.ok || !response.body) throw new Error('pinned ffprobe archive download failed')
  const declaredLength = response.headers.get('content-length')
  if (declaredLength !== null && (!/^\\d+$/.test(declaredLength) || Number(declaredLength) !== expectedBytes)) {
    await response.body.cancel()
    throw new Error('ffprobe archive declared length exceeds pinned limit')
  }
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
