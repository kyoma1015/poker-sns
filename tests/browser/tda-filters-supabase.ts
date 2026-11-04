// Synthetic optional-filter transport; never instantiates a real DB client.
const scenario = new URLSearchParams(location.search).get('case')
const calls: { name: string; args: unknown }[] = []
Object.assign(window, { tdaFilterCalls: calls, tdaFilterResponseDelivered: false })
const question = { question_id: 'synthetic-filter-q1', question_text: 'QA用の合成問題', difficulty: null, category: null,
  options: [{ id: 'a', option_order: 0, option_text: '合成選択肢A' }, { id: 'b', option_order: 1, option_text: '合成選択肢B' }] }
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
  rpc: async (name: string, args: unknown) => {
    calls.push({ name, args })
    if (name === 'get_tda_quiz_filters') {
      const filters = scenario === 'bad-difficulty' ? { difficulties: [{ bad: true }], categories: ['MTT'] }
        : scenario === 'bad-category' ? { difficulties: ['BEGINNER'], categories: [{ bad: true }] }
        : scenario === 'mixed-items' ? { difficulties: ['BEGINNER', {}, null, 7, ['nested']], categories: ['MTT', false, { bad: true }] }
        : { difficulties: ['BEGINNER', 'ADVANCED'], categories: ['MTT', 'RING'] }
      Object.assign(window, { tdaFilterResponseDelivered: true })
      return { data: [filters], error: null }
    }
    if (name === 'get_tda_quiz_questions') return { data: [question], error: null }
    throw new Error('Unexpected synthetic test RPC')
  },
}
