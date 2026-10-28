import { spawn } from 'node:child_process'
import { mkdtemp, writeFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { isAbsolute, join } from 'node:path'

export const MAX_VIDEO_BYTES = 20 * 1024 * 1024
export const MAX_VIDEO_SECONDS = 30
export type VideoExtension = 'mp4' | 'webm'

type ProbeStream = {
  codec_type?: string
  codec_name?: string
  codec_tag_string?: string
  width?: number
  height?: number
  duration?: string
}
type ProbeResult = {
  format?: { format_name?: string; duration?: string }
  streams?: ProbeStream[]
}

/**
 * Trusted-server-only validation of a previously downloaded, immutable object.
 * Does not fetch, publish or delete Storage objects. ffprobe must be installed
 * in the server runtime; unavailable binaries fail closed.
 */
export async function probeVideoBytes(bytes: Buffer, extension: VideoExtension): Promise<{ duration: number; size: number }> {
  if (extension !== 'mp4' && extension !== 'webm') throw new Error('unsupported extension')
  if (!Buffer.isBuffer(bytes) || bytes.length === 0 || bytes.length > MAX_VIDEO_BYTES) {
    throw new Error('invalid video size')
  }
  // A seekable temporary file supports MP4 moov atoms stored at the end.
  const directory = await mkdtemp(join(tmpdir(), 'poker-video-probe-'))
  const filename = join(directory, `upload.${extension}`)
  let metadata: ProbeResult
  try {
    await writeFile(filename, bytes, { flag: 'wx', mode: 0o600 })
    // Production must supply an audited executable path bundled into the Vercel function.
    // Never accept a relative path or a shell command. Missing binaries fail closed.
    const configured = process.env.FFPROBE_BINARY_PATH
    if (configured && !isAbsolute(configured)) throw new Error('ffprobe binary path must be absolute')
    const executable = configured || (process.env.VERCEL ? join(process.cwd(), 'api', 'bin', 'ffprobe') : 'ffprobe')
    metadata = await new Promise<ProbeResult>((resolve, reject) => {
    const child = spawn(executable, [
      '-v', 'error', '-show_format', '-show_streams', '-of', 'json', '-i', filename,
    ], { stdio: ['pipe', 'pipe', 'pipe'], shell: false })
    let stdout = ''
    let stderrSize = 0
    let settled = false
    const finish = (error?: Error, result?: ProbeResult) => {
      if (settled) return
      settled = true
      clearTimeout(timeout)
      child.kill()
      if (error || !result) reject(error || new Error('invalid ffprobe result'))
      else resolve(result)
    }
    const timeout = setTimeout(() => finish(new Error('ffprobe timeout')), 20000)
    child.on('error', () => finish(new Error('ffprobe unavailable')))
    child.stdout.on('data', (chunk: Buffer) => {
      stdout += chunk.toString('utf8')
      if (Buffer.byteLength(stdout) > 256 * 1024) finish(new Error('ffprobe output too large'))
    })
    child.stderr.on('data', (chunk: Buffer) => {
      stderrSize += chunk.length
      if (stderrSize > 64 * 1024) finish(new Error('ffprobe error output too large'))
    })
    child.on('close', code => {
      if (settled) return
      if (code !== 0) return finish(new Error('ffprobe rejected video'))
      try { finish(undefined, JSON.parse(stdout) as ProbeResult) }
      catch { finish(new Error('invalid ffprobe JSON')) }
    })
    child.stdin.end()
    })
  } finally {
    await rm(directory, { recursive: true, force: true })
  }
  const streams = metadata.streams
  if (!Array.isArray(streams)) throw new Error('missing streams')
  const videos = streams.filter(s => s.codec_type === 'video')
  const audios = streams.filter(s => s.codec_type === 'audio')
  // Apple QuickTime MOV may carry a dedicated timed-metadata (mebx) data track.
  // This track is not playable content; do not accept arbitrary extra streams.
  const dataTracks = streams.filter(s => s.codec_type === 'data')
  const auxiliaryAllowed = (extension === 'mp4' || dataTracks.length === 0) &&
    dataTracks.every(s => s.codec_tag_string === 'mebx' || s.codec_tag_string === 'mdta')
  if (videos.length !== 1 || audios.length > 1 || !auxiliaryAllowed ||
      streams.length !== videos.length + audios.length + dataTracks.length) {
    throw new Error('invalid stream structure')
  }
  const videoCodecs = extension === 'mp4' ? ['h264', 'hevc', 'av1'] : ['vp8', 'vp9', 'av1']
  const audioCodecs = extension === 'mp4' ? ['aac', 'mp3', 'opus'] : ['opus', 'vorbis']
  if (!videoCodecs.includes(videos[0].codec_name || '') ||
      (audios.length && !audioCodecs.includes(audios[0].codec_name || ''))) {
    throw new Error('unsupported codec')
  }
  const { width, height } = videos[0]
  if (typeof width !== 'number' || typeof height !== 'number' ||
      !Number.isInteger(width) || !Number.isInteger(height) ||
      !width || !height || width > 4096 || height > 4096) {
    throw new Error('invalid video dimensions')
  }
  const formats = (metadata.format?.format_name || '').split(',')
  if (extension === 'mp4' ? !formats.some(f => f === 'mp4' || f === 'mov') :
    !formats.includes('matroska')) throw new Error('invalid container')
  // Ignore ancillary timed-metadata durations; bound the actual audio/video and format.
  const durations = [metadata.format?.duration, ...videos.map(s => s.duration), ...audios.map(s => s.duration)]
    .filter((value): value is string => typeof value === 'string').map(Number)
  if (!durations.length || durations.some(n => !Number.isFinite(n) || n <= 0 || n > MAX_VIDEO_SECONDS)) {
    throw new Error('invalid video duration')
  }
  return { duration: Math.max(...durations), size: bytes.length }
}
