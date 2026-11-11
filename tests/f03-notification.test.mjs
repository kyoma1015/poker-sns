import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { stripTypeScriptTypes } from 'node:module'
import vm from 'node:vm'

const baseline = process.env.F03_BASELINE_ROOT
test('notification entry points use verified events and the saved comment ID', () => {
  const source = path => baseline
    ? readFileSync(join(baseline, path), 'utf8')
    : readFileSync(new URL(`../${path}`, import.meta.url), 'utf8')
  for (const path of ['src/Timeline.tsx', 'src/PostDetail.tsx', 'src/PlayerProfile.tsx']) {
    assert.equal(/\.from\('notifications'\)\s*\.insert\(/.test(source(path)), false, path)
  }
  assert.match(source('src/PostDetail.tsx'), /createVerifiedNotification\('comment', savedComment\.id\)/)
})

if (!baseline) {
  const code = stripTypeScriptTypes(readFileSync(new URL('../src/createVerifiedNotification.ts', import.meta.url), 'utf8'))
    .replace(/import \{ supabase \} from '\.\/supabase'\s*/, '')
    .replace('export async function', 'async function') + '\ncreateVerifiedNotification'

  async function run(t, replies) {
    t.mock.timers.enable({ apis: ['setTimeout', 'Date'], now: 1000 })
    const calls = []
    const supabase = { rpc(name, args) {
      const call = { name, args, aborted: false }
      calls.push(call)
      return { abortSignal(signal) {
        signal.addEventListener('abort', () => { call.aborted = true })
        const reply = replies[Math.min(calls.length - 1, replies.length - 1)]
        if (reply === 'hang') return new Promise(() => {})
        if (reply instanceof Error) return Promise.reject(reply)
        return Promise.resolve(reply)
      } }
    } }
    const fn = vm.runInNewContext(code, { supabase, AbortController, Date, setTimeout, clearTimeout, Error })
    let settled = false
    const started = Date.now()
    const result = fn('comment', 'saved-comment-id').then(value => { settled = true; return value })
    for (let i = 0; i < 160 && !settled; i++) {
      for (let j = 0; j < 12; j++) await Promise.resolve()
      if (!settled) t.mock.timers.tick(100)
    }
    assert.equal(settled, true, 'RPC must finish within its total budget')
    const value = await result
    for (const call of calls) {
      assert.equal(call.name, 'create_verified_notification')
      assert.equal(call.args.p_event_type, 'comment')
      assert.equal(call.args.p_event_id, 'saved-comment-id')
    }
    return { value, calls, elapsed: Date.now() - started }
  }

  test('successful verified event returns null once', async t => {
    const r = await run(t, [{ error: null, status: 200 }])
    assert.equal(r.value, null); assert.equal(r.calls.length, 1)
  })
  for (const [status, code] of [[401, 'unauthorized'], [403, 'denied'], [400, '22023'], [200, '42501']]) {
    test(`authorization/validation ${status}/${code} is never retried`, async t => {
      const r = await run(t, [{ error: { code, message: 'denied' }, status }])
      assert.equal(r.calls.length, 1); assert.equal(r.value.code, code)
    })
  }
  for (const status of [429, 500, 503]) {
    test(`HTTP ${status} retries with the same event and recovers`, async t => {
      const r = await run(t, [{ error: { message: 'transient' }, status }, { error: null, status: 200 }])
      assert.equal(r.value, null); assert.equal(r.calls.length, 2)
    })
  }
  test('network failure is retried at most three times', async t => {
    const r = await run(t, [new Error('Failed to fetch')])
    assert.equal(r.calls.length, 3); assert.match(r.value.message, /Failed to fetch/)
  })
  test('transport ignoring abort still finishes and aborts each of three attempts', async t => {
    const r = await run(t, ['hang'])
    assert.equal(r.calls.length, 3)
    assert.ok(r.calls.every(c => c.aborted))
    assert.equal(r.value.code, 'NOTIFICATION_TIMEOUT')
    assert.ok(r.elapsed <= 15000)
  })
}
