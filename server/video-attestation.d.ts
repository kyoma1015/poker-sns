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
export declare function canonicalVideoAttestation(c: VideoAttestationClaims): Buffer
export declare function signVideoAttestation(key: Buffer, claims: VideoAttestationClaims): string
export declare function verifyVideoAttestation(key: Buffer, claims: VideoAttestationClaims, signature: string): boolean
export declare function createVideoAttestationNonce(): string
export declare function videoAttestationDigest(content: string): string
export declare function binaryVideoAttestation(c: VideoAttestationClaims): Buffer
export declare function signBinaryVideoAttestation(key: Buffer, c: VideoAttestationClaims): string
