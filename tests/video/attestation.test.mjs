import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { canonicalVideoAttestation, createVideoAttestationNonce, signVideoAttestation, verifyVideoAttestation } from '../../api/video-attestation.ts'

const owner='10000000-0000-0000-0000-000000000001'
const key=Buffer.alloc(32,0x41)
const claims={
 owner,path:owner+'/30000000-0000-0000-0000-000000000001.webm',
 generation:'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
 sha256:'a'.repeat(64),durationMs:2000,
 contentSha256:createHash('sha256').update('video caption').digest('hex'),
 expiresAt:1893456000,nonce:createVideoAttestationNonce(),
}
const sig=signVideoAttestation(key,claims)
assert.equal(sig.length,64)
assert.equal(verifyVideoAttestation(key,claims,sig),true)
assert.equal(verifyVideoAttestation(Buffer.alloc(32,0x42),claims,sig),false)
assert.equal(verifyVideoAttestation(key,claims,'x'.repeat(64)),false)
for(const [field,value] of Object.entries({
 owner:'20000000-0000-0000-0000-000000000002',
 path:owner+'/30000000-0000-0000-0000-000000000002.webm',
 generation:'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
 sha256:'b'.repeat(64),durationMs:2500,
 contentSha256:'b'.repeat(64),expiresAt:1893455999,
 nonce:createVideoAttestationNonce(),
})){
 const tampered={...claims,[field]:value}
 assert.equal(verifyVideoAttestation(key,tampered,sig),false,'tampering '+field+' must fail')
}
assert.throws(()=>signVideoAttestation(Buffer.alloc(16),claims),/signing key/)
assert.throws(()=>canonicalVideoAttestation({...claims,durationMs:31000}),/invalid/)
assert.throws(()=>canonicalVideoAttestation({...claims,nonce:'bad'}),/invalid/)
console.log('PASS: canonical video attestation, tampering, key isolation and bounds')
