// In-memory identity and RPC boundaries. No client, credentials, network or DB.
let identity: string | null = 'account-a'
let inCallback = false
let deferAuth = false
let deferQuestions = false
let deferSubmit = false
let deferDetail = false
let resolveAuth: (() => void) | undefined
let resolveQuestions: (() => void) | undefined
let resolveSubmit: (() => void) | undefined
let resolveDetail: (() => void) | undefined
const listeners = new Set<(event: string, session: unknown) => unknown>()
const calls: {name: string; account: string | null}[] = []
let callbackSdkCalls = 0
let asyncCallbacks = 0
let unsubscribed = 0
const question = (id: string | null) => ({ question_id: `${id}-q`, question_text: `${id}の合成問題`, difficulty: null, category: null,
  options: [{ id: 'a', option_order: 1, option_text: '合成A' }, { id: 'b', option_order: 2, option_text: '合成B' }] })
const session = () => identity ? {user:{id:identity}} : null
function authCall() { if (inCallback) callbackSdkCalls++ }
const qa = {
  calls,
  emit: (id: string | null, event = id ? 'SIGNED_IN' : 'SIGNED_OUT') => {
    identity = id; inCallback = true
    try { for (const callback of listeners) if (callback(event, session()) instanceof Promise) asyncCallbacks++ }
    finally { inCallback = false }
  },
  silentlyChange: (id: string | null) => { identity = id },
  defer: (kind: string) => {
    if (kind === 'auth') deferAuth = true
    if (kind === 'questions') deferQuestions = true
    if (kind === 'submit') deferSubmit = true
    if (kind === 'detail') deferDetail = true
  },
  resolve: (kind: string) => {
    if (kind === 'auth') resolveAuth?.()
    if (kind === 'questions') resolveQuestions?.()
    if (kind === 'submit') resolveSubmit?.()
    if (kind === 'detail') resolveDetail?.()
  },
  stats: () => ({callbackSdkCalls,asyncCallbacks,unsubscribed,listeners:listeners.size}),
}
Object.assign(window, { tdaAccountQa: qa })
export const supabase = {
  auth: {
    onAuthStateChange: (callback: (event: string, session: unknown) => unknown) => {
      listeners.add(callback)
      queueMicrotask(() => { if (listeners.has(callback)) { inCallback = true; try { if (callback('INITIAL_SESSION', session()) instanceof Promise) asyncCallbacks++ } finally { inCallback = false } } })
      return {data:{subscription:{unsubscribe:()=>{ listeners.delete(callback); unsubscribed++ }}}}
    },
    getSession: async () => { authCall(); return {data:{session:session()},error:null} },
    getUser: async () => {
      authCall(); const captured = identity
      const result = {data:{user:captured ? {id:captured} : null},error:null}
      if (deferAuth) { deferAuth = false; return new Promise(resolve => { resolveAuth = () => resolve(result) }) }
      return result
    },
  },
  rpc: async (name: string) => {
    if (inCallback) callbackSdkCalls++
    const captured = identity
    calls.push({name,account:captured})
    if (name === 'get_tda_quiz_filters') return {data:[{difficulties:[],categories:[]}],error:null}
    if (['get_tda_quiz_questions','get_tda_quiz_hard_questions','get_my_wrong_tda_quiz_questions'].includes(name)) {
      const result = {data:[question(captured)],error:null}
      if (deferQuestions) {deferQuestions = false; return new Promise(resolve => {resolveQuestions = () => resolve(result)})}
      return result
    }
    if (name === 'submit_tda_quiz_answer') {
      const result = {data:[{is_correct:true,correct_option_id:'b',explanation:`${captured}の保存済み解説`,total_answers:1,correct_answers:1,correct_rate:null}],error:null}
      if (deferSubmit) {deferSubmit = false; return new Promise(resolve => {resolveSubmit = () => resolve(result)})}
      return result
    }
    if (name === 'check_tda_quiz_answer') {
      const result = {data:[{explanation:`${captured}の追加解説`,rules:[]}],error:null}
      if (deferDetail) {deferDetail = false; return new Promise(resolve => {resolveDetail = () => resolve(result)})}
      return result
    }
    return {data:[],error:null}
  },
}
