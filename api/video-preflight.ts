import { createHash } from 'node:crypto'
import { probeVideoBytes, type VideoExtension, MAX_VIDEO_BYTES } from './video-ffprobe.js'

/** Candidate read-only preflight. Does not authorize publication or cleanup.
 * Storage immutability and a transactionally fenced object identity remain
 * mandatory before any caller may commit a post.
 */
export async function inspectStagedVideo(
  bytes: Buffer,
  extension: VideoExtension,
  expectedSize: number,
): Promise<{ sha256: string; duration: number; size: number }> {
  if (!Number.isSafeInteger(expectedSize) || expectedSize < 1 || expectedSize > MAX_VIDEO_BYTES) {
    throw new Error('invalid expected object size')
  }
  if (!Buffer.isBuffer(bytes) || bytes.length !== expectedSize) {
    throw new Error('downloaded bytes do not match expected object size')
  }
  const { duration, size } = await probeVideoBytes(bytes, extension)
  return { sha256: createHash('sha256').update(bytes).digest('hex'), duration, size }
}

/** Comparing hashes does not prevent an ABA swap. Requires an immutable
 * generation identifier or version fence enforced by the Storage service.
 */
export function requireImmutableGeneration(before: string | null, after: string | null): void {
  if (!before || !after || before !== after) {
    throw new Error('immutable Storage generation not proven')
  }
}
