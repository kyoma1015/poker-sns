import { readFileSync } from 'node:fs'
import { quizAuditReport } from '../src/tdaQuizData.ts'

const defaultIo = {
  readFile: file => readFileSync(file, 'utf8'),
  stdout: line => console.log(line),
  stderr: line => console.error(line),
}
const usage = 'Usage: node scripts/audit-tda-questions.mjs <questions.json> [expected-count]'

// Keep failure output independent of input text, file paths and error messages.
// V8 JSON errors can quote the invalid input; filesystem errors can quote paths.
export function runQuizAuditCli(args, io = defaultIo) {
  const [file, expectedCount] = args
  const count = expectedCount === undefined ? undefined : Number(expectedCount)
  if (args.length < 1 || args.length > 2 || typeof file !== 'string' || !file ||
      (expectedCount !== undefined &&
       (typeof expectedCount !== 'string' || !/^[1-9]\d*$/.test(expectedCount) || !Number.isSafeInteger(count)))) {
    io.stderr(usage)
    return 2
  }
  const fail = reason => {
    io.stderr(JSON.stringify({ verdict: 'FAIL', reason, official_rule_accuracy: 'UNVERIFIED', publication_approved: false }))
    return 1
  }
  let raw
  try { raw = io.readFile(file) }
  catch { return fail('INPUT_READ_FAILED') }
  let value
  try { value = JSON.parse(raw) }
  catch { return fail('INVALID_JSON') }
  let report
  try { report = quizAuditReport(value, count) }
  catch { return fail('INVALID_QUESTION_DATA') }
  io.stdout(JSON.stringify(report, null, 2))
  return report.verdict === 'STRUCTURE_PASS' ? 0 : 1
}
