import { test } from 'node:test'
import assert from 'node:assert/strict'
import { findIndependentResearch, independentResearch as data, independentQuery, independentStages } from '../src/gto/independentResearch.ts'
import { findVerifiedRange, handLabels } from '../src/gto/rangeCatalog.ts'
import { oneBBRange, oneBBCertificate } from '../src/gto/oneBBRange.ts'
const verifiedCatalog = [oneBBRange], reviewedCertificates = { [oneBBCertificate.id]: oneBBCertificate }

test('new fixed-game research169x4x2 rows, EV intervals and exact conditions', () => {
  for (const stage of independentStages) assert.equal(findIndependentResearch({ ...independentQuery, stage, seat: ['rfi', 'vs_3bet'].includes(stage) ? 0 : 1 }), stage)
  for (const model of Object.values(data.models)) for (const ctx of Object.values(model.contexts)) {
    assert.deepEqual(Object.keys(ctx.hands).sort(), [...handLabels].sort())
    for (const row of Object.values(ctx.hands)) assert.ok(Math.abs(row.ev_bb - row.frequencies.reduce((sum, f, i) => sum + f * row.action_ev_bb[i], 0)) < 1e-10)
  }
})
test('unsupported player, seat, stack, ante, rake and size do not interpolate', () => {
  for (const patch of [{ players: 6 }, { seat: 1 }, { stackBb: '100' }, { anteBb: '1' }, { format: 'ring', rakePct: '5', rakeCapBb: '5' }, { openBb: '2' }, { threeBetBb: '8' }, { fourBetBb: '22' }]) assert.equal(findIndependentResearch({ ...independentQuery, ...patch }), null)
  assert.equal(findIndependentResearch({ ...independentQuery, format: 'ring' }), 'rfi')
})
test('research data cannot be promoted into verified GTO via labels or catalog', () => {
  assert.equal(findVerifiedRange(independentQuery, [data], reviewedCertificates), null)
  assert.equal(findVerifiedRange(independentQuery, verifiedCatalog, reviewedCertificates), null)
  assert.equal(findIndependentResearch(independentQuery, { ...data, full_game_gto_verified: true }), null)
  assert.equal(findIndependentResearch(independentQuery, { ...data, formal_acceptance_complete: 1 }), null)
})
test('corrupt frequency, history or action EV interval fails closed', () => {
  for (const alter of [x => { x.models.learned_small.contexts.rfi.hands.AA.frequencies[0] = 2 },
    x => { x.models.learned_small.contexts.vs_open.history = [] },
    x => { x.models.learned_large.contexts.vs_4bet.hands.AA.action_ev_intervals_bb[0] = [100, 101] }]) {
    const x = structuredClone(data); alter(x); assert.equal(findIndependentResearch(independentQuery, x), null)
  }
})
