import { assertCurrentVideoCloudTestClient } from './videoCloudTestGuard'
import { supabase } from './supabase'
import { readVideoResponse } from './videoMedia'

/** Candidate client/server contract. Not enabled until a trusted endpoint is reviewed. */
export const VIDEO_FINALIZE_ROUTE = '/internal/video/finalize'
export const VIDEO_MEDIA_ROUTE = '/internal/video/media'
const POST_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
// Build-time feature gate: keep disabled until production DB, runtime and API smoke QA pass.
// Never infer readiness from the presence of Supabase credentials.
export const VIDEO_SERVER_ENABLED = import.meta.env.VITE_VIDEO_SERVER_ENABLED === 'true' || import.meta.env.VITE_VIDEO_CLOUD_TEST_ENABLED === 'true'

async function authHeader(signal?: AbortSignal): Promise<string> {
  const { data: { session }, error } = await supabase.auth.getSession()
  signal?.throwIfAborted()
  if (error || !session?.access_token) throw new Error('再ログインしてください。')
  return `Bearer ${session.access_token}`
}

export async function finalizeUploadedVideo(objectPath: string, content: string, signal?: AbortSignal): Promise<string> {
  assertCurrentVideoCloudTestClient()
  if (!VIDEO_SERVER_ENABLED) throw new Error('動画投稿はサーバーAPIの安全確認待ちです。')
  const response = await fetch(VIDEO_FINALIZE_ROUTE, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: await authHeader(signal) },
    redirect: 'error', signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(30000)]) : AbortSignal.timeout(30000),
    cache: 'no-store', body: JSON.stringify({ object_path: objectPath, content }),
  })
  if (!response.ok) throw new Error('動画投稿を確定できませんでした。')
  const payload: unknown = await response.json()
  if (!payload || typeof payload !== 'object' || !('post_id' in payload) ||
      typeof payload.post_id !== 'string' || !POST_UUID.test(payload.post_id)) {
    throw new Error('動画投稿の応答が不正です。')
  }
  return payload.post_id
}

/** Recovery reuses the existing reserved private object; no Storage upload or new key. */
export async function recoverCloudVideo(objectPath: string): Promise<string> {
  assertCurrentVideoCloudTestClient()
  if (import.meta.env.VITE_VIDEO_CLOUD_TEST_ENABLED !== 'true') throw new Error('テスト環境以外では復旧できません。')
  const response = await fetch(VIDEO_FINALIZE_ROUTE, {
    method: 'POST',
    headers: { 'Content-Type':'application/json', Authorization: await authHeader() },
    body: JSON.stringify({action:'recover',object_path:objectPath}),
    redirect:'error',cache:'no-store',signal:AbortSignal.timeout(30000),
  })
  if (!response.ok) {
    const details: unknown = await response.json().catch(()=>null)
    const stage = details && typeof details==='object' && 'stage' in details && typeof details.stage==='string'
      && /^(configuration|authentication|reservation_state|storage_fetch|storage_download|ffprobe_validation|attestation_key|publish_rpc)$/.test(details.stage) ? details.stage : 'unknown'
    throw new Error('既存動画の確定に失敗しました（段階: '+stage+'、HTTP '+response.status+'）。')
  }
  const data: unknown = await response.json()
  if (!data || typeof data !== 'object' || !('post_id' in data) ||
    typeof data.post_id !== 'string' || !POST_UUID.test(data.post_id)) throw new Error('復旧結果が不正です。')
  return data.post_id
}

/** Reserve an object path before ANY Storage write. The server is the sole
 * trusted caller of the permanent-key ledger. Never retry a rejected key. */
export async function reserveVideoObjectPath(objectPath: string, signal?: AbortSignal, manifest?: {sha256:string;size:number;type:string;content:string}): Promise<void> {
  assertCurrentVideoCloudTestClient()
  if (!VIDEO_SERVER_ENABLED) throw new Error('動画投稿はサーバーAPIの安全確認待ちです。')
  const response = await fetch(VIDEO_FINALIZE_ROUTE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: await authHeader(signal) },
    redirect: 'error', signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(30000)]) : AbortSignal.timeout(30000),
    cache: 'no-store',
    body: JSON.stringify({ action: 'reserve', object_path: objectPath, ...(import.meta.env.VITE_VIDEO_CLOUD_TEST_ENABLED === 'true' ? manifest : {}) }),
  })
  if (!response.ok) throw new Error('動画の保存先を安全に確保できませんでした。')
  const payload: unknown = await response.json()
  if (!payload || typeof payload !== 'object' || !('reserved' in payload) || payload.reserved !== true) {
    throw new Error('動画保存先の予約応答が不正です。')
  }
}

/** Requires server-side JWT/RLS check per request; never uses a signed URL. */
export async function loadAuthorizedVideo(postId: string): Promise<string> {
  assertCurrentVideoCloudTestClient()
  if (!VIDEO_SERVER_ENABLED) throw new Error('動画再生APIは安全確認待ちです。')
  if (!POST_UUID.test(postId)) throw new Error('投稿IDが不正です。')
  const response = await fetch(`${VIDEO_MEDIA_ROUTE}/${encodeURIComponent(postId)}`, {
    headers: { Authorization: await authHeader() }, cache: 'no-store',
    redirect: 'error', signal: AbortSignal.timeout(30000),
  })
  const blob = await readVideoResponse(response)
  return URL.createObjectURL(blob)
}


/** Hide the post through owner-scoped RPC; never delete Storage bytes. */
export async function hideVideoPost(postId: string): Promise<void> {
  if (!VIDEO_SERVER_ENABLED || !POST_UUID.test(postId)) throw new Error('動画の非表示を実行できません。')
  const response = await fetch(VIDEO_FINALIZE_ROUTE, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: await authHeader() },
    redirect: 'error', cache: 'no-store', signal: AbortSignal.timeout(30000),
    body: JSON.stringify({ action: 'hide', post_id: postId }),
  })
  const result: unknown = await response.json().catch(() => null)
  if (!response.ok || !result || typeof result !== 'object' || !('hidden' in result) || result.hidden !== true) throw new Error('動画を非表示にできませんでした。')
}
