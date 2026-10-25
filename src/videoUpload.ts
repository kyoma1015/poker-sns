import { supabase } from './supabase'

export const MAX_VIDEO_BYTES = 20 * 1024 * 1024
export const MAX_VIDEO_SECONDS = 30
export const VIDEO_TYPES = ['video/mp4', 'video/webm'] as const
export const VIDEO_BUCKET = 'post-videos'

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
    // A corrupt container can neither emit loadedmetadata nor error.
    // Bound the pending Promise and release the object URL on timeout.
    const timeout = window.setTimeout(() => finish(), 15000)
    const finish = (value?: number) => {
      if (finished) return
      finished = true
      window.clearTimeout(timeout)
      video.onloadedmetadata = null
      video.onerror = null
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

/** Staged only: caller must enforce server-side duration and reviewed RLS before enabling. */
export async function uploadPostVideo(userId: string, file: File): Promise<string> {
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user || user.id !== userId) throw new Error('ログイン情報を確認してください。')
  const validationError = await validateVideo(file)
  if (validationError) throw new Error(validationError)
  const ext = file.type === 'video/mp4' ? 'mp4' : 'webm'
  const path = `${user.id}/${crypto.randomUUID()}.${ext}`
  const { error } = await supabase.storage.from(VIDEO_BUCKET).upload(path, file, { contentType: file.type, upsert: false })
  if (error) throw error
  return path
}

/** Reject path traversal, extra segments and mismatched owners. */
export function isOwnedVideoPath(path: string, userId: string): boolean {
  return /^[0-9a-f-]{36}\/[0-9a-f-]{36}\.(mp4|webm)$/i.test(path) && path.split('/')[0] === userId
}

/** Fail closed: Storage remove(path) cannot guarantee version-fenced deletion. */
export async function removePostVideo(userId: string, path: string): Promise<void> {
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user || user.id !== userId) throw new Error('ログイン情報を確認してください。')
  if (!isOwnedVideoPath(path, user.id)) throw new Error('動画パスの権限を確認できません。')
  throw new Error('動画ファイルの削除は安全な条件付き削除が実装されるまで停止しています。')
}

/** Direct Storage signed URLs bypass per-view JWT/RLS checks. Never issue them. */
export async function createPostVideoPlaybackUrl(_path: string): Promise<string> {
  throw new Error('動画再生には認証済みの投稿IDと専用media APIを使用してください。')
}
