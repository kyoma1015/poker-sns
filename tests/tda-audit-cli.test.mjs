import test from 'node:test'
import assert from 'node:assert/strict'
import { runQuizAuditCli } from '../scripts/tda-audit-cli.mjs'

const question = { question_id: 'synthetic-q1', question_text: 'Synthetic question', difficulty: null, category: null,
  options: [{ id: 'a', option_order: 1, option_text: 'A' }, { id: 'b', option_order: 2, option_text: 'B' }] }
function invoke(args, readFile = () => JSON.stringify([question])) {
  const stdout = [], stderr = []
  let reads = 0
  const exit = runQuizAuditCli(args, { readFile: file => { reads++; return readFile(file) },
    stdout: text => stdout.push(text), stderr: text => stderr.push(text) })
  return { exit, reads, stdout, stderr }
}
const sentinel = 'PRIVATE_DRAFT_ISSUE22_SENTINEL'
for (const raw of [sentinel, `{"${sentinel}":`, `{"question_text":"${sentinel}"oops}`]) {
  test('malformed JSON never echoes payload fragments or parser details', () => {
    const result = invoke(['private-export.json'], () => raw)
    assert.equal(result.exit, 1)
    assert.deepEqual(result.stdout, [])
    assert.deepEqual(JSON.parse(result.stderr[0]), { verdict: 'FAIL', reason: 'INVALID_JSON',
      official_rule_accuracy: 'UNVERIFIED', publication_approved: false })
    assert.doesNotMatch(result.stderr.join(''), /PRIVATE|Unexpected|position|question_text|private-export/)
  })
}
test('read failures do not reveal paths or untrusted error text', () => {
  const result = invoke([`/private/${sentinel}.json`], () => { throw new Error(sentinel) })
  assert.equal(result.exit, 1)
  assert.equal(JSON.parse(result.stderr[0]).reason, 'INPUT_READ_FAILED')
  assert.doesNotMatch(result.stderr.join(''), /PRIVATE|\/private/)
})
test('invalid question shape has a stable failure code without raw data', () => {
  const result = invoke(['export.json'], () => JSON.stringify({ secret: sentinel }))
  assert.equal(result.exit, 1)
  assert.equal(JSON.parse(result.stderr[0]).reason, 'INVALID_QUESTION_DATA')
  assert.doesNotMatch(result.stderr.join(''), /PRIVATE|secret/)
})
for (const args of [[], [''], ['export.json', '1', 'ignored-before'], ['export.json','0'], ['export.json','-1'],
  ['export.json','1.5'], ['export.json','1e3'], ['export.json','01'], ['export.json','NaN'],
  ['export.json','9007199254740992'], ['export.json','9'.repeat(400)]]) {
  test(`invalid arguments fail before reading (${JSON.stringify(args).slice(0,100)})`, () => {
    const result = invoke(args)
    assert.equal(result.exit, 2)
    assert.equal(result.reads, 0)
    assert.deepEqual(result.stdout, [])
    assert.equal(result.stderr.length, 1)
    assert.match(result.stderr[0], /^Usage:/)
  })
}
test('valid report and count mismatch preserve the non-publication contract', () => {
  const valid = invoke(['export.json','1'])
  assert.equal(valid.exit, 0)
  assert.deepEqual(valid.stderr, [])
  const report = JSON.parse(valid.stdout[0])
  assert.equal(report.verdict, 'STRUCTURE_PASS')
  assert.equal(report.publication_approved, false)
  assert.equal(report.official_rule_accuracy, 'UNVERIFIED')
  const mismatch = invoke(['export.json','350'])
  assert.equal(mismatch.exit, 1)
  assert.equal(JSON.parse(mismatch.stdout[0]).count_matches, false)
})
test('safe integer upper boundary is accepted as a count, without rounding', () => {
  const result = invoke(['export.json', String(Number.MAX_SAFE_INTEGER)])
  assert.equal(result.exit, 1)
  assert.deepEqual(result.stderr, [])
  assert.equal(JSON.parse(result.stdout[0]).expected_count, Number.MAX_SAFE_INTEGER)
})
