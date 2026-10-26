// Synthetic browser transport. No production credentials, HTTP or persistence.
const qa = {
  userId: 'me' as string | null, rejectAuth: false, errorAuth: false,
  rejectMessages: false, rejectProfiles: false, errorBlocks: false,
  holdMessages: false, pending: [] as Array<(value: unknown) => void>,
  messageReads: 0, filters: [] as string[], insideAuth: false, reentrant: 0,
  listeners: new Set<(event: string, session: unknown) => void>(),
  channels: [] as Array<any>, content: 'PRIVATE_OLD_MESSAGE', extraRows: [] as any[],
  rows(id = this.userId, content = this.content) { return [{ id: 'synthetic', sender_id: 'peer', receiver_id: id, content, created_at: '2026-10-25T00:00:00Z', read_at: null }, ...this.extraRows] },
  emit(id: string | null, event = id ? 'SIGNED_IN' : 'SIGNED_OUT') { this.userId = id; this.insideAuth = true; try { this.listeners.forEach(fn => fn(event, id ? { user: { id } } : null)) } finally { this.insideAuth = false } },
  release(content = 'LATE_OLD_MESSAGE') { this.holdMessages = false; this.pending.splice(0).forEach(done => done({ data: this.rows('me', content), error: null })) },
  realtime() { this.channels.filter(c => c.active).forEach(c => c.handler({ new: {} })) },
}
;(window as any).inboxQA = qa
function query(table: string) {
 const chain: any = {
  select() { return chain }, or(filter: string) { if (table === 'direct_messages') qa.filters.push(filter); return chain },
  in() { return chain },
  order() { qa.messageReads++; const data = qa.rows(qa.userId, qa.userId === 'newme' ? 'PRIVATE_NEW_MESSAGE' : qa.content); if (qa.rejectMessages) { qa.rejectMessages = false; return Promise.reject(new Error('SYNTHETIC_PRIVATE_BACKEND')) } if (qa.holdMessages) return new Promise(done => qa.pending.push(done)); return Promise.resolve({ data, error: null }) },
  then(resolve: any, reject: any) { if (table === 'profiles' && qa.rejectProfiles) { qa.rejectProfiles = false; return Promise.reject(new Error('SYNTHETIC_PRIVATE_PROFILE')).then(resolve, reject) } return Promise.resolve(table === 'user_blocks' ? { data: [], error: qa.errorBlocks ? { message: 'SYNTHETIC_PRIVATE_BLOCK' } : null } : { data: [{ id: 'peer', display_name: 'Synthetic peer', poker_id: 'synthetic', avatar_url: null }], error: null }).then(resolve, reject) },
 }; return chain
}
export const supabase = {
 auth: { async getUser() { if (qa.insideAuth) qa.reentrant++; if (qa.rejectAuth) { qa.rejectAuth = false; throw new Error('SYNTHETIC_PRIVATE_AUTH') } return { data: { user: qa.userId ? { id: qa.userId } : null }, error: qa.errorAuth ? { message: 'SYNTHETIC_PRIVATE_AUTH' } : null } },
 onAuthStateChange(fn: any) { qa.listeners.add(fn); queueMicrotask(() => { if (qa.listeners.has(fn)) fn('INITIAL_SESSION', qa.userId ? { user: { id: qa.userId } } : null) }); return { data: { subscription: { unsubscribe() { qa.listeners.delete(fn) } } } } } },
 from: query,
 channel() { const c: any = { active: true, handler: () => {}, on(_a: any, _b: any, handler: any) { c.handler = handler; return c }, subscribe() { qa.channels.push(c); return c } }; return c },
 removeChannel(c: any) { c.active = false },
}
