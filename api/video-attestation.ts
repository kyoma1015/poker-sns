import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto'

/** Versioned, length-delimited server evidence. Never call with browser-supplied metadata. */
export type VideoAttestationClaims = {
  owner: string
  path: string
  generation: string
  sha256: string
  durationMs: number
  contentSha256: string
  expiresAt: number
  nonce: string
}
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
const digest=/^[0-9a-f]{64}$/
const noncePattern=/^[0-9a-f]{32}$/
export function canonicalVideoAttestation(c: VideoAttestationClaims): Buffer {
  if (!uuid.test(c.owner) || !uuid.test(c.generation) ||
    !new RegExp('^'+c.owner+'/[0-9a-f-]{36}\\.(mp4|webm)$').test(c.path) ||
    !digest.test(c.sha256) || !digest.test(c.contentSha256) ||
    !Number.isSafeInteger(c.durationMs) || c.durationMs<=0 || c.durationMs>30000 ||
    !Number.isSafeInteger(c.expiresAt) || c.expiresAt<=0 ||
    !noncePattern.test(c.nonce)) throw new Error('invalid video attestation claims')
  const fields=['video-attestation-v1',c.owner,c.path,c.generation,c.sha256,
    String(c.durationMs),c.contentSha256,String(c.expiresAt),c.nonce]
  return Buffer.from(fields.map(v=>Buffer.byteLength(v,'utf8')+':'+v).join(''),'utf8')
}
export function signVideoAttestation(key: Buffer, claims: VideoAttestationClaims): string {
  if (key.length!==32) throw new Error('invalid attestation signing key')
  return createHmac('sha256',key).update(canonicalVideoAttestation(claims)).digest('hex')
}
export function verifyVideoAttestation(key: Buffer, claims: VideoAttestationClaims, signature: string): boolean {
  if (!digest.test(signature)) return false
  try {
    const expected=Buffer.from(signVideoAttestation(key,claims),'hex')
    return timingSafeEqual(expected,Buffer.from(signature,'hex'))
  } catch {
    return false // malformed or inconsistent claims must fail verification
  }
}
export function createVideoAttestationNonce(): string {
  return randomBytes(16).toString('hex')
}
