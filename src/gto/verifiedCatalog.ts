import type { ReviewedCertificate } from './rangeCatalog'
import { oneBBRange, oneBBCertificate } from './oneBBRange'

// Explicit HU1BB calibration only; no ordinary/formal RFI or3bet data accepted.
// Raw native counts and the whole-game certificate are regenerated/checked in CI.
// Partial research artifacts cannot be promoted by merely adding a boolean.
export const verifiedCatalog: readonly unknown[] = [oneBBRange]
export const reviewedCertificates: Readonly<Record<string, ReviewedCertificate>> = {
  [oneBBRange.certificateId]: oneBBCertificate,
}
