// Test-only transport: no real client, network or user records.
const scenario = new URLSearchParams(location.search).get('case')
let questionCalls = 0
let submitCalls = 0
let detailCalls = 0
const calls: string[] = []
Object.assign(window, { tdaQaCalls: calls })
const question = { question_id: 'synthetic-q1', question_text: 'QA用の合成問題', difficulty: null, category: null,
  options: [{ id: 'a', option_order: 2, option_text: '合成選択肢A' }, { id: 'b', option_order: 1, option_text: '合成選択肢B' }] }
export const supabase = {
  auth: {
    onAuthStateChange: (callback: (event: string, session: unknown) => void) => {
      let active = true
      queueMicrotask(() => { if (active) callback('INITIAL_SESSION', {user:{id:'qa-only'}}) })
      return {data:{subscription:{unsubscribe:()=>{ active = false }}}}
    },
    getUser: async () => ({ data: { user: { id: 'qa-only' } }, error: null }),
    getSession: async () => ({ data: { session: {} }, error: null }),
  },
  from: () => {
    const query: any = new Proxy({}, { get: (_, key) => key === 'then'
      ? (resolve: (value: unknown) => void) => Promise.resolve({ data: [], error: null }).then(resolve)
      : () => query })
    return query
  },
  rpc: async (name: string) => {
    calls.push(name)
    if (name === 'get_tda_quiz_filters') return { data: [{ difficulties: [], categories: [] }], error: null }
    if (['get_tda_quiz_questions','get_tda_quiz_hard_questions','get_my_wrong_tda_quiz_questions'].includes(name)) {
      questionCalls++
      if (scenario === 'throw-once' && questionCalls === 1) throw new Error('Synthetic transport failure')
      return { data: ['uncertain-then-next','detail-late'].includes(scenario ?? '') ? [question, { ...question, question_id: 'synthetic-q2', question_text: 'QA用の合成問題2' }] : [scenario === 'malformed' ? { ...question, options: null } : question], error: null }
    }
    if (name === 'submit_tda_quiz_answer') {
      submitCalls++
      if ((scenario === 'save-throws' || scenario === 'uncertain-then-next') && submitCalls === 1) throw new Error('Synthetic unknown commit outcome')
      if (scenario === 'save-empty') return { data: [], error: null }
      if (scenario === 'permission-once' && submitCalls === 1) return { data: null, error: {code:'42501',message:'permission denied for function'} }
      return { data: [{ is_correct: scenario === 'malformed-answer' ? 'false' : true, correct_option_id: 'b', explanation: '保存済みの合成解説', total_answers: 1, correct_answers: 1, correct_rate: null }], error: null }
    }
    if (name === 'check_tda_quiz_answer' && scenario === 'detail-late' && ++detailCalls === 1) return new Promise(resolve => { Object.assign(window, { resolveTdaDetail: () => resolve({ data: [{ explanation: '遅延した前問の解説', rules: [] }], error: null }) }) })
    if (name === 'check_tda_quiz_answer' && scenario === 'detail-never') return new Promise(() => {})
    if (name === 'check_tda_quiz_answer' && scenario === 'detail-throws') throw new Error('Synthetic optional detail outage')
    return { data: [], error: null }
  },
}
