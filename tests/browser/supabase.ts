// Test-only in-memory transport. No client library or environment credentials.
const calls: { name: string; args: unknown }[] = []
Object.assign(window, { qaRpcCalls: calls })
const user = { id: 'qa-user' }
export const supabase = {
  auth: {
    onAuthStateChange: (callback: (event: string, session: { user: typeof user }) => void) => {
      let active = true
      queueMicrotask(() => { if (active) callback('INITIAL_SESSION', { user }) })
      return { data: { subscription: { unsubscribe: () => { active = false } } } }
    },
    getUser: async () => ({ data: { user }, error: null }),
    getSession: async () => ({ data: { session: { user } }, error: null }),
  },
  from: () => {
    const query: any = new Proxy({}, { get: (_, key) => key === 'then'
      ? (resolve: (value: unknown) => void) => Promise.resolve({ data: [], error: null }).then(resolve)
      : () => query })
    return query
  },
  rpc: async (name: string, args: unknown) => { calls.push({ name, args }); return { data: [], error: null } },
}
