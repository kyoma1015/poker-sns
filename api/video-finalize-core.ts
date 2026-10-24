import { inspectStagedVideo, requireImmutableGeneration } from './video-preflight.ts'
import type { VideoExtension } from './video-ffprobe.ts'

/** A confirmed RPC rejection is not an ambiguous commit and must never reconcile to an older post. */
export class DefinitivePublishRejection extends Error {}

export type ImmutableStagedSnapshot = {
  ownerId: string
  objectPath: string
  generation: string | null
  size: number
  bytes: Buffer
}

export type FinalizeCandidateAdapters = {
  /** MUST be verified by Supabase Auth, never read from the HTTP body. */
  authenticate(token: string): Promise<string>
  /** MUST read an immutable, version-pinned Storage object. */
  snapshot(ownerId: string, path: string): Promise<ImmutableStagedSnapshot>
  /** MUST recheck the SAME immutable object generation. */
  currentGeneration(ownerId: string, path: string): Promise<string | null>
  /** MUST atomically fence generation and publish once. No path-only insert. */
  publish(ownerId: string, path: string, generation: string, sha256: string, duration: number, content: string): Promise<string>
  /** MUST be owner scoped and read only. Never delete on uncertainty. */
  reconcile(ownerId: string, path: string, generation: string): Promise<string | null>
}

const UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
const PATH = new RegExp('^(' + UUID + ')/(' + UUID + ')\\.(mp4|webm)$')

/** Isolated candidate composition. Never wire to production without proving
 * Storage generation fencing and transactional DB RPC. No cleanup or delete.
 */
export async function finalizeImmutableCandidate(
  token: string,
  path: string,
  content: string,
  adapters: FinalizeCandidateAdapters,
): Promise<string> {
  if (!token || typeof token !== 'string') throw new Error('missing JWT')
  if (typeof content !== 'string' || content.length > 10000) throw new Error('invalid content')
  const match = PATH.exec(path)
  if (!match) throw new Error('invalid Storage path')
  const owner = await adapters.authenticate(token)
  if (owner !== match[1]) throw new Error('Storage owner mismatch')
  const snapshot = await adapters.snapshot(owner, path)
  if (snapshot.ownerId !== owner || snapshot.objectPath !== path) {
    throw new Error('Storage snapshot owner mismatch')
  }
  const generation = snapshot.generation
  requireImmutableGeneration(generation, await adapters.currentGeneration(owner, path))
  const inspected = await inspectStagedVideo(snapshot.bytes, match[3] as VideoExtension, snapshot.size)
  requireImmutableGeneration(generation, await adapters.currentGeneration(owner, path))
  if (!generation) throw new Error('missing immutable generation')
  // A second pre-publish check is only a detection mechanism. The adapter's
  // publish operation MUST enforce the generation inside the DB transaction.
  requireImmutableGeneration(generation, await adapters.currentGeneration(owner, path))
  let published: string
  try {
    published = await adapters.publish(owner, path, generation, inspected.sha256, inspected.duration, content)
  } catch (error) {
    if (error instanceof DefinitivePublishRejection) throw error
    // An ambiguous write may already have committed. Reconciliation errors
    // must preserve the unknown outcome; never delete or republish blindly.
    let reconciled: string | null = null
    try {
      reconciled = await adapters.reconcile(owner, path, generation)
    } catch {
      throw new Error('video commit outcome unknown; reconciliation unavailable')
    }
    if (reconciled && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(reconciled)) return reconciled
    throw new Error('video commit outcome unknown; retry with same object')
  }
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(published)) {
    throw new Error('invalid published post identity; retain staged object')
  }
  return published
}
