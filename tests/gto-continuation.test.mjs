import { test } from 'node:test'
import assert from 'node:assert/strict'
import { auditData, findContinuationAudit, auditModels } from '../src/gto/continuationAudit.ts'
import { findVerifiedRange } from '../src/gto/rangeCatalog.ts'
import { independentQuery } from '../src/gto/independentResearch.ts'

test('all4 frozen reach configurations and5 continuation profiles remain research-only', () => {
 for (const preflop of ['learned_small', 'learned_large']) for (const stage of ['vs_3bet', 'vs_4bet']) {
  const c = findContinuationAudit(stage, preflop); assert.ok(c)
  assert.deepEqual(Object.keys(c.models).sort(), [...auditModels].sort())
  for (const m of Object.values(c.models)) assert.ok(m.board_class_flags.conditional_call_nashconv_bb + 1e-7 >= m.texture_flags.conditional_call_nashconv_bb)
 }
 assert.equal(findVerifiedRange(independentQuery, [auditData], {}), null)
})
test('uncomputed stages, missing/invalid data and false admission fail closed', () => {
 for (const stage of ['rfi', 'vs_open', 'invalid']) assert.equal(findContinuationAudit(stage, 'learned_small'), null)
 for (const patch of [{ normal_gto_admission: true }, { formal_acceptance: 1 }, { condition: { ...auditData.condition, players: 6 } }, { real_game_approximation_error: '0' }]) assert.equal(findContinuationAudit('vs_4bet', 'learned_small', { ...auditData, ...patch }), null)
 assert.equal(findContinuationAudit('vs_4bet', 'bad'), null)
})
test('unphysical future envelope and nonfinite BR are rejected', () => {
 for (const alter of [x => { x.configs['learned_small|vs_4bet'].models.fixed_small.board_class_flags.conditional_call_nashconv_bb = NaN },
  x => { x.configs['learned_small|vs_4bet'].models.fixed_small.future_street_envelope.root_lower = 100 },
  x => { x.configs['learned_small|vs_4bet'].root_call_probability = 0 }]) {
  const x = structuredClone(auditData); alter(x); assert.equal(findContinuationAudit('vs_4bet', 'learned_small', x), null)
 }
})
