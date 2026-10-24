import { createClient } from '@supabase/supabase-js'
import type { FinalizeCandidateAdapters, ImmutableStagedSnapshot } from './video-finalize-core.ts'

/**
 * Server-only candidate. Supabase Storage metadata / ETag alone cannot
 * atomically fence object replacement (ABA). No destructive operation is
 * exposed until an immutable generation and DB transaction are verified.
 */
const UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
const PATH = new RegExp('^(' + UUID + ')/(' + UUID + ')\\.(mp4|webm)$')
const MAX_BYTES = 20 * 1024 * 1024
function owned(owner: string, path: string): boolean {
  const m = PATH.exec(path)
  return Boolean(m && m[1] === owner)
}
export function createSupabaseVideoAdapters(
  url: string,
  anonKey: string,
  serviceRoleKey: string,
): FinalizeCandidateAdapters {
  if (!/^https:\/\/[^/]+\/?$/.test(url) || !anonKey || !serviceRoleKey) {
    throw new Error('missing trusted Supabase configuration')
  }
  const admin = createClient(url, serviceRoleKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  })
  return {
    async authenticate(token) {
      const viewer = createClient(url, anonKey, {
        global: { headers: { Authorization: 'Bearer ' + token } },
        auth: { persistSession: false, autoRefreshToken: false },
      })
      const { data, error } = await viewer.auth.getUser(token)
      if (error || !data.user) throw new Error('unauthorized')
      return data.user.id
    },
    async snapshot(ownerId, objectPath): Promise<ImmutableStagedSnapshot> {
      if (!owned(ownerId, objectPath)) throw new Error('owner mismatch')
      // A successful authenticated Storage download proves access, not
      // immutable generation. Download is read-only and size checked.
      const { data: object, error } = await admin.storage.from('post-videos').download(objectPath)
      if (error || !object || object.size < 1 || object.size > MAX_BYTES) {
        throw new Error('Storage download unavailable or invalid size')
      }
      const bytes = Buffer.from(await object.arrayBuffer())
      if (bytes.byteLength !== object.size || bytes.byteLength > MAX_BYTES) {
        throw new Error('Storage byte length mismatch')
      }
      return { ownerId, objectPath, size: bytes.length, bytes, generation: null }
    },
    async currentGeneration(ownerId, objectPath) {
      if (!owned(ownerId, objectPath)) throw new Error('owner mismatch')
      // HEAD / ETag comparison does not establish an atomic generation fence.
      return null
    },
    async publish(ownerId, objectPath) {
      if (!owned(ownerId, objectPath)) throw new Error('owner mismatch')
      // Explicitly do not invoke unfenced video_qa_publish or a path-only insert.
      throw new Error('generation-fenced publish RPC not available')
    },
    async reconcile(ownerId, objectPath) {
      if (!owned(ownerId, objectPath)) throw new Error('owner mismatch')
      // The isolated video_qa_reconcile RPC is NOT a production contract.
      // Returning a path-only match would misidentify a replaced generation.
      return null
    },
  }
}
