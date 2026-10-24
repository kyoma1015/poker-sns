import assert from 'node:assert/strict'
import test from 'node:test'
import handler from '../api/video-finalize.ts'

function response() {
  return {
    statusCode: 200,
    headers: {},
    body: null,
    setHeader(key, value) { this.headers[key] = value; return this },
    status(code) { this.statusCode = code; return this },
    json(value) { this.body = value; return this },
    end() { return this },
  }
}
const request = overrides => ({
  method: 'POST',
  headers: { authorization: 'Bearer test.token', 'content-type': 'application/json', 'content-length': '1' },
  body: { object_path: '11111111-1111-4111-8111-111111111111/22222222-2222-4222-8222-222222222222.mp4', content: '' },
  ...overrides,
})
test('default finalize route rejects non-POST before network', async () => {
  const res = response()
  await handler(request({ method: 'GET' }), res)
  assert.equal(res.statusCode, 405)
  assert.equal(res.headers['Cache-Control'], 'no-store, private')
})
test('default finalize route rejects missing bearer before network', async () => {
  const res = response()
  await handler(request({ headers: { authorization: '' } }), res)
  assert.equal(res.statusCode, 401)
})
test('default finalize route rejects invalid Storage path before network', async () => {
  const res = response()
  await handler(request({ body: { object_path: 'bad.mp4', content: '' } }), res)
  assert.equal(res.statusCode, 400)
})
test('default finalize route rejects unconfigured backend without mutation', async () => {
  const res = response()
  await handler(request(), res)
  assert.equal(res.statusCode, 503)
})
