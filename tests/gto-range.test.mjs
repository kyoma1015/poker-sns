import { test } from 'node:test'
import assert from 'node:assert/strict'
import { canonicalQuery, queryKey, oneBBQuery, positions, handLabels, handGrid, validateVerifiedRange, findVerifiedRange } from '../src/gto/rangeCatalog.ts'
import { oneBBRange, oneBBCertificate } from '../src/gto/oneBBRange.ts'

// Synthetic parser fixtures only; these are never included in the app catalog.
const query = { format: 'ring', players: 6, seat: 2, stackBb: '100', anteBb: '0', rakePct: '5',
  rakeCapBb: '5', openBb: '2.5', threeBetBb: '9', fourBetBb: '21', stage: 'vs_3bet' }
function fixture() {
  const record = { schema: 'pokerid-verified-preflop-v1', id: 'parser-fixture-only', query: { ...query },
    conditionClass: 'explicit_test', conditionName: 'Synthetic parser fixture only',
    policyDigest: 'a'.repeat(64), configDigest: 'b'.repeat(64), certificateId: 'fixture-only',
    actions: ['Fold', 'Call', 'Raise'], coverage: { combinations: 1326, hands: 169 }, equilibriumVerified: true,
    hands: Object.fromEntries(handLabels.map(label => [label, { combinations: label.endsWith('s') ? 4 : label.endsWith('o') ? 12 : 6,
      frequencies: [.25, .5, .25], evBb: .1, evIntervalBb: [.1, .1] }])) }
  const certificate = { datasetId: record.id, queryKey: queryKey(query), policyDigest: record.policyDigest,
    configDigest: record.configDigest, artifactSha256: 'c'.repeat(64), scope: 'complete_target_game',
    continuation: 'full_native_game', metric: 'max_unilateral_deviation_gain', upperBoundBb: .001,
    acceptedToleranceBb: .01, confidence: 1, verificationMethod: 'deterministic_full_game',
    reviewReference: 'synthetic test fixture; not real equilibrium evidence' }
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
test('actual native full-game evidence yields one separate test range with169EV intervals', () => {
  const registry = { [oneBBRange.certificateId]: oneBBCertificate }
  const result = findVerifiedRange(oneBBQuery, [oneBBRange], registry)
  assert.equal(result?.conditionClass, 'explicit_test')
  assert.equal(result.query.stage, 'forced_blind_allin')
  for (const row of Object.values(result.hands)) {
    assert.deepEqual(row.frequencies, [0, 1])
    assert.ok(row.evIntervalBb[0] > -.5)
    assert.ok(row.evIntervalBb[0] <= row.evBb && row.evBb <= row.evIntervalBb[1])
  }
  assert.equal(result.certificate.upperBoundBb, 0)
  assert.equal(result.certificate.confidence, .999999998)
})
test('the forced-blind certificate cannot be reused for ordinary RFI or other stack sizes', () => {
  assert.throws(() => canonicalQuery({ ...oneBBQuery, stackBb: '2' }))
  assert.throws(() => canonicalQuery({ ...oneBBQuery, players: 6 }))
  assert.throws(() => canonicalQuery({ ...oneBBQuery, stage: 'rfi' }))
  assert.throws(() => canonicalQuery({ ...oneBBQuery, openBb: '1' }))
})
test('missing array entries cannot cross the verified release boundary', () => {
  for (const alter of [
    r => { delete r.actions[1] },
    r => { r.hands.AA.frequencies = [.5, 0, .5]; delete r.hands.AA.frequencies[1] },
    r => { delete r.hands.AA.evIntervalBb[0] },
    r => { delete r.hands.AA.evIntervalBb[1] },
  ]) {
    const { record, registry } = fixture()
    alter(record)
    assert.equal(validateVerifiedRange(record, registry), null)
    assert.equal(findVerifiedRange(query, [record], registry), null)
  }
})
test('explicit histories distinguish opener seats and never reuse unspecified-history data', () => {
  const early = [{ seat: 2, action: 'raise', toBb: '2.50' }]
  const late = [{ seat: 2, action: 'fold' }, { seat: 3, action: 'raise', toBb: '2.5' },
    { seat: 4, action: 'fold' }, { seat: 5, action: 'fold' }, { seat: 0, action: 'fold' }]
  const q = { ...query, stage: 'vs_open', seat: 3, history: early }
  assert.equal(canonicalQuery(q).history[0].toBb, '2.5')
  assert.notEqual(queryKey(q), queryKey({ ...q, history: undefined }))
  assert.notEqual(queryKey({ ...q, seat: 1, history: [...early, { seat: 3, action: 'fold' },
    { seat: 4, action: 'fold' }, { seat: 5, action: 'fold' }, { seat: 0, action: 'fold' }] }), queryKey({ ...q, seat: 1, history: late }))
  const { record, registry } = fixture()
  const threeBetHistory = [{ seat: 2, action: 'raise', toBb: '2.5' }, { seat: 3, action: 'raise', toBb: '9' },
    { seat: 4, action: 'fold' }, { seat: 5, action: 'fold' }, { seat: 0, action: 'fold' }, { seat: 1, action: 'fold' }]
  assert.equal(findVerifiedRange({ ...query, history: threeBetHistory }, [record], registry), null)
})
test('actual HU limp raise 3bet 4bet history retains the correct next actor', () => {
  const history = [{ seat: 0, action: 'call' }, { seat: 1, action: 'raise', toBb: '2.5' },
    { seat: 0, action: 'raise', toBb: '9' }, { seat: 1, action: 'raise', toBb: '21' }]
  const q = { ...query, players: 2, stackBb: '50', seat: 0, stage: 'vs_4bet', history }
  assert.deepEqual(canonicalQuery(q).history, history)
  assert.throws(() => canonicalQuery({ ...q, seat: 1 }))
  assert.throws(() => canonicalQuery({ ...q, stage: 'vs_3bet' }))
  assert.throws(() => canonicalQuery({ ...q, threeBetBb: '10' }))
  assert.throws(() => canonicalQuery({ ...q, history: [...history, { seat: 0, action: 'call' }] }))
})
test('illegal or incomplete public actions fail closed without guessing formal sizes', () => {
  const base = { ...query, stage: 'vs_open', seat: 3 }
  for (const history of [[{ seat: 3, action: 'raise', toBb: '2.5' }],
    [{ seat: 2, action: 'raise', toBb: '1.5' }], [{ seat: 2, action: 'raise', toBb: '101' }],
    [{ seat: 2, action: 'check' }], [{ seat: 2, action: 'fold', toBb: '2' }], new Array(1)]) {
    assert.throws(() => canonicalQuery({ ...base, history }))
  }
  assert.throws(() => canonicalQuery({ ...query, stage: 'rfi', seat: 3, history: [{ seat: 2, action: 'call' }] }))
})
test('BB option and all-in calls end the round; every table size starts at the correct seat', async () => {
  const { analyzeHistory } = await import('../src/gto/preflopHistory.ts')
  for (let n = 2; n <= 9; n++) assert.equal(analyzeHistory(n, '50', []).nextSeat, n === 2 ? 0 : 2)
  assert.equal(analyzeHistory(2, '50', [{ seat: 0, action: 'call' }]).nextSeat, 1)
  assert.equal(analyzeHistory(2, '50', [{ seat: 0, action: 'call' }, { seat: 1, action: 'check' }]).nextSeat, null)
  const allin = [{ seat: 0, action: 'raise', toBb: '50' }, { seat: 1, action: 'call' }]
  assert.equal(analyzeHistory(2, '50', allin).nextSeat, null)
  assert.throws(() => analyzeHistory(2, '50', [...allin, { seat: 0, action: 'check' }]))
})
test('only a separately reviewed exact-history certificate enables an explicit-history range', () => {
  const { record, registry } = fixture()
  const history = [{ seat: 2, action: 'raise', toBb: '2.5' }, { seat: 3, action: 'raise', toBb: '9' },
    { seat: 4, action: 'fold' }, { seat: 5, action: 'fold' }, { seat: 0, action: 'fold' }, { seat: 1, action: 'fold' }]
  record.query = canonicalQuery({ ...query, history })
  assert.equal(findVerifiedRange(record.query, [record], registry), null)
  registry['fixture-only'].queryKey = queryKey(record.query)
  assert.equal(findVerifiedRange(record.query, [record], registry)?.id, record.id)
  assert.equal(findVerifiedRange(query, [record], registry), null)
})
