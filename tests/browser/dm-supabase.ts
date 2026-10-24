// Synthetic transport only. The test browser aborts every non-local request.
const qa = {
  holdBlocks: false, holdInsert: false, rejectInsert: false,
  errorInsert: false, blockError: false, rejectReload: false,
  checks: [] as Array<(x: unknown) => void>, inserts: [] as unknown[],
  insertWaiters: [] as Array<(x: unknown) => void>,
  release() { this.holdBlocks = false; this.checks.splice(0).forEach(done => done({ data: [], error: null })) },
  finish() { this.holdInsert = false; this.insertWaiters.splice(0).forEach(done => done({ error: null })) },
}
;(window as any).dmQA = qa
function query(table: string) {
  const chain: any = {
    select() { return chain }, eq() { return chain }, is() { return chain }, or() { return chain }, update() { return chain },
    maybeSingle() { return Promise.resolve({ data: { display_name: 'Synthetic player', poker_id: 'synthetic', avatar_url: null }, error: null }) },
    order() { return Promise.resolve({ data: [], error: null }) },
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
    if (qa.rejectReload && qa.inserts.length) throw new Error('SYNTHETIC_PRIVATE_ERROR')
    return { data: { user: { id: 'me' } }, error: null }
  } },
  from: query,
  channel() { const channel: any = { on() { return channel }, subscribe() { return channel } }; return channel },
  removeChannel() {},
}
