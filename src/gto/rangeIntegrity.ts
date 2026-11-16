/** Content binding for reviewed release artifacts. Structural validation alone
 * cannot establish that hand values are the ones reviewed. No strategy is certified here. */
import { canonicalQuery, queryKey, validateVerifiedRange } from './rangeCatalog.ts'
import type { ReviewedCertificate, VerifiedRange } from './rangeCatalog.ts'

export function canonicalJson(value: unknown): string {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value)
  if (typeof value === 'number' && Number.isFinite(value)) return JSON.stringify(value)
  if (Array.isArray(value)) return '[' + Array.from(value).map(canonicalJson).join(',') + ']'
  if (typeof value === 'object' && value !== null) {
    const obj = value as Record<string, unknown>
    return '{' + Object.keys(obj).sort().map(key => JSON.stringify(key) + ':' + canonicalJson(obj[key])).join(',') + '}'
  }
  throw new Error('検証対象のデータに欠損値または非有限値があります。')
}
export async function sha256(value: string | Uint8Array<ArrayBuffer>): Promise<string> {
  try {
    const result = await crypto.subtle.digest('SHA-256', typeof value === 'string' ? new TextEncoder().encode(value) : value)
    return Array.from(new Uint8Array(result), b => b.toString(16).padStart(2, '0')).join('')
  } catch (cause) {
    throw new Error('表示データの整合性を検証できませんでした。再検索してください。', { cause })
  }
}
export async function rangePayloadDigest(range: Omit<VerifiedRange, 'certificate'> | VerifiedRange): Promise<string> {
  const payload = { schema: range.schema, id: range.id, query: canonicalQuery(range.query),
    conditionClass: range.conditionClass, conditionName: range.conditionName,
    policyDigest: range.policyDigest, configDigest: range.configDigest, certificateId: range.certificateId,
    actions: range.actions, hands: range.hands, coverage: range.coverage, equilibriumVerified: range.equilibriumVerified }
  return sha256(canonicalJson(payload))
}
export async function findIntegrityCheckedRange(query: unknown, catalog: readonly unknown[],
  registry: Readonly<Record<string, ReviewedCertificate>>): Promise<VerifiedRange | null> {
  const key = queryKey(query)
  for (const raw of catalog) {
    const range = validateVerifiedRange(raw, registry)
    if (!range || queryKey(range.query) !== key) continue
    const expected = range.certificate.rangePayloadSha256
    // Preserve only the existing narrowly specified HU1BB calibration path.
    // Ordinary RFI/3bet data requires a reviewed content digest.
    if (expected === undefined && range.query.stage === 'forced_blind_allin') return range
    if (typeof expected !== 'string' || !/^[a-f0-9]{64}$/.test(expected)) continue
    if (await rangePayloadDigest(range) === expected) return range
  }
  return null
}
