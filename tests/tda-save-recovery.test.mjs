import test from 'node:test'
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'

test('quiz save uncertainty cannot duplicate writes or fabricate a score and remains navigable', { timeout: 30000 }, () => {
  const result = spawnSync(process.execPath, ['tests/browser/tda-save-recovery.mjs'], {
    cwd: process.cwd(), encoding: 'utf8', timeout: 27000,
  })
  assert.equal(result.error, undefined, 'bounded actual React browser run must complete')
  assert.equal(result.status, 0, result.stdout + result.stderr)
  const reports = result.stdout.split('\n').filter(line => line.startsWith('{')).map(line => JSON.parse(line))
  assert.equal(reports.at(-1)?.verdict, 'PASS')
  assert.equal(reports.at(-1)?.tests, 8)
})

// Use the locked production SDK with an injected fetch, never a real endpoint.
// The installed SDK (unlike a general docs example) excludes POST from retries.
for (const outcome of ['service-unavailable', 'network-rejection', 'permission-rejection']) {
  test('installed SDK answer POST is sent once on ' + outcome, async () => {
    const { createClient } = await import('@supabase/supabase-js')
    const { safeQuizRpc } = await import('../src/tdaQuizData.ts')
    const requests = []
    const client = createClient('https://synthetic.invalid', 'synthetic-public-key', {
      auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
      global: { fetch: async (url, options) => {
        requests.push({ url: String(url), method: options.method, body: JSON.parse(options.body) })
        if (outcome === 'network-rejection') throw new TypeError('synthetic transport rejection')
        return new Response(JSON.stringify({code: outcome === 'permission-rejection' ? '42501' : '503', message:'synthetic rejection'}), {
          status: outcome === 'permission-rejection' ? 403 : 503, headers: {'Content-Type':'application/json'},
        })
      } },
    })
    const result = await safeQuizRpc(() => client.rpc('submit_tda_quiz_answer', {p_question_id:'synthetic-q1',p_selected_option_id:'b'}))
    assert.ok(result.error)
    assert.equal(requests.length, 1)
    assert.equal(requests[0].method, 'POST')
    assert.equal(requests[0].url, 'https://synthetic.invalid/rest/v1/rpc/submit_tda_quiz_answer')
    assert.deepEqual(requests[0].body, {p_question_id:'synthetic-q1',p_selected_option_id:'b'})
  })
}
