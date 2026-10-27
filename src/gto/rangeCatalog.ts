/** Verified-only release boundary. Review certificates are trusted build inputs,
 * not user-uploaded assertions. Existing sampled/native research schemas fail.
 * This checks transport completeness; it does not independently prove Nash. */
export type RangeQuery = {
  format: 'mtt' | 'ring'; players: number; seat: number; stackBb: string;
  anteBb: '0' | '1'; rakePct: '0' | '5' | '10'; rakeCapBb: null | '5' | '10';
  openBb: string; threeBetBb: string; fourBetBb: string;
  stage: 'rfi' | 'vs_open' | 'vs_3bet' | 'vs_4bet';
}
export type ReviewedCertificate = {
  datasetId: string; queryKey: string; policyDigest: string; configDigest: string;
  artifactSha256: string; scope: 'complete_target_game'; continuation: 'full_native_game';
  metric: 'max_unilateral_deviation_gain'; upperBoundBb: number; acceptedToleranceBb: number;
  reviewReference: string;
}
export type VerifiedRange = {
  schema: 'pokerid-verified-preflop-v1'; id: string; query: RangeQuery;
  policyDigest: string; configDigest: string; certificateId: string;
  actions: string[]; hands: Record<string, { combinations: number; frequencies: number[]; evBb: number }>;
  coverage: { combinations: 1326; hands: 169 }; equilibriumVerified: true;
  certificate: ReviewedCertificate;
}
const ranks = 'AKQJT98765432'
export const handGrid: string[][] = Array.from(ranks, (a, row) => Array.from(ranks, (b, column) =>
  row === column ? a + b : row < column ? a + b + 's' : b + a + 'o'))
