import { createHash, createHmac, randomBytes, timingSafeEqual } from 'node:crypto'

/** Versioned, length-delimited server evidence. Never call with browser-supplied metadata. */
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
const digest=/^[0-9a-f]{64}$/
const noncePattern=/^[0-9a-f]{32}$/
export function canonicalVideoAttestation(c) {
  if (!uuid.test(c.owner) || !uuid.test(c.generation) ||
    !new RegExp('^'+c.owner+'/[0-9a-f-]{36}\\.(mp4|webm|mov)$').test(c.path) ||
    !digest.test(c.sha256) || !digest.test(c.contentSha256) ||
    !Number.isSafeInteger(c.durationMs) || c.durationMs<=0 || c.durationMs>30000 ||
    !Number.isSafeInteger(c.expiresAt) || c.expiresAt<=0 ||
    !noncePattern.test(c.nonce)) throw new Error('invalid video attestation claims')
  const fields=['video-attestation-v1',c.owner,c.path,c.generation,c.sha256,
    String(c.durationMs),c.contentSha256,String(c.expiresAt),c.nonce]
  return Buffer.from(fields.map(v=>Buffer.byteLength(v,'utf8')+':'+v).join(''),'utf8')
}
export function signVideoAttestation(key, claims) {
  if (key.length!==32) throw new Error('invalid attestation signing key')
  return createHmac('sha256',key).update(canonicalVideoAttestation(claims)).digest('hex')
}
export function verifyVideoAttestation(key, claims, signature) {
  if (!digest.test(signature)) return false
  try {
    const expected=Buffer.from(signVideoAttestation(key,claims),'hex')
    return timingSafeEqual(expected,Buffer.from(signature,'hex'))
  } catch {
    return false // malformed or inconsistent claims must fail verification
  }
}
export function createVideoAttestationNonce() {
  return randomBytes(16).toString('hex')
}

/** Fixed-width byte encoding shared with pgcrypto decode(...,'hex') on the DB side. */
export function videoAttestationDigest(content) {
  return createHash('sha256').update(content,'utf8').digest('hex')
}

/** PostgreSQL can verify this exact binary payload using decode and pgcrypto.hmac.
 * This avoids JS/Postgres float serialization or ambiguous field boundaries. */
export function binaryVideoAttestation(c) {
  canonicalVideoAttestation(c)
  const path=Buffer.from(c.path,'utf8')
  if (path.length>255) throw new Error('attestation path too long')
  const result=Buffer.alloc(1+16+1+path.length+16+32+4+32+8+16)
  let offset=0
  result.writeUInt8(1,offset++)
  for(const id of [c.owner]) { Buffer.from(id.replaceAll('-',''),'hex').copy(result,offset); offset+=16 }
  result.writeUInt8(path.length,offset++);path.copy(result,offset);offset+=path.length
  Buffer.from(c.generation.replaceAll('-',''),'hex').copy(result,offset);offset+=16
  Buffer.from(c.sha256,'hex').copy(result,offset);offset+=32
  result.writeUInt32BE(c.durationMs,offset);offset+=4
  Buffer.from(c.contentSha256,'hex').copy(result,offset);offset+=32
  result.writeBigUInt64BE(BigInt(c.expiresAt),offset);offset+=8
  Buffer.from(c.nonce,'hex').copy(result,offset)
  return result
}
export function signBinaryVideoAttestation(key,c) {
  if(key.length!==32) throw new Error('invalid attestation signing key')
  return createHmac('sha256',key).update(binaryVideoAttestation(c)).digest('hex')
}
).test(c.path) ||
    !digest.test(c.sha256) || !digest.test(c.contentSha256) ||
    !Number.isSafeInteger(c.durationMs) || c.durationMs<=0 || c.durationMs>30000 ||
    !Number.isSafeInteger(c.expiresAt) || c.expiresAt<=0 ||
    !noncePattern.test(c.nonce)) throw new Error('invalid video attestation claims')
  const fields=['video-attestation-v1',c.owner,c.path,c.generation,c.sha256,
    String(c.durationMs),c.contentSha256,String(c.expiresAt),c.nonce]
  return Buffer.from(fields.map(v=>Buffer.byteLength(v,'utf8')+':'+v).join(''),'utf8')
}
export function signVideoAttestation(key, claims) {
  if (key.length!==32) throw new Error('invalid attestation signing key')
  return createHmac('sha256',key).update(canonicalVideoAttestation(claims)).digest('hex')
}
export function verifyVideoAttestation(key, claims, signature) {
  if (!digest.test(signature)) return false
  try {
    const expected=Buffer.from(signVideoAttestation(key,claims),'hex')
    return timingSafeEqual(expected,Buffer.from(signature,'hex'))
  } catch {
    return false // malformed or inconsistent claims must fail verification
  }
}
export function createVideoAttestationNonce() {
  return randomBytes(16).toString('hex')
}

/** Fixed-width byte encoding shared with pgcrypto decode(...,'hex') on the DB side. */
export function videoAttestationDigest(content) {
  return createHash('sha256').update(content,'utf8').digest('hex')
}

/** PostgreSQL can verify this exact binary payload using decode and pgcrypto.hmac.
 * This avoids JS/Postgres float serialization or ambiguous field boundaries. */
export function binaryVideoAttestation(c) {
  canonicalVideoAttestation(c)
  const path=Buffer.from(c.path,'utf8')
  if (path.length>255) throw new Error('attestation path too long')
  const result=Buffer.alloc(1+16+1+path.length+16+32+4+32+8+16)
  let offset=0
  result.writeUInt8(1,offset++)
  for(const id of [c.owner]) { Buffer.from(id.replaceAll('-',''),'hex').copy(result,offset); offset+=16 }
  result.writeUInt8(path.length,offset++);path.copy(result,offset);offset+=path.length
  Buffer.from(c.generation.replaceAll('-',''),'hex').copy(result,offset);offset+=16
  Buffer.from(c.sha256,'hex').copy(result,offset);offset+=32
  result.writeUInt32BE(c.durationMs,offset);offset+=4
  Buffer.from(c.contentSha256,'hex').copy(result,offset);offset+=32
  result.writeBigUInt64BE(BigInt(c.expiresAt),offset);offset+=8
  Buffer.from(c.nonce,'hex').copy(result,offset)
  return result
}
export function signBinaryVideoAttestation(key,c) {
  if(key.length!==32) throw new Error('invalid attestation signing key')
  return createHmac('sha256',key).update(binaryVideoAttestation(c)).digest('hex')
}
