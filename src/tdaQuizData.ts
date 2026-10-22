export type TdaQuizOption = { id: string; option_order: number; option_text: string }
export type TdaQuizQuestion = {
  question_id: string
  question_text: string
  difficulty: string | null
  category: string | null
  options: TdaQuizOption[]
}

type RpcError = { message: string; code?: string }
type RpcResult<T> = { data: T | null; error: RpcError | null }

// A thrown transport exception must follow the same recovery path as an RPC error.
// Never retry answer writes automatically: the original request may have committed.
export async function safeQuizRpc<T>(request: () => PromiseLike<RpcResult<T>>): Promise<RpcResult<T>> {
  try { return await request() }
  catch { return { data: null, error: { message: '通信状況を確認して再度お試しください。' } } }
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
function text(value: unknown): value is string { return typeof value === 'string' && value.trim().length > 0 }

// Structural validation is deliberately separate from official-rule correctness.
export function parseQuizQuestions(value: unknown): TdaQuizQuestion[] {
  if (!Array.isArray(value)) throw new Error('問題データの形式を確認できませんでした。再度お試しください。')
  const ids = new Set<string>()
  return value.map(row => {
    if (!record(row) || !text(row.question_id) || ids.has(row.question_id) || !text(row.question_text) ||
        !(row.difficulty === null || typeof row.difficulty === 'string') ||
        !(row.category === null || typeof row.category === 'string') || !Array.isArray(row.options) || row.options.length < 2) {
      throw new Error('問題データの整合性を確認できませんでした。再度お試しください。')
    }
    ids.add(row.question_id)
    const optionIds = new Set<string>()
    const orders = new Set<number>()
    const options = row.options.map(option => {
      if (!record(option) || !text(option.id) || optionIds.has(option.id) || !text(option.option_text) ||
          typeof option.option_order !== 'number' || !Number.isInteger(option.option_order) ||
          option.option_order < 0 || orders.has(option.option_order)) {
        throw new Error('選択肢データの整合性を確認できませんでした。再度お試しください。')
      }
      optionIds.add(option.id); orders.add(option.option_order)
      return { id: option.id, option_order: option.option_order, option_text: option.option_text }
    })
    return { question_id: row.question_id, question_text: row.question_text,
      difficulty: row.difficulty, category: row.category, options: options.sort((a,b) => a.option_order - b.option_order) }
  })
}

const normalized = (value: string) => value.normalize('NFKC').replace(/\s+/gu, '').toLocaleLowerCase('en-US')
export function auditQuizQuestions(value: unknown) {
  const questions = parseQuizQuestions(value)
  const duplicateQuestionCandidates: string[][] = []
  const duplicateOptionCandidates: { question_id: string; option_ids: string[] }[] = []
  const questionGroups = new Map<string, string[]>()
  for (const question of questions) {
    const key = normalized(question.question_text)
    questionGroups.set(key, [...(questionGroups.get(key) || []), question.question_id])
    const groups = new Map<string, string[]>()
    for (const option of question.options) {
      const key = normalized(option.option_text)
      groups.set(key, [...(groups.get(key) || []), option.id])
    }
    for (const ids of groups.values()) if (ids.length > 1) duplicateOptionCandidates.push({ question_id: question.question_id, option_ids: ids })
  }
  for (const ids of questionGroups.values()) if (ids.length > 1) duplicateQuestionCandidates.push(ids)
  return { question_count: questions.length, duplicateQuestionCandidates, duplicateOptionCandidates,
    official_rule_accuracy: 'UNVERIFIED' as const }
}

export function quizAuditReport(value: unknown, expectedCount?: number) {
  if (expectedCount !== undefined && (!Number.isSafeInteger(expectedCount) || expectedCount < 1)) throw new Error('Expected count must be a positive integer')
  const report = auditQuizQuestions(value)
  const countMatches = expectedCount === undefined || report.question_count === expectedCount
  const candidates = report.duplicateQuestionCandidates.length + report.duplicateOptionCandidates.length
  return { ...report, expected_count: expectedCount ?? null, count_matches: countMatches,
    verdict: report.question_count > 0 && countMatches && !candidates ? 'STRUCTURE_PASS' as const : 'REVIEW_REQUIRED' as const,
    publication_approved: false as const }
}


// Saved answers are authoritative only after structural and cross-field checks.
// Optional explanation failures must not erase a valid, already committed save.
export function parseQuizAnswer(question: TdaQuizQuestion, selectedOptionId: string, value: unknown, detail: unknown = null) {
  const invalid = () => { throw new Error('回答結果を確認できませんでした。保存済みの可能性があるため、この問題には再回答しないでください。') }
  if (!record(value)) return invalid()
  const options = new Set(question.options.map(option => option.id))
  if (!options.has(selectedOptionId) || typeof value.is_correct !== 'boolean' ||
      typeof value.correct_option_id !== 'string' || !options.has(value.correct_option_id) ||
      value.is_correct !== (selectedOptionId === value.correct_option_id) ||
      typeof value.total_answers !== 'number' || !Number.isSafeInteger(value.total_answers) || value.total_answers < 0 ||
      typeof value.correct_answers !== 'number' || !Number.isSafeInteger(value.correct_answers) || value.correct_answers < 0 ||
      value.correct_answers > value.total_answers ||
      !(value.correct_rate === null || (typeof value.correct_rate === 'number' && Number.isFinite(value.correct_rate) && value.correct_rate >= 0 && value.correct_rate <= 100)) ||
      !(value.explanation == null || typeof value.explanation === 'string')) return invalid()
  const extra = record(detail) ? detail : null
  const rules: { rule_number: number; title_ja: string | null }[] = []
  if (extra && Array.isArray(extra.rules)) for (const rule of extra.rules) {
    if (record(rule) && typeof rule.rule_number === 'number' && Number.isSafeInteger(rule.rule_number) && rule.rule_number > 0 &&
        (rule.title_ja === null || typeof rule.title_ja === 'string')) rules.push({rule_number:rule.rule_number,title_ja:rule.title_ja})
  }
  return { is_correct:value.is_correct, correct_option_id:value.correct_option_id,
    explanation:extra && typeof extra.explanation === 'string' ? extra.explanation : (value.explanation ?? null) as string | null,
    rules, total_answers:value.total_answers, correct_answers:value.correct_answers,
    correct_rate:value.total_answers >= 10 ? value.correct_rate as number | null : null }
}
