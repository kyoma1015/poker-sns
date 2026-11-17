/** Client-side fail-closed precondition only. The server remains authoritative. */
export function isProvenPublishedVideoRecovery(
  proof: { state: string; allow_resume: boolean; storage_present: boolean; sha256: string; size: number; post_id: string | null },
  hint: { sha256: string; size: number },
): boolean {
  return proof.state === 'published' && proof.allow_resume === false &&
    proof.storage_present === true && proof.sha256 === hint.sha256 &&
    proof.size === hint.size && typeof proof.post_id === 'string' &&
    /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(proof.post_id)
}

/** A different or malformed draft must never be discarded as part of recovery. */
export function matchesPendingVideoRecovery(raw: string | null, owner: string, path: string): boolean {
  if (raw === null) return true
  try {
    const value: unknown = JSON.parse(raw)
    return value !== null && typeof value === 'object' && !Array.isArray(value) &&
      (value as { owner?: unknown }).owner === owner &&
      (value as { path?: unknown }).path === path
  } catch { return false }
}
