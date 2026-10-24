import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'
import { finalizeImmutableCandidate, type FinalizeCandidateAdapters } from './video-finalize-core.ts'

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
const VIDEO_PATH = /^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.(mp4|webm)$/
const MAX_BODY_BYTES = 12 * 1024

/**
 * Staged production transport. Publishing is deliberately disabled until
 * immutable Storage identity, ffprobe, atomic DB commit and cleanup exist.
 * This handler performs no Storage or database mutations.
 */
export function createVideoFinalizeHandler(adapters?: FinalizeCandidateAdapters) {
  return async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Cache-Control', 'no-store, private')
  res.setHeader('Vary', 'Authorization')
  res.setHeader('X-Content-Type-Options', 'nosniff')
  if (req.method !== 'POST') return res.status(405).end()
  const authorization = req.headers.authorization
  if (typeof authorization !== 'string' || !/^Bearer [A-Za-z0-9_.-]+$/.test(authorization)) return res.status(401).end()
  const rawLength = req.headers['content-length']
  if (typeof rawLength !== 'string' || !/^[1-9][0-9]{0,4}$/.test(rawLength)) return res.status(413).end()
  const size = Number(rawLength)
  if (!Number.isSafeInteger(size) || size < 1 || size > MAX_BODY_BYTES) return res.status(413).end()
  if (!/^application\/json(?:;\s*charset=utf-8)?$/i.test(String(req.headers['content-type'] || ''))) return res.status(415).end()
  const body: unknown = req.body
  if (!body || typeof body !== 'object' || Array.isArray(body)) return res.status(400).end()
  // Reject inherited fields and exotic prototypes at the HTTP trust boundary.
  if (Object.getPrototypeOf(body) !== Object.prototype && Object.getPrototypeOf(body) !== null) return res.status(400).end()
  const fields = Object.keys(body)
  if (fields.length !== 2 || !fields.includes('object_path') || !fields.includes('content')) return res.status(400).end()
  const { object_path, content } = body as { object_path: unknown; content: unknown }
  if (typeof object_path !== 'string' || typeof content !== 'string' || content.length > 10000) return res.status(400).end()
  if (Buffer.byteLength(JSON.stringify(body), 'utf8') > MAX_BODY_BYTES) return res.status(413).end()
  const match = VIDEO_PATH.exec(object_path)
  if (!match) return res.status(400).end()
  const url = process.env.VITE_SUPABASE_URL
  const anon = process.env.VITE_SUPABASE_ANON_KEY
  if (!url || !anon || !/^https:\/\/[^/]+\/?$/.test(url)) return res.status(503).end()
  try {
    const viewer = createClient(url, anon, {
      global: { headers: { Authorization: authorization } },
      auth: { persistSession: false, autoRefreshToken: false },
    })
    const { data, error } = await viewer.auth.getUser(authorization.slice(7))
    if (error || !data.user || !UUID.test(data.user.id)) return res.status(401).end()
    if (match[1] !== data.user.id) return res.status(403).end()
    // Production remains disabled until immutable Storage fencing and an atomic
    // generation-aware DB RPC are proven. Injected adapters are isolated QA only.
    if (!adapters) return res.status(503).json({ error: 'video_finalize_not_enabled' })
    try {
      const postId = await finalizeImmutableCandidate(authorization.slice(7), object_path, content, {
        ...adapters,
        authenticate: async () => data.user!.id,
      })
      return res.status(201).json({ post_id: postId })
    } catch {
      return res.status(503).json({ error: 'video_finalize_unavailable' })
    }
  } catch {
    return res.status(503).end()
  }
  }
}

export default createVideoFinalizeHandler()
