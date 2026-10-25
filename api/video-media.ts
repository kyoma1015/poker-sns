import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
const VIDEO_PATH = /^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.(mp4|webm)$/
const MAX_BYTES = 20 * 1024 * 1024

/** Candidate Vercel route: no public URLs, no redirect, and no Storage mutation. */
export function createVideoMediaHandler(options: { isolatedLocalOnly?: boolean } = {}) {
return async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Cache-Control', 'private, no-store, no-cache, max-age=0, must-revalidate')
  res.setHeader('Pragma', 'no-cache')
  res.setHeader('Expires', '0')
  res.setHeader('Vary', 'Authorization')
  res.setHeader('X-Content-Type-Options', 'nosniff')
  res.setHeader('Content-Security-Policy', "default-src 'none'; sandbox")
  res.setHeader('Cross-Origin-Resource-Policy', 'same-origin')
  if (req.method !== 'GET') return res.status(405).end()
  const rawAuth = req.headers.authorization
  if (!rawAuth || !/^Bearer [A-Za-z0-9_.-]+$/.test(rawAuth)) return res.status(401).end()
  const rawId = req.query.post_id
  if (typeof rawId !== 'string' || !UUID.test(rawId)) return res.status(400).end()
  const url = process.env.VITE_SUPABASE_URL
  const anon = process.env.VITE_SUPABASE_ANON_KEY
  if (!url || !anon || !(/^https:\/\/[^/]+\/?$/.test(url) ||
    (options.isolatedLocalOnly === true && url === 'http://127.0.0.1:56321'))) return res.status(503).end()
  // Keep media disabled until the same audited production fence as finalize.
  // Isolated tests may opt into their explicit local-only transport.
  if (options.isolatedLocalOnly !== true &&
      (!/^https:\/\/[a-z0-9-]+\.supabase\.co\/?$/.test(url) ||
       process.env.VIDEO_PRODUCTION_FENCED_READY !== 'true')) {
    return res.status(503).end()
  }
  const token = rawAuth.slice(7)
  const viewer = createClient(url, anon, {
    global: { headers: { Authorization: rawAuth } },
    auth: { persistSession: false, autoRefreshToken: false },
  })
  try {
    const { data: identity, error: authError } = await viewer.auth.getUser(token)
    if (authError || !identity.user || !UUID.test(identity.user.id)) return res.status(401).end()
    const visible = async () => {
      const { data, error } = await viewer.from('posts')
        .select('user_id,video_path').eq('id', rawId).maybeSingle()
      if (error) throw error
      // Existing posts SELECT RLS is the visibility authority. Do not require
      // is_public: that column does not exist in the production posts schema.
      if (!data) return null
      const match = typeof data.video_path === 'string' ? VIDEO_PATH.exec(data.video_path) : null
      if (!match || match[1] !== data.user_id) return null
      return data.video_path as string
    }
    const path = await visible()
    if (!path) return res.status(404).end()
    // Bound storage fetch and response processing to reduce resource exhaustion.
    // Stream from the private bucket through a bounded trusted-server read.
    // The Storage SDK's download() would buffer an unbounded Blob first.
    const media = await fetch((url.endsWith('/') ? url.slice(0, -1) : url) +
      '/storage/v1/object/authenticated/post-videos/' + path, {
      headers: { apikey: anon, Authorization: rawAuth },
      signal: AbortSignal.timeout(30000),
    })
    if (!media.ok || !media.body) return res.status(503).end()
    const declared = media.headers.get('content-length')
    if (declared && (!Number.isSafeInteger(Number(declared)) ||
      Number(declared) < 1 || Number(declared) > MAX_BYTES)) {
      await media.body.cancel()
      return res.status(503).end()
    }
    const chunks: Buffer[] = []
    let received = 0
    const reader = media.body.getReader()
    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        received += value.byteLength
        if (received > MAX_BYTES) throw new Error('oversized media')
        chunks.push(Buffer.from(value))
      }
    } finally {
      await reader.cancel().catch(() => undefined)
    }
    if (!received || (declared && Number(declared) !== received)) return res.status(503).end()
    const bytes = Buffer.concat(chunks, received)
    // Re-check RLS and identity before returning any media bytes.
    const { data: refreshed, error: refreshedError } = await viewer.auth.getUser(token)
    if (refreshedError || refreshed.user?.id !== identity.user.id || await visible() !== path) {
      return res.status(403).end()
    }
    // A second authorization check closes the gap between async byte materialization and response.
    const { data: finalIdentity, error: finalAuthError } = await viewer.auth.getUser(token)
    if (finalAuthError || finalIdentity.user?.id !== identity.user.id || await visible() !== path) {
      return res.status(403).end()
    }
    if (bytes.byteLength === 0 || bytes.byteLength > MAX_BYTES) return res.status(503).end()
    res.setHeader('Content-Type', path.endsWith('.mp4') ? 'video/mp4' : 'video/webm')
    res.setHeader('Content-Length', String(bytes.byteLength))
    return res.status(200).send(bytes)
  } catch {
    return res.status(503).end()
  }
}
}

export default createVideoMediaHandler()
