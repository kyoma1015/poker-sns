import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { topPersonalTraits, personalAdvice, traitPositiveMax, relativePositiveScore } from '../src/playerTypePresentation.ts'
import { parseQuestions, LatestRequest } from '../src/playerTypeQuestions.ts'

const fixture = JSON.parse(readFileSync(new URL('./fixtures/player-type-v2.json', import.meta.url)))
const detail = scores => ({ trait_scores: scores, discriminator_scores: {} })

test('all 32 positive ceilings equal the sum of per-question attainable maxima', () => {
  const questions = parseQuestions(fixture.rows)
  const scores = Object.fromEntries(fixture.scores.map(s => [s.option_id, s]))
  for (const [key, cap] of Object.entries(traitPositiveMax)) {
    assert.equal(cap, questions.reduce((sum, q) => sum + Math.max(0, ...q.options.map(o => scores[o.id][key])), 0), key)
  }
})

test('negative, zero, unknown and nonfinite values do not become top tendencies', () => {
  assert.deepEqual(topPersonalTraits(detail({ initiative: -1, exploit: 0, analytical: NaN, patience: Infinity, bogus: 99 })), [])
  assert.equal(relativePositiveScore('bogus', 100), 0)
})

test('normalization compares proportions rather than raw totals', () => {
  assert.deepEqual(topPersonalTraits(detail({ exploit: 24, risk_tolerance: 3, patience: 23 })).map(t => t.key), ['patience', 'risk_tolerance', 'exploit'])
})

test('one incidental selective-burst point must not assert attacking ability', () => {
  const weak = fixture.personas[0]
  assert.equal(weak.raw.selective_burst, 1)
  assert.match(personalAdvice(detail(weak.raw)), /危険や難しい衝突/)
  assert.doesNotMatch(personalAdvice(detail(weak.raw)), /武器|踏み込める|攻めを続ける回答/)
})

test('attack wording needs both initiative and sustained attack at the threshold', () => {
  const high = { initiative: 8.55, confidence: 3.3, attack_momentum: 6, threat_sensitivity: 0 }
  assert.match(personalAdvice(detail(high)), /自分から動き、攻めを続ける/)
  for (const key of ['initiative', 'confidence', 'attack_momentum']) {
    assert.doesNotMatch(personalAdvice(detail({ ...high, [key]: high[key] - .01 })), /自分から動き、攻めを続ける/)
  }
})

for (const persona of fixture.personas) {
  test(`fixed persona replay (not live): ${persona.name}`, () => {
    const questions = parseQuestions(fixture.rows)
    const byId = Object.fromEntries(fixture.scores.map(s => [s.option_id, s]))
    const chosen = questions.map((q, i) => byId[q.options.find(o => o.order === persona.answers[i].charCodeAt(0) - 64).id])
    const raw = Object.fromEntries(Object.keys(traitPositiveMax).map(k => [k, chosen.reduce((sum, s) => sum + s[k], 0)]))
    assert.deepEqual(raw, persona.raw)
    const traits = topPersonalTraits(detail(raw))
    assert.equal(traits.length, 3)
    assert.ok(traits.every(t => raw[t.key] > 0))
    const advice = personalAdvice(detail(raw))
    if (raw.attack_momentum < 0 || raw.initiative < 8.55) assert.doesNotMatch(advice, /自分から動き、攻めを続ける|攻めを続ける回答/)
    assert.doesNotMatch(advice, /武器|さらに強く|確実に勝てる/)
  })
}

test('question bank validation rejects incomplete or contradictory data', () => {
  assert.equal(parseQuestions(fixture.rows).length, 50)
  const withoutQ50 = fixture.rows.filter(r => r.question_order !== 50)
  const onlyOneOption = fixture.rows.filter(r => r.question_order !== 50 || r.option_order === 1)
  for (const invalid of [null, {}, withoutQ50, onlyOneOption, [...fixture.rows, fixture.rows[0]],
    fixture.rows.map((r, i) => i === 0 ? { ...r, option_text: '' } : r),
    fixture.rows.map((r, i) => i === 0 ? { ...r, question_order: 2 } : r),
    fixture.rows.map((r, i) => i === 0 ? { ...r, option_order: 9 } : r)]) {
    assert.throws(() => parseQuestions(invalid))
  }
})

test('a late result cannot win after a new request, restart or unmount', () => {
  const gate = new LatestRequest()
  const old = gate.start()
  const next = gate.start()
  assert.equal(gate.isCurrent(old), false)
  assert.equal(gate.isCurrent(next), true)
  gate.invalidate()
  assert.equal(gate.isCurrent(next), false)
})
