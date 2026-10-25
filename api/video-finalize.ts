import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'
import { spawn } from 'node:child_process'
import { isAbsolute, join } from 'node:path'
import { finalizeImmutableCandidate, type FinalizeCandidateAdapters } from './video-finalize-core.js'
import { createProductionSupabaseVideoAdapters } from './video-production-supabase-adapters.js'

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
const VIDEO_PATH = /^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.(mp4|webm)$/
const MAX_BODY_BYTES = 12 * 1024

/**
 * Staged production transport. Publishing is deliberately disabled until
 * immutable Storage identity, ffprobe, atomic DB commit and cleanup exist.
 * This handler performs no Storage or database mutations.
 */
export function createVideoFinalizeHandler(adapters?: FinalizeCandidateAdapters, options: { isolatedLocalOnly?: boolean } = {}) {
  return async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Cache-Control', 'no-store, private')
  res.setHeader('Vary', 'Authorization')
  res.setHeader('X-Content-Type-Options', 'nosniff')
  // Preview-only runtime attestation, sharing this existing serverless function.
  // No new Vercel function or production endpoint is required.
  if (req.method === 'GET' && req.query?.runtime_attestation === 'ffprobe') {
    if (process.env.VERCEL_ENV !== 'preview') return res.status(404).end()
    const executable = process.env.FFPROBE_BINARY_PATH || join(process.cwd(), 'api', 'bin', 'ffprobe')
    if (!isAbsolute(executable)) return res.status(503).json({ ffprobe: 'unconfigured' })
    const ok = await new Promise<boolean>(resolve => {
      const child = spawn(executable, ['-version'], { stdio: 'ignore', shell: false })
      let settled = false
      const done = (value: boolean) => {
        if (settled) return
        settled = true
        clearTimeout(timeout)
        resolve(value)
      }
      const timeout = setTimeout(() => { child.kill(); done(false) }, 5000)
      child.on('error', () => done(false))
      child.on('close', code => done(code === 0))
    })
    return res.status(ok ? 200 : 503).json({ ffprobe: ok ? 'executable' : 'unavailable' })
  }
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
  // Reservation shares the existing serverless function (Hobby function cap).
  // Only trusted service_role can invoke the append-only permanent ledger.
  // A failed or ambiguous reservation is never treated as success.
  if (Object.keys(body).length === 2 &&
      (body as Record<string, unknown>).action === 'reserve' &&
      typeof (body as Record<string, unknown>).object_path === 'string') {
    const path = (body as Record<string, unknown>).object_path as string
    const match = VIDEO_PATH.exec(path)
    if (!match) return res.status(400).end()
    const url = process.env.VITE_SUPABASE_URL
    const anon = process.env.VITE_SUPABASE_ANON_KEY
    const service = process.env.SUPABASE_SERVICE_ROLE_KEY
    // Production release requires a separately audited Storage writer fence.
    // Isolated local QA may reserve against its disposable ledger only.
    const isolatedReservation = options.isolatedLocalOnly === true && url === 'http://127.0.0.1:56321'
    const host = url?.startsWith('https://') ? url.slice(8).split('/')[0] : ''
    if ((!isolatedReservation && (process.env.VIDEO_PRODUCTION_FENCED_READY !== 'true' ||
        !/^[a-z0-9-]+[.]supabase[.]co$/.test(host))) ||
        !anon || !service) return res.status(503).json({ error: 'video_reservation_not_enabled' })
    try {
      const viewer = createClient(url, anon, {
        global: { headers: { Authorization: authorization } },
        auth: { persistSession: false, autoRefreshToken: false },
      })
      const token = authorization.slice(7)
      const { data, error } = await viewer.auth.getUser(token)
      if (error || !data.user || !UUID.test(data.user.id)) return res.status(401).end()
      if (data.user.id !== match[1]) return res.status(403).end()
      const admin = createClient(url, service, {
        auth: { persistSession: false, autoRefreshToken: false },
      })
      // Reauthenticate immediately before committing a permanent reservation.
      // A token revoked while the trusted RPC client was being constructed
      // must not reserve a key for an invalid session.
      const { data: fresh, error: freshError } = await viewer.auth.getUser(token)
      if (freshError || fresh.user?.id !== data.user.id) return res.status(401).end()
      const { data: reservation, error: reservationError } = await admin.rpc('video_reserve_object_key', {
        p_owner: data.user.id, p_path: path,
      })
      if (reservationError || typeof reservation !== 'string' || !UUID.test(reservation)) {
        return res.status(503).json({ error: 'video_reservation_unavailable' })
      }
      return res.status(201).json({ reserved: true })
    } catch {
      return res.status(503).json({ error: 'video_reservation_unavailable' })
    }
  }
  const fields = Object.keys(body)
  if (fields.length !== 2 || !fields.includes('object_path') || !fields.includes('content')) return res.status(400).end()
  const { object_path, content } = body as { object_path: unknown; content: unknown }
  if (typeof object_path !== 'string' || typeof content !== 'string' || content.length > 10000) return res.status(400).end()
  if (Buffer.byteLength(JSON.stringify(body), 'utf8') > MAX_BODY_BYTES) return res.status(413).end()
  const match = VIDEO_PATH.exec(object_path)
  if (!match) return res.status(400).end()
  const url = process.env.VITE_SUPABASE_URL
  const anon = process.env.VITE_SUPABASE_ANON_KEY
  if (!url || !anon || !(/^https:\/\/[^/]+\/?$/.test(url) ||
    (options.isolatedLocalOnly === true && url === 'http://127.0.0.1:56321'))) return res.status(503).end()
  const isolated = options.isolatedLocalOnly === true && url === 'http://127.0.0.1:56321'
  const production = options.isolatedLocalOnly !== true &&
    /^https:\/\/[a-z0-9-]+\.supabase\.co\/?$/.test(url) &&
    process.env.VIDEO_PRODUCTION_FENCED_READY === 'true'
  if (!isolated && !production) return res.status(503).json({ error: 'video_finalize_not_enabled' })
  if (adapters && !isolated) return res.status(503).json({ error: 'video_finalize_not_enabled' })
  try {
    const viewer = createClient(url, anon, {
      global: { headers: { Authorization: authorization } },
      auth: { persistSession: false, autoRefreshToken: false },
    })
    const { data, error } = await viewer.auth.getUser(authorization.slice(7))
    if (error || !data.user || !UUID.test(data.user.id)) return res.status(401).end()
    if (match[1] !== data.user.id) return res.status(403).end()
    let activeAdapters: FinalizeCandidateAdapters
    try {
      if (isolated) {
        if (!adapters) return res.status(503).json({ error: 'video_finalize_not_enabled' })
        activeAdapters = adapters
      } else {
        const service = process.env.SUPABASE_SERVICE_ROLE_KEY
        if (!service) return res.status(503).json({ error: 'video_finalize_not_enabled' })
        activeAdapters = createProductionSupabaseVideoAdapters(url, anon, service, authorization.slice(7))
      }
    } catch {
      return res.status(503).json({ error: 'video_finalize_not_enabled' })
    }
    try {
      // Preserve the adapter's live authentication callback. Replacing it with
      // the identity captured above would let a revoked token pass the core's
      // post-ffprobe authorization recheck.
      const postId = await finalizeImmutableCandidate(
        authorization.slice(7), object_path, content, activeAdapters,
      )
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
