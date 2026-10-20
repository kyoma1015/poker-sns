// Offline audit. No DB calls, no publication, no inference of classifier accuracy.
import { readFileSync, readdirSync } from 'node:fs'
import { parseQuestions } from '../src/playerTypeQuestions.ts'
import { animalEmoji } from '../src/playerTypeAnimals.ts'
import { traitPositiveMax } from '../src/playerTypePresentation.ts'
const fixture = JSON.parse(readFileSync(new URL('../tests/fixtures/player-type-v2.json', import.meta.url)))
const questions = parseQuestions(fixture.rows)
const assets = readdirSync(new URL('../public/animals/', import.meta.url)).filter(name => name.endsWith('.png')).map(name => name.slice(0, -4))
const scores = new Map(fixture.scores.map(row => [row.option_id, row]))
const errors = []
const warnings = []
const textSeen = new Map()
for (const question of questions) {
  const normalized = question.text.normalize('NFKC').replace(/\s+/g, '').toLowerCase()
  if (textSeen.has(normalized)) warnings.push({ code: 'DUPLICATE_QUESTION_TEXT', orders: [textSeen.get(normalized), question.order] })
  textSeen.set(normalized, question.order)
  for (const option of question.options) {
    const row = scores.get(option.id)
    if (!row) errors.push({ code: 'MISSING_OPTION_SCORE', option: option.id })
    else for (const key of Object.keys(traitPositiveMax)) {
      if (!Number.isFinite(row[key])) errors.push({ code: 'NONFINITE_SCORE', option: option.id, key })
    }
  }
}
for (const [key, expected] of Object.entries(traitPositiveMax)) {
  const actual = questions.reduce((sum, question) => sum + Math.max(0, ...question.options.map(option => Number(scores.get(option.id)?.[key]))), 0)
  if (actual !== expected) errors.push({ code: 'CEILING_MISMATCH', key, expected, actual })
}
const configured = Object.keys(animalEmoji)
for (const key of new Set([...assets, ...configured])) {
  if (!assets.includes(key) || !configured.includes(key)) errors.push({ code: 'ANIMAL_ASSET_MISMATCH', key })
}
if (configured.length !== 36) errors.push({ code: 'ANIMAL_COUNT', actual: configured.length })
const report = { status: errors.length ? 'FAIL' : 'CONDITIONAL PASS', source: 'checked-in historical fixture; not live DB', questions: questions.length, options: questions.reduce((n,q) => n + q.options.length, 0), scoreDimensions: Object.keys(traitPositiveMax).length,
  animalDisplayKeys: configured.length, pngAssets: assets.length, personas: fixture.personas.length, errors, warnings,
  classificationSemanticValidity: 'UNKNOWN: fixture includes option scores/personas, not authoritative 36-animal classifier definitions or human-reviewed labels', liveSchemaAndQuestions: 'NOT CHECKED', scoringChanges: 'none', sqlExecuted: false }
console.log(JSON.stringify(report, null, 2))
process.exitCode = errors.length ? 1 : 0
