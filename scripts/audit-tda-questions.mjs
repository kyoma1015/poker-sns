#!/usr/bin/env node
// Offline JSON export audit. Never accesses a DB or publishes questions.
import { readFileSync } from 'node:fs'
import { quizAuditReport } from '../src/tdaQuizData.ts'
const [file, expectedCount] = process.argv.slice(2)
if (!file || (expectedCount !== undefined && !/^[1-9]\d*$/.test(expectedCount))) {
  console.error('Usage: node scripts/audit-tda-questions.mjs <questions.json> [expected-count]')
  process.exitCode = 2
} else {
  try {
    const report = quizAuditReport(JSON.parse(readFileSync(file, 'utf8')), expectedCount ? Number(expectedCount) : undefined)
    console.log(JSON.stringify(report, null, 2))
    process.exitCode = report.verdict === 'STRUCTURE_PASS' ? 0 : 1
  } catch (error) {
    // Do not echo question text or raw file payloads to logs.
    console.error(JSON.stringify({ verdict: 'FAIL', reason: error instanceof Error ? error.message : 'Invalid input', publication_approved: false }))
    process.exitCode = 1
  }
}
