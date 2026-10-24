import { createClient } from '@supabase/supabase-js'
import type { FinalizeCandidateAdapters, ImmutableStagedSnapshot } from './video-finalize-core.ts'
import { MAX_VIDEO_BYTES } from './video-ffprobe.ts'

const UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
const PATH = new RegExp('^(' + UUID + ')/(' + UUID + ')\\.(mp4|webm)$')
const ISOLATED = /^http:\/\/127\.0\.0\.1:56321\/?$/

/**
 * Trusted-server candidate for a disposable local Supabase stack ONLY.
 * Requires isolated RPC video_qa_publish_fenced and video_qa_reconcile_fenced.
 * The SQL RPC must atomically check storage.objects.id under a row lock.
 * No production configuration, no path-only publishing and no deletion.
 */
export function createIsolatedSupabaseVideoAdapters(
  url: string, anonKey: string, serviceRoleKey: string, accessToken: string,
): FinalizeCandidateAdapters {
  if (!ISOLATED.test(url) || !anonKey || !serviceRoleKey || !accessToken) {
    throw new Error('isolated Supabase configuration required')
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
    const { data, error } = await admin.schema('storage').from('objects')
      .select('id,owner_id,name,bucket_id').eq('bucket_id', 'post-videos').eq('name', path).maybeSingle()
    if (error || !data || data.owner_id !== owner || data.name !== path ||
        typeof data.id !== 'string' || !new RegExp('^' + UUID + '$').test(data.id)) {
      throw new Error('immutable Storage identity unavailable')
    }
    return data.id as string
  }
  return {
    authenticate,
    async snapshot(ownerId, path): Promise<ImmutableStagedSnapshot> {
      if (await authenticate(accessToken) !== ownerId) throw new Error('unauthorized owner')
      ownerPath(ownerId, path)
      const generation = await metadata(ownerId, path)
      const { data, error } = await viewer.storage.from('post-videos').download(path)
      if (error || !data || data.size <= 0 || data.size > MAX_VIDEO_BYTES) {
        throw new Error('private Storage read unavailable or size invalid')
      }
      const bytes = Buffer.from(await data.arrayBuffer())
      if (bytes.length !== data.size || bytes.length > MAX_VIDEO_BYTES) throw new Error('invalid media bytes')
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
      const { data, error } = await admin.rpc('video_qa_publish_fenced', {
        p_owner: ownerId, p_path: path, p_generation: generation,
        p_sha256: sha256, p_duration: duration, p_content: content,
      })
      if (error || typeof data !== 'string') throw new Error('fenced publish outcome unknown')
      return data
    },
    async reconcile(ownerId, path, generation) {
      if (await authenticate(accessToken) !== ownerId) throw new Error('unauthorized owner')
      ownerPath(ownerId, path)
      const { data, error } = await admin.rpc('video_qa_reconcile_fenced', {
        p_owner: ownerId, p_path: path, p_generation: generation,
      })
      if (error || (data !== null && typeof data !== 'string')) throw new Error('reconciliation unavailable')
      return data
    },
  }
}
