import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { auditPlayerType } from '../scripts/audit-player-type.mjs'
const fixture = JSON.parse(readFileSync(new URL('./fixtures/player-type-v2.json', import.meta.url)))
const assets = readdirSync(new URL('../public/animals/', import.meta.url)).map(name => name.replace(/\.png$/, ''))

test('unchanged historical fixture remains conditional and semantically unverified', () => {
  const before = JSON.stringify(fixture)
  const result = auditPlayerType(fixture, assets)
  assert.equal(result.status, 'CONDITIONAL PASS')
  assert.deepEqual(result.errors, [])
  assert.match(result.classificationSemanticValidity, /^UNKNOWN:/)
  assert.equal(JSON.stringify(fixture), before)
})

test('equal duplicate score rows cannot silently pass through Map overwrite', () => {
  const duplicate = structuredClone(fixture)
  duplicate.scores.push({ ...duplicate.scores[0] })
  const result = auditPlayerType(duplicate, assets)
  assert.equal(result.status, 'FAIL')
  assert.deepEqual(result.errors, [{ code: 'DUPLICATE_OPTION_SCORE', option: duplicate.scores[0].option_id }])
})

test('duplicate score row cannot conceal corrupt earlier values', () => {
  const duplicate = structuredClone(fixture)
  duplicate.scores.unshift({ ...duplicate.scores[0], initiative: 9999 })
  const result = auditPlayerType(duplicate, assets)
  assert.equal(result.status, 'FAIL')
  assert.ok(result.errors.some(error => error.code === 'DUPLICATE_OPTION_SCORE'))
})

test('orphan option score rows are rejected even if all real scores are complete', () => {
  const orphan = structuredClone(fixture)
  orphan.scores.push({ ...orphan.scores[0], option_id: 'not-in-question-bank' })
  const result = auditPlayerType(orphan, assets)
  assert.equal(result.status, 'FAIL')
  assert.deepEqual(result.errors, [{ code: 'ORPHAN_OPTION_SCORE', option: 'not-in-question-bank' }])
})

test('existing missing-score detection is preserved', () => {
  const missing = structuredClone(fixture)
  const removed = missing.scores.pop()
  const result = auditPlayerType(missing, assets)
  assert.equal(result.status, 'FAIL')
  assert.ok(result.errors.some(error => error.code === 'MISSING_OPTION_SCORE' && error.option === removed.option_id))
})
