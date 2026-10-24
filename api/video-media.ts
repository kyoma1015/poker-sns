import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
const VIDEO_PATH = /^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.(mp4|webm)$/
const MAX_BYTES = 20 * 1024 * 1024

/** Candidate Vercel route: no public URLs, no redirect, and no Storage mutation. */
export default async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Cache-Control', 'no-store, private')
  res.setHeader('Vary', 'Authorization')
  res.setHeader('X-Content-Type-Options', 'nosniff')
  if (req.method !== 'GET') return res.status(405).end()
  const rawAuth = req.headers.authorization
  if (!rawAuth || !/^Bearer [A-Za-z0-9_.-]+$/.test(rawAuth)) return res.status(401).end()
  const rawId = req.query.post_id
  if (typeof rawId !== 'string' || !UUID.test(rawId)) return res.status(400).end()
  const url = process.env.VITE_SUPABASE_URL
  const anon = process.env.VITE_SUPABASE_ANON_KEY
  const service = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !anon || !service || !url.startsWith('https://')) return res.status(503).end()
  const token = rawAuth.slice(7)
  const viewer = createClient(url, anon, {
    global: { headers: { Authorization: rawAuth } },
    auth: { persistSession: false, autoRefreshToken: false },
  })
  const admin = createClient(url, service, {
    auth: { persistSession: false, autoRefreshToken: false },
  })
  try {
    const { data: identity, error: authError } = await viewer.auth.getUser(token)
    if (authError || !identity.user || !UUID.test(identity.user.id)) return res.status(401).end()
    const visible = async () => {
      const { data, error } = await viewer.from('posts')
        .select('user_id,video_path,is_public').eq('id', rawId).maybeSingle()
      if (error) throw error
      if (!data || (data.user_id !== identity.user!.id && data.is_public !== true)) return null
      const match = typeof data.video_path === 'string' ? VIDEO_PATH.exec(data.video_path) : null
      if (!match || match[1] !== data.user_id) return null
      return data.video_path as string
    }
    const path = await visible()
    if (!path) return res.status(404).end()
    const { data: blob, error: storageError } = await admin.storage.from('post-videos').download(path)
    if (storageError || !blob || blob.size === 0 || blob.size > MAX_BYTES) return res.status(503).end()
    // Re-check RLS and identity before returning any media bytes.
    const { data: refreshed, error: refreshedError } = await viewer.auth.getUser(token)
    if (refreshedError || refreshed.user?.id !== identity.user.id || await visible() !== path) {
      return res.status(403).end()
    }
    const bytes = Buffer.from(await blob.arrayBuffer())
    if (bytes.byteLength === 0 || bytes.byteLength > MAX_BYTES) return res.status(503).end()
    res.setHeader('Content-Type', path.endsWith('.mp4') ? 'video/mp4' : 'video/webm')
    res.setHeader('Content-Length', String(bytes.byteLength))
    return res.status(200).send(bytes)
  } catch {
    return res.status(503).end()
  }
}
