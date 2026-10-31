import { test } from 'node:test'
import assert from 'node:assert/strict'
import { abstractResearch, abstractResearchQuery, findAbstractResearch } from '../src/gto/abstractResearch.ts'
import { findVerifiedRange, validateVerifiedRange } from '../src/gto/rangeCatalog.ts'
import { oneBBRange, oneBBCertificate } from '../src/gto/oneBBRange.ts'

test('research is separate from verified GTO and real-game error remains unknown', () => {
  assert.equal(abstractResearch.full_game_gto_verified, false)
  assert.equal(abstractResearch.real_game_error_bound_bb, null)
  assert.equal(abstractResearch.reference_solution_comparison, 'UNPERFORMED')
  assert.equal(validateVerifiedRange(abstractResearch, {}), null)
  assert.equal(findVerifiedRange(abstractResearchQuery, [oneBBRange], { [oneBBRange.certificateId]: oneBBCertificate }), null)
})
test('research lookup requires exact stack sizes position and history', () => {
  for (const [stage, seat] of [['rfi', 0], ['vs_open', 1], ['vs_3bet', 0], ['vs_4bet', 1]]) {
    assert.equal(findAbstractResearch({ ...abstractResearchQuery, stage, seat }), stage)
    assert.equal(findAbstractResearch({ ...abstractResearchQuery, stage, seat: 1 - seat }), null)
  }
  for (const patch of [{ players: 3 }, { stackBb: '100' }, { anteBb: '1' }, { format: 'ring', rakePct: '5' }, { openBb: '3' }, { threeBetBb: '10' }, { fourBetBb: '22' }]) {
    assert.equal(findAbstractResearch({ ...abstractResearchQuery, ...patch }), null)
  }
})
test('both continuation models contain normalized169 hands and model EV intervals', () => {
  for (const model of Object.values(abstractResearch.models)) {
    assert.ok(model.abstract_nashconv_bb < .01)
    assert.equal(model.heldout.seed, 700017)
    assert.ok(model.heldout.interval_bb[0] <= model.heldout.profile_sb_ev_bb && model.heldout.profile_sb_ev_bb <= model.heldout.interval_bb[1])
    for (const context of Object.values(model.contexts)) {
      assert.equal(Object.keys(context.hands).length, 169)
      for (const row of Object.values(context.hands)) {
        assert.ok(Math.abs(row.frequencies.reduce((a, b) => a + b, 0) - 1) < 1e-10)
        assert.ok(Math.abs(row.ev_bb - row.frequencies.reduce((v, p, i) => v + p * row.action_ev_bb[i], 0)) < 1e-10)
      }
    }
  }
})
