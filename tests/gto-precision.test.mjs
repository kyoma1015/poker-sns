import { test } from 'node:test'
import assert from 'node:assert/strict'
import { abstractResearch } from '../src/gto/abstractResearch.ts'
import { conditionalPrecision, precisionResearch } from '../src/gto/precisionResearch.ts'
import { validateVerifiedRange } from '../src/gto/rangeCatalog.ts'

test('precision data remains research-only with unknown reference and game error', () => {
  assert.equal(precisionResearch.reference_solution_comparison, 'UNPERFORMED')
  assert.equal(precisionResearch.reference_difference, null)
  assert.equal(precisionResearch.real_game_approximation_error, null)
  assert.equal(validateVerifiedRange(precisionResearch, {}), null)
  assert.equal(precisionResearch.exact_cells.exact_showdown_cells, 2227)
  assert.deepEqual(precisionResearch.exact_cells.targets, ['AA', 'KK', 'AKo', 'AKs', 'QQ', 'TT'])
})
test('all169 conditional profiles and actions bind to their original frozen policy', () => {
  for (const [mode, model] of Object.entries(abstractResearch.models)) {
    for (const [stage, context] of Object.entries(model.contexts)) {
      const p = conditionalPrecision(mode, stage, model.policy_digest, context.actor, context.actions)
      assert.ok(p)
      assert.equal(Object.keys(p.hands).length, 169)
      for (const [hand, row] of Object.entries(p.hands)) {
        assert.ok(Math.abs(row.ev_bb - context.hands[hand].frequencies.reduce((ev, f, i) => ev + f * row.action_ev_bb[i], 0)) < 1e-9)
        assert.ok(row.radius_bb < 18.311301534)
        const fold = context.actions.indexOf('fold')
        assert.equal(row.action_exact[fold], true)
        assert.equal(row.action_intervals_bb[fold][0], row.action_intervals_bb[fold][1])
      }
      assert.equal(conditionalPrecision(mode, stage, '0'.repeat(64), context.actor, context.actions), null)
      assert.equal(conditionalPrecision(mode, stage, model.policy_digest, 1 - context.actor, context.actions), null)
    }
  }
})
test('AA/KK/AKo/AKs checkdown values have no sampling uncertainty without claiming real GTO', () => {
  const m = abstractResearch.models.checkdown
  for (const stage of ['rfi', 'vs_open', 'vs_3bet', 'vs_4bet']) {
    const c = m.contexts[stage];const p = conditionalPrecision('checkdown', stage, m.policy_digest, c.actor, c.actions)
    for (const h of ['AA', 'KK', 'AKo', 'AKs', 'QQ', 'TT']) {
      assert.equal(p.hands[h].radius_bb, 0)
      assert.ok(p.hands[h].action_exact.every(Boolean))
    }
  }
})
