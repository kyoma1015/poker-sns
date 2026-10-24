import { createClient } from '@supabase/supabase-js'
import type { FinalizeCandidateAdapters, ImmutableStagedSnapshot } from './video-finalize-core.ts'
import { MAX_VIDEO_BYTES } from './video-ffprobe.ts'

/**
 * Server-only Supabase adapter candidate. Intentionally never grants a
 * generation token: Storage list/HEAD/ETag is NOT a version-pinned read,
 * and cannot prevent ABA swaps. No service-role writes or deletes.
 */
export function createSupabaseVideoAdapters(
  url: string,
  anonKey: string,
  serviceRoleKey: string,
): FinalizeCandidateAdapters {
  if (!/^https:\/\/[^/]+\/?$/.test(url) || !anonKey || !serviceRoleKey) {
    throw new Error('missing trusted Supabase configuration')
  }
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
      if (!objectPath.startsWith(ownerId + '/')) throw new Error('owner mismatch')
      // A Storage listing is insufficient to prove immutability or ownership.
      // Never download by mutable path before the object is version-fenced.
      throw new Error('immutable Storage snapshot API unavailable')
    },
    async currentGeneration() {
      // Never substitute an ETag or a list result for a locked generation.
      return null
    },
    async publish() {
      // No production RPC with an atomic generation fence has been approved.
      throw new Error('atomic generation-aware publish RPC unavailable')
    },
    async reconcile(ownerId, objectPath) {
      if (!objectPath.startsWith(ownerId + '/')) throw new Error('owner mismatch')
      // Read-only, but cannot prove a specific immutable generation yet.
      // Preserve the object and surface an uncertain commit outcome.
      return null
    },
  }
}

export { MAX_VIDEO_BYTES }
