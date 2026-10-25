import assert from 'node:assert/strict'
import test from 'node:test'
import handler, { createVideoFinalizeHandler } from '../api/video-finalize.ts'

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

test('injected finalize adapter cannot enable publishing against a production origin', async () => {
  const previousUrl = process.env.VITE_SUPABASE_URL
  const previousAnon = process.env.VITE_SUPABASE_ANON_KEY
  process.env.VITE_SUPABASE_URL = 'https://example.supabase.co'
  process.env.VITE_SUPABASE_ANON_KEY = 'test-anon'
  const adapters = {
    authenticate: async () => { throw new Error('must never be invoked') },
    snapshot: async () => { throw new Error('must never be invoked') },
    currentGeneration: async () => { throw new Error('must never be invoked') },
    publish: async () => { throw new Error('must never be invoked') },
    reconcile: async () => { throw new Error('must never be invoked') },
  }
  try {
    const res = response()
    await createVideoFinalizeHandler(adapters, { isolatedLocalOnly: true })(request(), res)
    assert.notEqual(res.statusCode, 201)
  } finally {
    if (previousUrl === undefined) delete process.env.VITE_SUPABASE_URL
    else process.env.VITE_SUPABASE_URL = previousUrl
    if (previousAnon === undefined) delete process.env.VITE_SUPABASE_ANON_KEY
    else process.env.VITE_SUPABASE_ANON_KEY = previousAnon
  }
})

test('runtime attestation never exposes a production GET endpoint', async () => {
  const previous = process.env.VERCEL_ENV
  process.env.VERCEL_ENV = 'production'
  try {
    const res = response()
    await handler(request({ method: 'GET', query: { runtime_attestation: 'ffprobe' } }), res)
    assert.equal(res.statusCode, 404)
    assert.equal(res.headers['Cache-Control'], 'no-store, private')
  } finally {
    if (previous === undefined) delete process.env.VERCEL_ENV
    else process.env.VERCEL_ENV = previous
  }
})

test('preview runtime attestation fails closed for missing absolute ffprobe binary', async () => {
  const previousEnv = process.env.VERCEL_ENV
  const previousBinary = process.env.FFPROBE_BINARY_PATH
  process.env.VERCEL_ENV = 'preview'
  process.env.FFPROBE_BINARY_PATH = '/nonexistent-poker-id-ffprobe/ffprobe'
  try {
    const res = response()
    await handler(request({ method: 'GET', query: { runtime_attestation: 'ffprobe' } }), res)
    assert.equal(res.statusCode, 503)
    assert.deepEqual(res.body, { ffprobe: 'unavailable' })
  } finally {
    if (previousEnv === undefined) delete process.env.VERCEL_ENV
    else process.env.VERCEL_ENV = previousEnv
    if (previousBinary === undefined) delete process.env.FFPROBE_BINARY_PATH
    else process.env.FFPROBE_BINARY_PATH = previousBinary
  }
})
