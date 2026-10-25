// Synthetic transport only. The test browser aborts every non-local request.
const qa = {
  userId: 'me' as string | null,
  rejectUserOnce: false, errorUserOnce: false,
  authListeners: new Set<(event: string, session: unknown) => void>(),
  insideAuthCallback: false, authCallsInsideCallback: 0,
  readUpdates: 0,
  channels: [] as Array<{ handler: (payload: any) => unknown, active: boolean }>,
  emitAuth(id: string | null, event = id ? 'SIGNED_IN' : 'SIGNED_OUT') {
    this.userId = id
    this.insideAuthCallback = true
    try { for (const callback of this.authListeners) callback(event, id ? { user: { id } } : null) }
    finally { this.insideAuthCallback = false }
  },
  holdBlocks: false, holdInsert: false, rejectInsert: false,
  errorInsert: false, blockError: false, rejectReload: false,
  holdOldMessages: false,
  oldMessages: [] as Array<(x: unknown) => void>,
  checks: [] as Array<(x: unknown) => void>, inserts: [] as unknown[],
  insertWaiters: [] as Array<(x: unknown) => void>,
  release() { this.holdBlocks = false; this.checks.splice(0).forEach(done => done({ data: [], error: null })) },
  finish() { this.holdInsert = false; this.insertWaiters.splice(0).forEach(done => done({ error: null })) },
}
;(window as any).dmQA = qa
function query(table: string) {
  let peer = ''
  let filter = ''
  const chain: any = {
    select() { return chain }, eq(key: string, value: string) { if (key === 'id') peer = value; return chain }, is() { return chain }, or(value: string) { filter = value; return chain }, update() { qa.readUpdates++; return chain },
    maybeSingle() { return Promise.resolve({ data: { display_name: peer === 'third' ? 'Another synthetic player' : 'Synthetic player', poker_id: 'synthetic', avatar_url: null }, error: null }) },
    order() {
      if (qa.holdOldMessages && filter.includes('other')) return new Promise(done => qa.oldMessages.push(done))
      return Promise.resolve({ data: filter.includes('third') ? [{ id: 'third-message', sender_id: 'third', receiver_id: qa.userId, content: qa.userId === 'newme' ? 'NEW_ACCOUNT_SYNTHETIC' : 'THIRD_SYNTHETIC', created_at: '2026-10-24T00:00:00Z', read_at: null }] : [], error: null })
    },
    insert(value: unknown) {
      qa.inserts.push(value)
      if (qa.rejectInsert) { qa.rejectInsert = false; return Promise.reject(new Error('SYNTHETIC_PRIVATE_ERROR')) }
      if (qa.errorInsert) { qa.errorInsert = false; return Promise.resolve({ error: { message: 'SYNTHETIC_PRIVATE_ERROR' } }) }
      if (qa.holdInsert) return new Promise(done => qa.insertWaiters.push(done))
      return Promise.resolve({ error: null })
    },
    then(resolve: any, reject: any) {
      const result = table === 'user_blocks' && qa.holdBlocks
        ? new Promise(done => qa.checks.push(done))
        : Promise.resolve({ data: [], error: table === 'user_blocks' && qa.blockError ? { message: 'SYNTHETIC_PRIVATE_ERROR' } : null })
      return result.then(resolve, reject)
    },
  }
  return chain
}
export const supabase = {
  auth: { getUser: async () => {
    if (qa.insideAuthCallback) qa.authCallsInsideCallback++
    if (qa.rejectUserOnce) { qa.rejectUserOnce = false; throw new Error('SYNTHETIC_PRIVATE_AUTH') }
    if (qa.errorUserOnce) { qa.errorUserOnce = false; return { data: { user: { id: qa.userId } }, error: { message: 'SYNTHETIC_PRIVATE_AUTH' } } }
    if (qa.rejectReload && qa.inserts.length) throw new Error('SYNTHETIC_PRIVATE_ERROR')
    return { data: { user: qa.userId ? { id: qa.userId } : null }, error: null }
  }, onAuthStateChange(callback: (event: string, session: unknown) => void) {
    qa.authListeners.add(callback)
    queueMicrotask(() => { if (qa.authListeners.has(callback)) callback('INITIAL_SESSION', qa.userId ? { user: { id: qa.userId } } : null) })
    return { data: { subscription: { unsubscribe() { qa.authListeners.delete(callback) } } } }
  } },
  from: query,
  channel() {
    const channel: any = { active: true, handler: () => {}, on(_type: unknown, _filter: unknown, handler: (payload: any) => unknown) { channel.handler = handler; return channel }, subscribe() { qa.channels.push(channel); return channel } }
    return channel
  },
  removeChannel(channel: { active: boolean }) { channel.active = false },
}
