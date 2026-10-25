// Pinned upstream release archive; no npm dependency or lockfile change required.
// Fail closed if the upstream asset changes or download/extraction fails.
import { createHash } from 'node:crypto'
import { createWriteStream, mkdirSync, mkdtempSync, readdirSync, copyFileSync, chmodSync, rmSync, statSync } from 'node:fs'
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
try {
  const archive = join(work, 'ffmpeg.tar.xz')
  const response = await fetch(url, { redirect: 'follow', signal: AbortSignal.timeout(180000) })
  if (!response.ok || !response.body) throw new Error('pinned ffprobe archive download failed')
  await pipeline(Readable.fromWeb(response.body), createWriteStream(archive))
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
  const entries = listing.stdout.trim().split('\\n')
  const probes = entries.filter(p => /^ffmpeg-master-latest-linux64-gpl\\/bin\\/ffprobe$/.test(p))
  if (probes.length !== 1) throw new Error('ffprobe archive layout changed')
  const extracted = spawnSync('tar', ['-xJf', archive, '-C', work, probes[0]], { timeout: 120000 })
  if (extracted.status !== 0) throw new Error('ffprobe extraction failed')
  const dest = join(process.cwd(), 'api', 'bin')
  mkdirSync(dest, { recursive: true })
  const target = join(dest, 'ffprobe')
  copyFileSync(join(work, probes[0]), target)
  chmodSync(target, 0o755)
  const verify = spawnSync(target, ['-version'], { timeout: 10000, stdio: 'ignore' })
  if (verify.status !== 0) throw new Error('bundled ffprobe execution failed')
  console.log('Pinned ffprobe executable verified')
} finally {
  rmSync(work, { recursive: true, force: true })
}
