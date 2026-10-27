import { test } from 'node:test'
import assert from 'node:assert/strict'
import { canonicalQuery, queryKey, positions, handLabels, handGrid, validateVerifiedRange, findVerifiedRange } from '../src/gto/rangeCatalog.ts'

// Synthetic parser fixtures only; these are never included in the app catalog.
const query = { format: 'ring', players: 6, seat: 2, stackBb: '100', anteBb: '0', rakePct: '5',
  rakeCapBb: '5', openBb: '2.5', threeBetBb: '9', fourBetBb: '21', stage: 'vs_3bet' }
function fixture() {
  const record = { schema: 'pokerid-verified-preflop-v1', id: 'parser-fixture-only', query: { ...query },
    policyDigest: 'a'.repeat(64), configDigest: 'b'.repeat(64), certificateId: 'fixture-only',
    actions: ['Fold', 'Call', 'Raise'], coverage: { combinations: 1326, hands: 169 }, equilibriumVerified: true,
    hands: Object.fromEntries(handLabels.map(label => [label, { combinations: label.endsWith('s') ? 4 : label.endsWith('o') ? 12 : 6,
      frequencies: [.25, .5, .25], evBb: .1 }])) }
  const certificate = { datasetId: record.id, queryKey: queryKey(query), policyDigest: record.policyDigest,
    configDigest: record.configDigest, artifactSha256: 'c'.repeat(64), scope: 'complete_target_game',
    continuation: 'full_native_game', metric: 'max_unilateral_deviation_gain', upperBoundBb: .001,
    acceptedToleranceBb: .01, reviewReference: 'synthetic test fixture; not real equilibrium evidence' }
  return { record, registry: { 'fixture-only': certificate } }
}
test('grid has169 unique classes and1326 concrete combinations', () => {
  assert.equal(handGrid.length, 13); assert.equal(new Set(handLabels).size, 169)
  assert.equal(handLabels.reduce((n, h) => n + (h.endsWith('s') ? 4 : h.endsWith('o') ? 12 : 6), 0), 1326)
})
test('decimal query normalization preserves exact condition lookup', () => {
  assert.equal(queryKey(query), queryKey({ ...query, stackBb: '100.00', openBb: '2.500' }))
  const { record, registry } = fixture()
  assert.equal(findVerifiedRange(query, [record], registry)?.id, record.id)
  assert.equal(findVerifiedRange({ ...query, players: 9 }, [record], registry), null)
})
test('all2..9 seats map to unique native seat numbers', () => {
  for (let n = 2; n <= 9; n++) assert.deepEqual(positions(n).map(p => p.seat).sort((a,b) => a-b), Array.from({ length: n }, (_, i) => i))
  assert.equal(positions(2)[0].label, 'BTN / SB')
  assert.equal(positions(6).find(p => p.seat === 2).label, 'UTG')
})
test('unreviewed claimed verification cannot enable display', () => {
  const { record } = fixture()
  assert.equal(validateVerifiedRange(record, {}), null)
  assert.equal(validateVerifiedRange({ schema: 'pokerid-learned-joint-preflop-v1', equilibriumVerified: true }, {}), null)
})
test('partial class or combination coverage is rejected', () => {
  for (const alter of [r => { delete r.hands.AA }, r => { r.coverage.combinations = 1325 }, r => { r.hands.AA.combinations = 5 }]) {
    const { record, registry } = fixture(); alter(record); assert.equal(validateVerifiedRange(record, registry), null)
  }
})
test('unknown EV, invalid frequencies and nonfinite EV are rejected', () => {
  for (const alter of [r => { r.hands.AA.evBb = null }, r => { r.hands.AA.evBb = Infinity },
    r => { r.hands.AA.frequencies = [.5, .5, .5] }, r => { r.hands.AA.frequencies = [-.1, .6, .5] }]) {
    const { record, registry } = fixture(); alter(record); assert.equal(validateVerifiedRange(record, registry), null)
  }
})
test('local drift or sampled confidence cannot substitute for full-game certificate', () => {
  for (const alter of [c => { c.scope = 'single_infoset' }, c => { c.metric = 'policy_drift' },
    c => { c.continuation = 'showdown_shortcut' }, c => { c.upperBoundBb = .1 }, c => { c.policyDigest = 'd'.repeat(64) }]) {
    const { record, registry } = fixture(); alter(registry['fixture-only']); assert.equal(validateVerifiedRange(record, registry), null)
  }
})
test('invalid modes, seats and MTT rake are rejected', () => {
  for (const patch of [{ players: 1 }, { seat: 6 }, { stackBb: '0' }, { openBb: 'NaN' }, { format: 'mtt' }]) {
    assert.throws(() => canonicalQuery({ ...query, ...patch }))
  }
})
