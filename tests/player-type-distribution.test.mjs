import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { auditPlayerType } from '../scripts/audit-player-type.mjs'
import { parseQuestions } from '../src/playerTypeQuestions.ts'
import { traitPositiveMax } from '../src/playerTypePresentation.ts'
const fixture = JSON.parse(readFileSync(new URL('./fixtures/player-type-v2.json', import.meta.url)))
const assets = readdirSync(new URL('../public/animals/', import.meta.url)).filter(x => x.endsWith('.png')).map(x => x.slice(0,-4))
const distribution = () => auditPlayerType(fixture, assets).scoreDistribution

test('score audit measures all 50 questions and 32 axes without claiming a classifier', () => {
  const d = distribution()
  assert.ok(d)
  assert.equal(d.questions.length, 50)
  assert.equal(Object.keys(d.traits).length, 32)
  assert.equal(d.samples, 1000)
  assert.equal(d.classification, 'BLOCKED: authoritative classifier and expert labels unavailable')
})
test('exact reachable extrema equal sums of per-question extrema including negative scores', () => {
  const d = distribution()
  assert.ok(d)
  const questions = parseQuestions(fixture.rows), scores = new Map(fixture.scores.map(x=>[x.option_id,x]))
  for (const key of Object.keys(traitPositiveMax)) {
    const minima=questions.map(q=>Math.min(...q.options.map(o=>scores.get(o.id)[key])))
    const maxima=questions.map(q=>Math.max(...q.options.map(o=>scores.get(o.id)[key])))
    assert.equal(d.traits[key].minimum, minima.reduce((a,b)=>a+b,0))
    assert.equal(d.traits[key].maximum, maxima.reduce((a,b)=>a+b,0))
    assert.ok(d.traits[key].sampleMinimum >= d.traits[key].minimum)
    assert.ok(d.traits[key].sampleMaximum <= d.traits[key].maximum)
    assert.ok(Number.isFinite(d.traits[key].mean))
    assert.ok(d.traits[key].variance >= 0)
  }
  assert.ok(Object.values(d.traits).some(t=>t.minimum<0))
})
test('seeded samples are reproducible, complete and do not mutate historical source', () => {
  const before = JSON.stringify(fixture)
  const a=distribution(), b=distribution()
  assert.ok(a)
  assert.deepEqual(a,b)
  assert.equal(a.seed, 0x504944)
  for (const q of a.questions) {
    assert.equal(q.optionCounts.reduce((x,y)=>x+y,0),a.samples)
    assert.ok(q.optionCounts.every(n=>n>0))
    assert.ok(q.distinctScoreVectors>=1 && q.distinctScoreVectors<=q.optionCounts.length)
  }
  assert.equal(JSON.stringify(fixture),before)
})
test('historical persona totals remain within exact bounds without invented animal labels', () => {
  const d=distribution()
  assert.ok(d)
  assert.equal(d.personas.length, fixture.personas.length)
  for (const persona of d.personas) for (const [key,value] of Object.entries(persona.scores)) {
    assert.ok(value>=d.traits[key].minimum && value<=d.traits[key].maximum)
  }
})
test('invalid scores cannot generate apparently valid distribution evidence', () => {
  const invalid=structuredClone(fixture)
  invalid.scores[0].initiative=Infinity
  const report=auditPlayerType(invalid,assets)
  assert.equal(report.status,'FAIL')
  assert.equal(report.scoreDistribution,null)
})
