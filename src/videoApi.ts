import { supabase } from './supabase'

/** Candidate client/server contract. Not enabled until a trusted endpoint is reviewed. */
export const VIDEO_FINALIZE_ROUTE = '/internal/video/finalize'
export const VIDEO_MEDIA_ROUTE = '/internal/video/media'
// Build-time feature gate: keep disabled until production DB, runtime and API smoke QA pass.
// Never infer readiness from the presence of Supabase credentials.
export const VIDEO_SERVER_ENABLED = import.meta.env.VITE_VIDEO_SERVER_ENABLED === 'true'

async function authHeader(): Promise<string> {
  const { data: { session }, error } = await supabase.auth.getSession()
  if (error || !session?.access_token) throw new Error('再ログインしてください。')
  return `Bearer ${session.access_token}`
}

export async function finalizeUploadedVideo(objectPath: string, content: string): Promise<string> {
  if (!VIDEO_SERVER_ENABLED) throw new Error('動画投稿はサーバーAPIの安全確認待ちです。')
  const response = await fetch(VIDEO_FINALIZE_ROUTE, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: await authHeader() },
    cache: 'no-store', body: JSON.stringify({ object_path: objectPath, content }),
  })
  if (!response.ok) throw new Error('動画投稿を確定できませんでした。')
  const payload: unknown = await response.json()
  if (!payload || typeof payload !== 'object' || !('post_id' in payload) ||
      typeof payload.post_id !== 'string' || !/^[0-9a-f-]{36}$/i.test(payload.post_id)) {
    throw new Error('動画投稿の応答が不正です。')
  }
  return payload.post_id
}

/** Reserve an object path before ANY Storage write. The server is the sole
 * trusted caller of the permanent-key ledger. Never retry a rejected key. */
export async function reserveVideoObjectPath(objectPath: string): Promise<void> {
  if (!VIDEO_SERVER_ENABLED) throw new Error('動画投稿はサーバーAPIの安全確認待ちです。')
  const response = await fetch(VIDEO_FINALIZE_ROUTE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: await authHeader() },
    cache: 'no-store',
    body: JSON.stringify({ action: 'reserve', object_path: objectPath }),
  })
  if (!response.ok) throw new Error('動画の保存先を安全に確保できませんでした。')
  const payload: unknown = await response.json()
  if (!payload || typeof payload !== 'object' || !('reserved' in payload) || payload.reserved !== true) {
    throw new Error('動画保存先の予約応答が不正です。')
  }
}

/** Requires server-side JWT/RLS check per request; never uses a signed URL. */
export async function loadAuthorizedVideo(postId: string): Promise<string> {
  if (!VIDEO_SERVER_ENABLED) throw new Error('動画再生APIは安全確認待ちです。')
  if (!/^[0-9a-f-]{36}$/i.test(postId)) throw new Error('投稿IDが不正です。')
  const response = await fetch(`${VIDEO_MEDIA_ROUTE}/${encodeURIComponent(postId)}`, {
    headers: { Authorization: await authHeader() }, cache: 'no-store',
  })
  if (!response.ok) throw new Error('動画を読み込めませんでした。')
  const blob = await response.blob()
  if (!blob.size || blob.size > 20 * 1024 * 1024 || !['video/mp4', 'video/webm'].includes(blob.type)) {
    throw new Error('動画データが不正です。')
  }
  return URL.createObjectURL(blob)
}
