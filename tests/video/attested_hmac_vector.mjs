import assert from 'node:assert/strict'
import { signBinaryVideoAttestation, videoAttestationDigest } from '../../api/video-attestation.ts'
// Fixed fixture key, never production secret. PostgreSQL checks the same vector.
const owner='10000000-0000-0000-0000-000000000001'
const signature=signBinaryVideoAttestation(Buffer.alloc(32,0x41),{
 owner,
 path:owner+'/30000000-0000-0000-0000-000000000009.mp4',
 generation:'d71e6f03-8ac2-4a55-91bf-fc3296e7184d',
 sha256:'a'.repeat(64),durationMs:2000,
 contentSha256:videoAttestationDigest('test'),
 expiresAt:1893456000,nonce:'b'.repeat(32),
})
assert.equal(signature,'d50ae4bb28c6c60b60f7e39b9acec328d537e188b78567ff4ddeab0de0a34779')
console.log('PASS: Node binary HMAC matches independent PostgreSQL test vector')
