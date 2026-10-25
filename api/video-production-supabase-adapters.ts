import { DefinitivePublishRejection } from './video-finalize-core.js'
import { createClient } from '@supabase/supabase-js'
import type { FinalizeCandidateAdapters, ImmutableStagedSnapshot } from './video-finalize-core.js'
import { MAX_VIDEO_BYTES } from './video-ffprobe.js'

const UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
const PATH = new RegExp('^(' + UUID + ')/(' + UUID + ')\\.(mp4|webm)$')
const PRODUCTION_URL = /^https:\/\/[a-z0-9-]+\.supabase\.co\/?$/

/** Production candidate: disabled until the audited production migration and runtime preflight pass. No Storage deletion. */
export function createProductionSupabaseVideoAdapters(
  url: string, anonKey: string, serviceRoleKey: string, accessToken: string,
): FinalizeCandidateAdapters {
  if (!PRODUCTION_URL.test(url) || !anonKey || !serviceRoleKey || !accessToken || process.env.VIDEO_PRODUCTION_FENCED_READY !== 'true') {
    throw new Error('production video fenced release gate disabled')
  }
  const ownerPath = (owner: string, path: string) => {
    const match = PATH.exec(path)
    if (!match || match[1] !== owner) throw new Error('owner/path mismatch')
  }
  const viewer = createClient(url, anonKey, {
    global: { headers: { Authorization: 'Bearer ' + accessToken } },
    auth: { persistSession: false, autoRefreshToken: false },
  })
  const admin = createClient(url, serviceRoleKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  })
  const authenticate = async (token: string) => {
    if (token !== accessToken) throw new Error('JWT differs from request-scoped token')
    const { data, error } = await viewer.auth.getUser(token)
    if (error || !data.user || !new RegExp('^' + UUID + '$').test(data.user.id)) throw new Error('unauthorized')
    return data.user.id
  }
  // Privileged metadata is never authorization: authenticate and read as viewer first.
  const metadata = async (owner: string, path: string) => {
    ownerPath(owner, path)
    // storage schema is not exposed through PostgREST by default. Use a
    // narrowly scoped trusted RPC, not an unrestricted storage schema grant.
    const { data, error } = await admin.rpc('video_production_storage_generation', {
      p_owner: owner, p_path: path,
    })
    if (error || typeof data !== 'string' || data.length !== 36) {
      throw new Error('immutable Storage identity unavailable')
    }
    return data
  }
  return {
    authenticate,
    async snapshot(ownerId, path): Promise<ImmutableStagedSnapshot> {
      ownerPath(ownerId, path)
      if (await authenticate(accessToken) !== ownerId) throw new Error('unauthorized owner')
      const generation = await metadata(ownerId, path)
      // Bounded HTTP stream: SDK .download() materializes a Blob before a
      // size check, so it cannot enforce a strict 20 MiB receive cap.
      const response = await fetch((url.endsWith('/') ? url.slice(0, -1) : url) +
        '/storage/v1/object/authenticated/post-videos/' + path, {
        headers: { apikey: anonKey, Authorization: 'Bearer ' + accessToken },
        signal: AbortSignal.timeout(30000),
      })
      if (!response.ok || !response.body) throw new Error('private Storage read denied')
      const declared = response.headers.get('content-length')
      if (declared && (!Number.isSafeInteger(Number(declared)) || Number(declared) < 0 || Number(declared) > MAX_VIDEO_BYTES)) {
        await response.body.cancel()
        throw new Error('media exceeds 20 MiB')
      }
      const chunks: Buffer[] = []
      let received = 0
      const reader = response.body.getReader()
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          received += value.byteLength
          if (received > MAX_VIDEO_BYTES) throw new Error('media exceeds 20 MiB')
          chunks.push(Buffer.from(value))
        }
      } finally {
        await reader.cancel().catch(() => undefined)
      }
      if (received === 0 || (declared && received !== Number(declared))) {
        throw new Error('incomplete Storage object')
      }
      const bytes = Buffer.concat(chunks, received)
      if (generation !== await metadata(ownerId, path)) throw new Error('Storage generation changed during read')
      return { ownerId, objectPath: path, generation, size: bytes.length, bytes }
    },
    async currentGeneration(ownerId, path) {
      if (await authenticate(accessToken) !== ownerId) throw new Error('unauthorized owner')
      return metadata(ownerId, path)
    },
    async publish(ownerId, path, generation, sha256, duration, content) {
      if (await authenticate(accessToken) !== ownerId) throw new Error('unauthorized owner')
      ownerPath(ownerId, path)
      const { data, error } = await admin.rpc('video_production_publish_fenced', {
        p_owner: ownerId, p_path: path, p_generation: generation,
        p_sha256: sha256, p_duration: duration, p_content: content,
      })
      if (error?.code === 'P0001' && /conflicting prior video publication|Storage generation mismatch|invalid fenced publication/.test(error.message)) {
        throw new DefinitivePublishRejection('fenced publication rejected')
      }
      if (error || typeof data !== 'string') throw new Error('fenced publish outcome unknown')
      return data
    },
    async reconcile(ownerId, path, generation, sha256, duration, content) {
      if (await authenticate(accessToken) !== ownerId) throw new Error('unauthorized owner')
      ownerPath(ownerId, path)
      const { data, error } = await admin.rpc('video_production_reconcile_fenced', {
        p_owner: ownerId, p_path: path, p_generation: generation,
      })
      if (error || (data !== null && typeof data !== 'string')) throw new Error('reconciliation unavailable')
      if (!data) return null
      if (!sha256 || duration === undefined || content === undefined) return null
      const { data: post, error: readError } = await admin.from('posts')
        .select('id,user_id,video_path,video_generation,video_sha256,video_duration_seconds,content')
        .eq('id', data).maybeSingle()
      if (readError || !post) throw new Error('reconciliation fingerprint unavailable')
      if (post.user_id !== ownerId || post.video_path !== path ||
          post.video_generation !== generation || post.video_sha256 !== sha256 ||
          post.video_duration_seconds !== duration || post.content !== content) {
        throw new DefinitivePublishRejection('reconciled post content differs from request')
      }
      return data
    },
  }
}

