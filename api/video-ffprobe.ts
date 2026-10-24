import { spawn } from 'node:child_process'

export const MAX_VIDEO_BYTES = 20 * 1024 * 1024
export const MAX_VIDEO_SECONDS = 30
export type VideoExtension = 'mp4' | 'webm'

type ProbeStream = {
  codec_type?: string
  codec_name?: string
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
  const metadata = await new Promise<ProbeResult>((resolve, reject) => {
    const child = spawn('ffprobe', [
      '-v', 'error', '-show_format', '-show_streams', '-of', 'json', '-i', 'pipe:0',
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
    child.stdin.on('error', () => { /* ffprobe may close stdin after rejecting bytes */ })
    child.stdin.end(bytes)
  })
  const streams = metadata.streams
  if (!Array.isArray(streams)) throw new Error('missing streams')
  const videos = streams.filter(s => s.codec_type === 'video')
  const audios = streams.filter(s => s.codec_type === 'audio')
  if (videos.length !== 1 || audios.length > 1 || streams.length !== videos.length + audios.length) {
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
  const durations = [metadata.format?.duration, ...streams.map(s => s.duration)]
    .filter((value): value is string => typeof value === 'string').map(Number)
  if (!durations.length || durations.some(n => !Number.isFinite(n) || n <= 0 || n > MAX_VIDEO_SECONDS)) {
    throw new Error('invalid video duration')
  }
  return { duration: Math.max(...durations), size: bytes.length }
}
