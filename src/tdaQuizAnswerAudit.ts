import { auditQuizQuestions, parseQuizQuestions } from './tdaQuizData.ts'

type AuditIssue = { code: string; question_id?: string }
type AnswerKey = { question_id: string; correct_option_id?: unknown; explanation?: unknown; rule_numbers?: unknown }
const record = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value)
const nonempty = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0

// Offline-only sidecar contract. Never request privileged correct answers in the
// public quiz RPC or interpret structural checks as official-rule verification.
export function auditQuizAnswerKey(questionExport: unknown, answerKeyExport: unknown) {
  const questions = parseQuizQuestions(questionExport)
  const duplicates = auditQuizQuestions(questionExport)
  if (!Array.isArray(answerKeyExport)) throw new Error('INVALID_ANSWER_KEY_EXPORT')
  const keys = new Map<string, AnswerKey[]>()
  for (const row of Array.from(answerKeyExport)) {
    if (!record(row) || !nonempty(row.question_id)) throw new Error('INVALID_ANSWER_KEY_ROW')
    const key: AnswerKey = { question_id: row.question_id, correct_option_id: row.correct_option_id,
      explanation: row.explanation, rule_numbers: row.rule_numbers }
    keys.set(key.question_id, [...(keys.get(key.question_id) ?? []), key])
  }
  const issues: AuditIssue[] = []
  const ids = new Set(questions.map(question => question.question_id))
  const answer_position_counts: Record<string, number> = {}
  for (const id of keys.keys()) if (!ids.has(id)) issues.push({code:'ORPHAN_ANSWER_KEY',question_id:id})
  for (const question of questions) {
    const id = question.question_id
    if (question.options.length !== 4) issues.push({code:'OPTION_COUNT_NOT_FOUR',question_id:id})
    const rows = keys.get(id) ?? []
    if (!rows.length) { issues.push({code:'MISSING_ANSWER_KEY',question_id:id}); continue }
    if (rows.length !== 1) { issues.push({code:'DUPLICATE_ANSWER_KEY',question_id:id}); continue }
    const key = rows[0]
    const index = question.options.findIndex(option => option.id === key.correct_option_id)
    if (index < 0) issues.push({code:'INVALID_CORRECT_OPTION',question_id:id})
    else { const position = String(index + 1); answer_position_counts[position] = (answer_position_counts[position] ?? 0) + 1 }
    if (!nonempty(key.explanation)) issues.push({code:'INVALID_EXPLANATION',question_id:id})
    const refs = key.rule_numbers
    if (!Array.isArray(refs) || !refs.length || Array.from(refs).some(ref =>
      typeof ref !== 'number' || !Number.isSafeInteger(ref) || ref < 1) || new Set(refs).size !== refs.length) {
      issues.push({code:'INVALID_RULE_REFERENCES',question_id:id})
    }
  }
  if (!questions.length) issues.push({code:'EMPTY_CORPUS'})
  const hasDuplicates = duplicates.duplicateQuestionCandidates.length > 0 || duplicates.duplicateOptionCandidates.length > 0
  return { ...duplicates, option_count: questions.reduce((total, question) => total + question.options.length, 0),
    answer_key_count: answerKeyExport.length, answer_position_counts, issues,
    verdict: !issues.length && !hasDuplicates ? 'STRUCTURE_PASS' as const : 'REVIEW_REQUIRED' as const,
    official_rule_accuracy: 'UNVERIFIED' as const, publication_approved: false as const }
}
