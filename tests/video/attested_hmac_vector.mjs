import assert from 'node:assert/strict'
import { signBinaryVideoAttestation, videoAttestationDigest } from '../../server/video-attestation.js'
// Fixture-only key; PostgreSQL checks this same independent deterministic vector.
const owner='10000000-0000-0000-0000-000000000001'
const claims={
 owner,
 path:owner+'/30000000-0000-0000-0000-000000000009.mp4',
 generation:'d71e6f03-8ac2-4a55-91bf-fc3296e7184d',
 sha256:'a'.repeat(64),durationMs:2000,
 contentSha256:videoAttestationDigest('test'),
 expiresAt:1893456000,nonce:'b'.repeat(32),
}
const key=Buffer.alloc(32,0x41)
const signature=signBinaryVideoAttestation(key,claims)
assert.equal(signature,'d50ae4bb28c6c60b60f7e39b9acec328d537e188b78567ff4ddeab0de0a34779')
// Every security-sensitive field must be cryptographically bound to the proof.
for(const [field,value] of Object.entries({
 owner:'10000000-0000-0000-0000-000000000002',
 path:owner+'/30000000-0000-0000-0000-000000000008.mp4',
 generation:'d71e6f03-8ac2-4a55-91bf-fc3296e7184e',
 sha256:'c'.repeat(64),durationMs:2001,
 contentSha256:videoAttestationDigest('tampered'),
 expiresAt:1893456001,nonce:'c'.repeat(32),
})) {
 const altered={...claims,[field]:value}
 if(field==='owner') altered.path=value+'/30000000-0000-0000-0000-000000000009.mp4'
 assert.notEqual(signBinaryVideoAttestation(key,altered),signature,field+' must change the HMAC')
}
assert.notEqual(signBinaryVideoAttestation(Buffer.alloc(32,0x42),claims),signature,
 'different key must not validate the attestation')
for(const invalid of [{durationMs:0},{durationMs:30001},{nonce:'bad'},{sha256:'invalid'},{expiresAt:-1}]) {
 assert.throws(()=>signBinaryVideoAttestation(key,{...claims,...invalid}))
}
console.log('PASS: Node/PostgreSQL HMAC vector and all security claim mutation checks')
