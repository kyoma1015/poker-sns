import test from 'node:test'
import assert from 'node:assert/strict'
import { checkQuizAuthentication } from '../src/tdaQuizAuth.ts'

function auth({ session = {}, sessionError = null, user = {}, userError = null, throws = false } = {}) {
  let calls = 0
  return {
    getSession: async () => ({ data: { session }, error: sessionError }),
    getUser: async () => {
      calls++
      if (throws) throw new Error('network down')
      return { data: { user }, error: userError }
    },
    calls: () => calls,
  }
}
test('guest cannot start and does not make a user lookup', async () => {
  const a = auth({ session: null })
  const r = await checkQuizAuthentication(a)
  assert.equal(r.requiresLogin, true); assert.equal(a.calls(), 0)
})
test('valid session and verified user can answer', async () => {
  assert.deepEqual(await checkQuizAuthentication(auth()), { ok: true })
})
for (const issue of [{ status: 0 }, { status: 503 }, { name: 'AuthRetryableFetchError' }]) {
  test(`user lookup transport error ${JSON.stringify(issue)} keeps retry guidance`, async () => {
    const r = await checkQuizAuthentication(auth({ userError: issue }))
    assert.equal(r.ok, false); assert.equal(r.requiresLogin, false)
    assert.match(r.message, /通信状況/)
  })
}
for (const issue of [{ status: 401 }, { code: 'session_not_found' }, { name: 'AuthSessionMissingError' }]) {
  test(`expired authentication ${JSON.stringify(issue)} asks for login`, async () => {
    const r = await checkQuizAuthentication(auth({ userError: issue }))
    assert.equal(r.ok, false); assert.equal(r.requiresLogin, true)
  })
}
test('session transport error does not claim expiry', async () => {
  const a = auth({ sessionError: { status: 503 } })
  const r = await checkQuizAuthentication(a)
  assert.equal(r.requiresLogin, false); assert.equal(a.calls(), 0)
})
test('thrown transport error does not escape the UI action', async () => {
  const r = await checkQuizAuthentication(auth({ throws: true }))
  assert.equal(r.requiresLogin, false)
})
test('missing verified user asks for login', async () => {
  const r = await checkQuizAuthentication(auth({ user: null }))
  assert.equal(r.requiresLogin, true)
})
