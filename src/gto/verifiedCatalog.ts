import type { ReviewedCertificate } from './rangeCatalog'

// Intentionally empty: no full-game equilibrium certificate has been accepted.
// Sampled/partial research artifacts must never be promoted by adding a boolean.
// Add data AND an independently reviewed matching certificate in a future PR.
export const verifiedCatalog: readonly unknown[] = []
export const reviewedCertificates: Readonly<Record<string, ReviewedCertificate>> = {}
