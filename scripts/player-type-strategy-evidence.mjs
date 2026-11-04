// Receives the offline audit's validated question/score snapshot only.
// These are literal search queries requested for review, not a scoring rubric.
const terms = ['ブラフ', 'ポラライズ', 'レンジ', 'ハンド', '強い相手', '弱い相手', 'バランス', 'エクスプロイト']

export function buildStrategyReviewEvidence(questions, scores, dimensionKeys) {
  return {
    method: 'exact literal question/option substring search and raw option-score contrasts',
    semanticValidity: 'BLOCKED: authoritative strategy rubric and expert labels unavailable; presence or absence of a word does not establish conceptual coverage',
    classifier: 'NOT EXECUTED',
    optionCount: questions.reduce((total, question) => total + question.options.length, 0),
    queries: terms.map(term => ({ term, matches: questions.flatMap(question => {
      const questionMatch = question.text.includes(term)
      const optionOrders = question.options.filter(option => option.text.includes(term)).map(option => option.order)
      return questionMatch || optionOrders.length ? [{ questionOrder: question.order, questionMatch, optionOrders }] : []
    }) })),
    questions: questions.map(question => ({
      order: question.order, text: question.text, optionIds: question.options.map(option => option.id),
      contrasts: dimensionKeys.flatMap(key => {
        const values = question.options.map(option => scores.get(option.id)[key])
        return new Set(values).size > 1 ? [{ key, baseline: values[0], differences: values.map(value => value - values[0]) }] : []
      }),
    })),
  }
}
