import assert from 'node:assert/strict'
import { test } from 'node:test'
import { spawnSync } from 'node:child_process'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { probeVideoBytes, MAX_VIDEO_BYTES } from '../api/video-ffprobe.ts'

const hasBinary = name => spawnSync(name, ['-version'], { stdio: 'ignore' }).status === 0

test('real server ffprobe accepts H264 and rejects invalid video', { skip: !hasBinary('ffmpeg') || !hasBinary('ffprobe') }, async () => {
  const dir = mkdtempSync(join(tmpdir(), 'poker-probe-test-'))
  try {
    const valid = join(dir, 'valid.mp4')
    const long = join(dir, 'long.mp4')
    const generate = (target, seconds) => spawnSync('ffmpeg', [
      '-hide_banner', '-loglevel', 'error', '-f', 'lavfi',
      '-i', 'color=c=black:s=32x32:r=5', '-t', String(seconds),
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-y', target,
    ], { timeout: 25000 })
    assert.equal(generate(valid, 2).status, 0)
    assert.equal(generate(long, 31).status, 0)
    const good = readFileSync(valid)
    const result = await probeVideoBytes(good, 'mp4')
    assert.ok(result.duration > 0 && result.duration <= 30)
    assert.equal(result.size, good.length)
    await assert.rejects(probeVideoBytes(readFileSync(long), 'mp4'), /duration/)
    await assert.rejects(probeVideoBytes(Buffer.from('not a video'), 'mp4'))
    await assert.rejects(probeVideoBytes(good, 'webm'))
    await assert.rejects(probeVideoBytes(Buffer.alloc(MAX_VIDEO_BYTES + 1), 'mp4'), /size/)
  } finally {
    rmSync(dir, { recursive: true, force: true })
  }
})

test('ffprobe missing input is rejected without executing a shell', async () => {
  await assert.rejects(probeVideoBytes(Buffer.alloc(0), 'mp4'), /size/)
  await assert.rejects(probeVideoBytes(Buffer.from('invalid'), 'avi'), /extension/)
})
