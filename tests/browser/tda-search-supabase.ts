// Isolated synthetic transport. No real Supabase client, credentials or network.
const pending: { resolve: (value: unknown) => void; reject: (reason: Error) => void }[] = []
const calls: string[] = []
Object.assign(window, { tdaSearchQA: {
  calls,
  resolve: (index: number, label: string) => pending[index].resolve({ data: [{ rule_number: index + 1, title_ja: label, summary_ja: null, conclusion_ja: null, explanation_ja: null }], error: null }),
  resolveRaw: (index: number, data: unknown) => pending[index].resolve({ data, error: null }),
  fail: (index: number) => pending[index].resolve({ data: null, error: { message: 'synthetic search error' } }),
  reject: (index: number) => pending[index].reject(new Error('synthetic disconnected search')),
} })
export const supabase = {
  auth: { getUser: async () => ({ data: { user: null }, error: null }) },
  rpc: (name: string, args: { search_text?: string }) => {
    if (name !== 'search_tda_rules') return Promise.resolve({ data: [], error: null })
    calls.push(args.search_text || '')
    return new Promise((resolve, reject) => pending.push({ resolve, reject }))
  },
}