export const handLabels = handGrid.flat()
const stages = new Set(['rfi', 'vs_open', 'vs_3bet', 'vs_4bet'])
const digestPattern = /^[a-f0-9]{64}$/
function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
function decimal(value: unknown): string {
  if (typeof value !== 'string' || value.length > 24 || !/^(0|[1-9]\d*)(\.\d{1,8})?$/.test(value)) {
    throw new Error('スタックとベットサイズを正の数で入力してください。')
  }
  const [whole, fraction = ''] = value.split('.')
  const tail = fraction.replace(/0+$/, '')
  const normalized = tail ? `${whole}.${tail}` : whole
  if (normalized === '0') throw new Error('スタックとベットサイズは0より大きい値が必要です。')
  return normalized
}
export function canonicalQuery(value: unknown): RangeQuery {
  if (!object(value) || typeof value.format !== 'string' || !['mtt', 'ring'].includes(value.format) ||
      !Number.isInteger(value.players) || Number(value.players) < 2 || Number(value.players) > 9 ||
      !Number.isInteger(value.seat) || Number(value.seat) < 0 || Number(value.seat) >= Number(value.players) ||
      !['0', '1'].includes(String(value.anteBb)) || typeof value.anteBb !== 'string' ||
      !['0', '5', '10'].includes(String(value.rakePct)) || typeof value.rakePct !== 'string' ||
      ![null, '5', '10'].includes(value.rakeCapBb as null | string) || typeof value.stage !== 'string' || !stages.has(value.stage)) {
    throw new Error('ゲーム形式・人数・ポジション・アンティ・レーキを確認してください。')
  }
  if (value.format === 'mtt' && (value.rakePct !== '0' || value.rakeCapBb !== null)) {
    throw new Error('MTT chipEVではレーキなしを指定してください。')
  }
  return { format: value.format as RangeQuery['format'], players: Number(value.players), seat: Number(value.seat),
    stackBb: decimal(value.stackBb), anteBb: value.anteBb as RangeQuery['anteBb'],
    rakePct: value.rakePct as RangeQuery['rakePct'], rakeCapBb: value.rakeCapBb as RangeQuery['rakeCapBb'],
    openBb: decimal(value.openBb), threeBetBb: decimal(value.threeBetBb), fourBetBb: decimal(value.fourBetBb),
    stage: value.stage as RangeQuery['stage'] }
}
export function queryKey(value: unknown): string { return JSON.stringify(canonicalQuery(value)) }
export function positions(players: number): { seat: number; label: string }[] {
  if (!Number.isInteger(players) || players < 2 || players > 9) throw new Error('人数は2〜9人です。')
  if (players === 2) return [{ seat: 0, label: 'BTN / SB' }, { seat: 1, label: 'BB' }]
  const early: Record<number, string[]> = {
    3: ['BTN'], 4: ['CO', 'BTN'], 5: ['HJ', 'CO', 'BTN'], 6: ['UTG', 'HJ', 'CO', 'BTN'],
    7: ['UTG', 'UTG+1', 'HJ', 'CO', 'BTN'], 8: ['UTG', 'UTG+1', 'LJ', 'HJ', 'CO', 'BTN'],
    9: ['UTG', 'UTG+1', 'UTG+2', 'LJ', 'HJ', 'CO', 'BTN'],
  }
  return [...early[players].map((label, index) => ({ seat: index + 2, label })),
    { seat: 0, label: 'SB' }, { seat: 1, label: 'BB' }]
}
export function validateVerifiedRange(value: unknown, registry: Readonly<Record<string, ReviewedCertificate>>): VerifiedRange | null {
  if (!object(value) || value.schema !== 'pokerid-verified-preflop-v1' || value.equilibriumVerified !== true ||
      typeof value.id !== 'string' || typeof value.certificateId !== 'string' ||
      typeof value.policyDigest !== 'string' || !digestPattern.test(value.policyDigest) ||
      typeof value.configDigest !== 'string' || !digestPattern.test(value.configDigest) ||
      !object(value.coverage) || value.coverage.combinations !== 1326 || value.coverage.hands !== 169 ||
      !Array.isArray(value.actions) || !value.actions.length || value.actions.length > 64 ||
      value.actions.some(a => typeof a !== 'string' || !a || a.length > 100) ||
      new Set(value.actions).size !== value.actions.length || !object(value.hands)) return null
  let query: RangeQuery
  try { query = canonicalQuery(value.query) } catch { return null }
  if (!Object.hasOwn(registry, value.certificateId)) return null
  const certificate = registry[value.certificateId]
  if (!certificate || typeof certificate !== 'object' || certificate.datasetId !== value.id || certificate.queryKey !== queryKey(query) ||
      certificate.policyDigest !== value.policyDigest || certificate.configDigest !== value.configDigest ||
      typeof certificate.artifactSha256 !== 'string' || !digestPattern.test(certificate.artifactSha256) || certificate.scope !== 'complete_target_game' ||
      certificate.continuation !== 'full_native_game' || certificate.metric !== 'max_unilateral_deviation_gain' ||
      !Number.isFinite(certificate.upperBoundBb) || certificate.upperBoundBb < 0 ||
      !Number.isFinite(certificate.acceptedToleranceBb) || certificate.acceptedToleranceBb < 0 ||
      certificate.upperBoundBb > certificate.acceptedToleranceBb || typeof certificate.reviewReference !== 'string' || !certificate.reviewReference) return null
  if (Object.keys(value.hands).length !== 169) return null
  const hands: VerifiedRange['hands'] = {}
  for (const label of handLabels) {
    const row = value.hands[label]
    const expected = label.endsWith('s') ? 4 : label.endsWith('o') ? 12 : 6
    if (!object(row) || row.combinations !== expected || typeof row.evBb !== 'number' || !Number.isFinite(row.evBb) ||
        !Array.isArray(row.frequencies) || row.frequencies.length !== value.actions.length ||
        row.frequencies.some(p => typeof p !== 'number' || !Number.isFinite(p) || p < 0 || p > 1) ||
        Math.abs(row.frequencies.reduce((a: number, b: number) => a + b, 0) - 1) > 1e-9) return null
    hands[label] = { combinations: expected, frequencies: [...row.frequencies], evBb: row.evBb }
  }
  return { schema: 'pokerid-verified-preflop-v1', id: value.id, query, policyDigest: value.policyDigest,
    configDigest: value.configDigest, certificateId: value.certificateId, actions: [...value.actions], hands,
    coverage: { combinations: 1326, hands: 169 }, equilibriumVerified: true, certificate: { ...certificate } }
}
export function findVerifiedRange(query: unknown, catalog: readonly unknown[], registry: Readonly<Record<string, ReviewedCertificate>>): VerifiedRange | null {
  const key = queryKey(query)
  for (const candidate of catalog) {
    if (!object(candidate)) continue
    try { if (queryKey(candidate.query) !== key) continue } catch { continue }
    const result = validateVerifiedRange(candidate, registry)
    if (result) return result
  }
  return null
}
