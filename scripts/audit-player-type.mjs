// Offline audit. No DB calls, no publication, no inference of classifier accuracy.
import { readFileSync, readdirSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
import { parseQuestions } from '../src/playerTypeQuestions.ts'
import { animalEmoji } from '../src/playerTypeAnimals.ts'
import { traitPositiveMax } from '../src/playerTypePresentation.ts'
// Uniform independent option sampling is a reproducible stress fixture, not a
// model of real players and not evidence for animal meaning or prevalence.
function scoreDistribution(questions, scores, personas) {
  const keys = Object.keys(traitPositiveMax)
  const samples = 1000, seed = 0x504944
  let state = seed
  const random = () => {
    state ^= state << 13; state ^= state >>> 17; state ^= state << 5
    return (state >>> 0) / 0x100000000
  }
  const vectors = questions.map(question => question.options.map(option => keys.map(key => scores.get(option.id)[key])))
  const traits = Object.fromEntries(keys.map((key, axis) => [key, {
    minimum: vectors.reduce((sum, options) => sum + Math.min(...options.map(v => v[axis])), 0),
    maximum: vectors.reduce((sum, options) => sum + Math.max(...options.map(v => v[axis])), 0),
    sampleMinimum: Infinity, sampleMaximum: -Infinity, mean: 0, variance: 0,
  }]))
  const questionEvidence = questions.map((question, index) => ({
    order: question.order,
    optionCounts: question.options.map(() => 0),
    distinctScoreVectors: new Set(vectors[index].map(vector => JSON.stringify(vector))).size,
  }))
  const sumAnswers = choices => keys.map((_, axis) => vectors.reduce((sum, options, index) => sum + options[choices[index]][axis], 0))
  for (let sample = 1; sample <= samples; sample++) {
    const choices = vectors.map((options, index) => {
      const choice = Math.floor(random() * options.length)
      questionEvidence[index].optionCounts[choice]++
      return choice
    })
    const totals = sumAnswers(choices)
    keys.forEach((key, axis) => {
      const item = traits[key], value = totals[axis], delta = value - item.mean
      item.sampleMinimum = Math.min(item.sampleMinimum, value)
      item.sampleMaximum = Math.max(item.sampleMaximum, value)
      item.mean += delta / sample
      item.variance += delta * (value - item.mean)
    })
  }
  for (const item of Object.values(traits)) item.variance /= samples
  return {
    sampling: 'uniform independent option choices; synthetic stress evidence, not player prevalence',
    seed, samples, traits, questions: questionEvidence,
    personas: personas.map((persona, index) => {
      const totals = sumAnswers(persona.answers.map((answer, question) => questions[question].options.findIndex(option => answer === String.fromCharCode(64 + option.order))))
      return { index, scores: Object.fromEntries(keys.map((key, axis) => [key, totals[axis]])) }
    }),
    classification: 'BLOCKED: authoritative classifier and expert labels unavailable',
  }
}
export function auditPlayerType(fixture, assets) {
  const questions = parseQuestions(fixture.rows)
  const errors = []
  const scores = new Map()
  const optionIds = new Set(questions.flatMap(question => question.options.map(option => option.id)))
  for (const row of fixture.scores) {
    if (scores.has(row.option_id)) errors.push({ code: 'DUPLICATE_OPTION_SCORE', option: row.option_id })
    if (!optionIds.has(row.option_id)) errors.push({ code: 'ORPHAN_OPTION_SCORE', option: row.option_id })
    scores.set(row.option_id, row)
  }
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
  for (const [personaIndex, persona] of fixture.personas.entries()) {
    const answers = persona?.answers
    if (!Array.isArray(answers) || answers.length !== questions.length) {
      errors.push({ code: 'INVALID_PERSONA_ANSWER_COUNT', persona: personaIndex, expected: questions.length, actual: Array.isArray(answers) ? answers.length : null })
      continue
    }
    for (const [questionIndex, question] of questions.entries()) {
      if (!question.options.some(option => answers[questionIndex] === String.fromCharCode(64 + option.order))) {
        errors.push({ code: 'INVALID_PERSONA_CHOICE', persona: personaIndex, question: question.order })
      }
    }
  }
  const configured = Object.keys(animalEmoji)
  for (const key of new Set([...assets, ...configured])) {
    if (!assets.includes(key) || !configured.includes(key)) errors.push({ code: 'ANIMAL_ASSET_MISMATCH', key })
  }
  if (configured.length !== 36) errors.push({ code: 'ANIMAL_COUNT', actual: configured.length })
  let distribution = errors.length ? null : scoreDistribution(questions, scores, fixture.personas)
  if (distribution) {
    for (const [key, metrics] of Object.entries(distribution.traits)) {
      if (Object.values(metrics).some(value => !Number.isFinite(value))) errors.push({ code: 'NONFINITE_SCORE_AGGREGATE', key })
    }
    if (errors.length) distribution = null
  }
  const scoringInputValid = !errors.length
  let comparedValues = 0
  const dimensionKeys = Object.keys(traitPositiveMax)
  for (const [personaIndex, persona] of fixture.personas.entries()) {
    const reference = persona?.raw
    if (!reference || typeof reference !== 'object' || Array.isArray(reference) ||
        Object.keys(reference).length !== dimensionKeys.length ||
        dimensionKeys.some(key => !Object.hasOwn(reference, key) || !Number.isFinite(reference[key]))) {
      errors.push({ code: 'INVALID_PERSONA_REFERENCE', persona: personaIndex })
      continue
    }
    // Only compare after the existing answer and score-bank validation succeeds.
    if (!scoringInputValid) continue
    const totals = Object.fromEntries(dimensionKeys.map(key => [key, questions.reduce((sum, question, index) => {
      const option = question.options.find(option => persona.answers[index] === String.fromCharCode(64 + option.order))
      return sum + scores.get(option.id)[key]
    }, 0)]))
    for (const key of dimensionKeys) {
      comparedValues++
      if (totals[key] !== reference[key]) errors.push({ code: 'PERSONA_REFERENCE_MISMATCH', persona: personaIndex, key })
    }
  }
  if (errors.length) distribution = null
  const report = { status: errors.length ? 'FAIL' : 'CONDITIONAL PASS', source: 'checked-in historical fixture; not live DB', questions: questions.length, options: questions.reduce((n,q) => n + q.options.length, 0), scoreDimensions: Object.keys(traitPositiveMax).length,
    animalDisplayKeys: configured.length, pngAssets: assets.length, personas: fixture.personas.length, errors, warnings,
    scoreDistribution: distribution,
    personaReferenceComparison: { status: comparedValues === fixture.personas.length * dimensionKeys.length && !errors.length ? 'PASS' : 'FAIL', personas: fixture.personas.length, dimensions: dimensionKeys.length, comparedValues, sourceCommit: fixture.source_commit, classification: 'NOT VERIFIED' },
    classificationSemanticValidity: 'UNKNOWN: fixture includes option scores/personas, not authoritative 36-animal classifier definitions or human-reviewed labels', liveSchemaAndQuestions: 'NOT CHECKED', scoringChanges: 'none', sqlExecuted: false }
  return report
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  const fixture = JSON.parse(readFileSync(new URL('../tests/fixtures/player-type-v2.json', import.meta.url)))
  const assets = readdirSync(new URL('../public/animals/', import.meta.url)).filter(name => name.endsWith('.png')).map(name => name.slice(0, -4))
  const report = auditPlayerType(fixture, assets)
  console.log(JSON.stringify(report, null, 2))
  process.exitCode = report.status === 'FAIL' ? 1 : 0
}
