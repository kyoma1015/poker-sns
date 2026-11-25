// Isolated real ffprobe regression: no Supabase, credentials, Storage, or network.
import assert from 'node:assert/strict'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'
import ts from 'typescript'

const directory = await mkdtemp(join(tmpdir(), 'poker-opus-mp4-'))
try {
  const source = await readFile('api/video-ffprobe.ts', 'utf8')
  const js = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 }
  }).outputText
  const { probeVideoBytes } = await import('data:text/javascript;base64,' + Buffer.from(js).toString('base64'))
  const file = join(directory, 'opus.mp4')
  execFileSync('ffmpeg', [
    '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:size=160x120:rate=15',
    '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000',
    '-t', '2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-c:a', 'libopus', '-strict', '-2', '-y', file
  ], { timeout: 30000 })
  const bytes = await readFile(file)
  const metadata = JSON.parse(execFileSync('ffprobe', [
    '-v', 'error', '-show_streams', '-show_format', '-of', 'json', file
  ], { encoding: 'utf8', timeout: 10000 }))
  assert.ok(metadata.streams.some(s => s.codec_type === 'video' && s.codec_name === 'h264'))
  assert.ok(metadata.streams.some(s => s.codec_type === 'audio' && s.codec_name === 'opus'))
  const result = await probeVideoBytes(bytes, 'mp4')
  assert.ok(result.duration > 1.5 && result.duration <= 30)
  assert.equal(result.size, bytes.length)
  await assert.rejects(probeVideoBytes(Buffer.from('invalid'), 'mp4'))
  console.log('PASS real H264/Opus MP4 accepted by server ffprobe; invalid bytes rejected')
} finally {
  await rm(directory, { recursive: true, force: true })
}
