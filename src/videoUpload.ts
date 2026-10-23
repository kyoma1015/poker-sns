export const MAX_VIDEO_BYTES = 20 * 1024 * 1024
export const MAX_VIDEO_SECONDS = 30
export const VIDEO_TYPES = ['video/mp4', 'video/webm'] as const

export function validateVideoFile(file: Pick<File, 'type' | 'size'>): string | null {
  if (!VIDEO_TYPES.includes(file.type as (typeof VIDEO_TYPES)[number])) return '動画はMP4またはWebM形式にしてください。'
  if (file.size <= 0 || file.size > MAX_VIDEO_BYTES) return '動画は20MB以内にしてください。'
  return null
}

export function validateVideoDuration(seconds: number): string | null {
  if (!Number.isFinite(seconds) || seconds <= 0 || seconds > MAX_VIDEO_SECONDS) return '動画は30秒以内にしてください。'
  return null
}

export function readVideoDuration(file: File): Promise<number> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    const url = URL.createObjectURL(file)
    let finished = false
    const finish = (value?: number) => {
      if (finished) return
      finished = true
      video.removeAttribute('src')
      video.load()
      URL.revokeObjectURL(url)
      if (value === undefined) reject(new Error('動画の長さを確認できませんでした。'))
      else resolve(value)
    }
    video.preload = 'metadata'
    video.onloadedmetadata = () => finish(video.duration)
    video.onerror = () => finish()
    video.src = url
  })
}

export async function validateVideo(file: File): Promise<string | null> {
  const fileError = validateVideoFile(file)
  if (fileError) return fileError
  try { return validateVideoDuration(await readVideoDuration(file)) }
  catch { return '動画の長さを確認できませんでした。' }
}
