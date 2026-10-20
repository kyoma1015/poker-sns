export type Question = {
  id: string
  key: string
  order: number
  text: string
  options: { id: string; order: number; text: string }[]
}

// Accept exactly one complete, internally consistent 50-question bank.
export function parseQuestions(data: unknown): Question[] {
  if (!Array.isArray(data)) throw new Error('設問データの形式が正しくありません。')
  const map = new Map<string, Question>()
  const optionIds = new Set<string>()
  const nonempty = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0
  for (const row of data) {
    if (!row || !nonempty(row.question_id) || !nonempty(row.question_key) ||
        !nonempty(row.question_text) || !nonempty(row.option_id) || !nonempty(row.option_text) ||
        !Number.isInteger(row.question_order) || row.question_order < 1 || row.question_order > 50 ||
        !Number.isInteger(row.option_order) || row.option_order < 1 || row.option_order > 26 ||
        optionIds.has(row.option_id)) throw new Error('設問または選択肢に不備があります。')
    optionIds.add(row.option_id)
    let question = map.get(row.question_id)
    if (!question) {
      question = { id: row.question_id, key: row.question_key, order: row.question_order, text: row.question_text, options: [] }
      map.set(question.id, question)
    }
    if (question.key !== row.question_key || question.order !== row.question_order || question.text !== row.question_text ||
        question.options.some(option => option.order === row.option_order)) throw new Error('設問の情報が一致しません。')
    question.options.push({ id: row.option_id, order: row.option_order, text: row.option_text })
  }
  const questions = [...map.values()].sort((a, b) => a.order - b.order)
  if (questions.length !== 50 || new Set(questions.map(q => q.key)).size !== 50 ||
      questions.some((q, i) => q.order !== i + 1 || q.options.length < 2)) throw new Error('全50問を読み込めませんでした。')
  for (const question of questions) {
    question.options.sort((a, b) => a.order - b.order)
    if (question.options.some((option, i) => option.order !== i + 1)) throw new Error('選択肢の順序が正しくありません。')
  }
  return questions
}

// Ignore responses from older navigations, restarts, and unmounted components.
export class LatestRequest {
  private generation = 0
  start() { return ++this.generation }
  isCurrent(generation: number) { return generation === this.generation }
  invalidate() { ++this.generation }
}
