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

// A deployment flag and apparently valid runtime secrets are not sufficient
// to authorize production publication before the independent DB/RLS release gate.
test('production attested adapter stays fail-closed with release flag and keys present', async () => {
  const { createProductionSupabaseVideoAdapters } = await import('../api/video-production-supabase-adapters.ts')
  const names = ['VIDEO_PRODUCTION_FENCED_READY', 'VIDEO_ATTESTATION_KEY_HEX', 'VIDEO_ATTESTATION_KEY_ID', 'VIDEO_ATTESTED_RPC_RELEASE_APPROVED']
  const previous = Object.fromEntries(names.map(name => [name, process.env[name]]))
  try {
    process.env.VIDEO_PRODUCTION_FENCED_READY = 'true'
    process.env.VIDEO_ATTESTATION_KEY_HEX = 'a'.repeat(64)
    process.env.VIDEO_ATTESTATION_KEY_ID = '2'
    delete process.env.VIDEO_ATTESTED_RPC_RELEASE_APPROVED
    assert.throws(() => createProductionSupabaseVideoAdapters(
      'https://example.supabase.co', 'fixture-anon', 'fixture-user-jwt',
    ), /production video publish requires provisioned server-attested database authorization/)
  } finally {
    for (const name of names) {
      if (previous[name] === undefined) delete process.env[name]
      else process.env[name] = previous[name]
    }
  }
})

test('production reservation cannot be enabled by a release flag and HMAC keys', async () => {
  const names = ['VITE_SUPABASE_URL', 'VITE_SUPABASE_ANON_KEY', 'VIDEO_PRODUCTION_FENCED_READY',
    'VIDEO_ATTESTATION_KEY_HEX', 'VIDEO_ATTESTATION_KEY_ID']
  const previous = Object.fromEntries(names.map(name => [name, process.env[name]]))
  try {
    process.env.VITE_SUPABASE_URL = 'https://example.supabase.co'
    process.env.VITE_SUPABASE_ANON_KEY = 'fixture-anon'
    process.env.VIDEO_PRODUCTION_FENCED_READY = 'true'
    process.env.VIDEO_ATTESTATION_KEY_HEX = 'a'.repeat(64)
    process.env.VIDEO_ATTESTATION_KEY_ID = '2'
    const body = { action: 'reserve', object_path: '11111111-1111-4111-8111-111111111111/22222222-2222-4222-8222-222222222222.mp4' }
    for (const h of [handler, createVideoFinalizeHandler(undefined, { isolatedLocalOnly: true })]) {
      const res = response()
      await h(request({ body }), res)
      assert.equal(res.statusCode, 503)
      assert.deepEqual(res.body, { error: 'video_reservation_not_enabled' })
    }
  } finally {
    for (const name of names) {
      if (previous[name] === undefined) delete process.env[name]
      else process.env[name] = previous[name]
    }
  }
})

// Exercise the real TypeScript API entrypoint, not just its source text.
// An incomplete cloud-test opt-in must fail before any network or adapter I/O.
test('real finalize entrypoint rejects incomplete cloud-test opt-in before I/O', async () => {
  const names = ['VIDEO_CLOUD_TEST_ENABLED','VIDEO_CLOUD_TEST_PROJECT_REF','VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID','VERCEL_ENV']
  const previous = Object.fromEntries(names.map(name => [name, process.env[name]]))
  try {
    process.env.VIDEO_CLOUD_TEST_ENABLED = 'true'
    delete process.env.VIDEO_CLOUD_TEST_PROJECT_REF
    delete process.env.VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID
    process.env.VERCEL_ENV = 'preview'
    const res = response()
    await createVideoFinalizeHandler(undefined, { isolatedLocalOnly: true })(request({ headers: { authorization: '' } }), res)
    assert.equal(res.statusCode, 503)
    assert.equal(res.headers['Cache-Control'], 'no-store, private')
    assert.equal(res.headers['Vary'], 'Authorization')
  } finally {
    for (const name of names) {
      if (previous[name] === undefined) delete process.env[name]
      else process.env[name] = previous[name]
    }
  }
})

// A complete, dedicated preview test configuration must reach the real cloud
// dispatcher. Missing bearer is rejected inside the cloud handler before I/O.
// No local-only bypass, external request, DB mutation, or production flag is used.
test('real finalize entrypoint dispatches valid isolated cloud config and denies anonymous before I/O', async () => {
  const names = ['VIDEO_CLOUD_TEST_ENABLED','VIDEO_CLOUD_TEST_PROJECT_REF','VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID','VERCEL_ENV','VERCEL_PROJECT_ID','VITE_SUPABASE_URL','SUPABASE_URL','VIDEO_PRODUCTION_FENCED_READY','VIDEO_ATTESTED_RPC_RELEASE_APPROVED','SUPABASE_SERVICE_ROLE_KEY','SUPABASE_SECRET_KEY','SUPABASE_DB_URL','DATABASE_URL','VIDEO_QA_ENV']
  const previous = Object.fromEntries(names.map(name => [name, process.env[name]]))
  try {
    process.env.VIDEO_CLOUD_TEST_ENABLED = 'true'
    process.env.VIDEO_CLOUD_TEST_PROJECT_REF = 'hbhyuotzginwysrineyo'
    process.env.VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID = 'prj_isolated_fixture_only'
    process.env.VERCEL_PROJECT_ID = 'prj_isolated_fixture_only'
    process.env.VERCEL_ENV = 'preview'
    process.env.VITE_SUPABASE_URL = 'https://hbhyuotzginwysrineyo.supabase.co'
    process.env.SUPABASE_URL = process.env.VITE_SUPABASE_URL
    for (const name of ['VIDEO_PRODUCTION_FENCED_READY','VIDEO_ATTESTED_RPC_RELEASE_APPROVED','SUPABASE_SERVICE_ROLE_KEY','SUPABASE_SECRET_KEY','SUPABASE_DB_URL','DATABASE_URL','VIDEO_QA_ENV']) delete process.env[name]
    const res = response()
    await createVideoFinalizeHandler()(request({ headers: { authorization: '' } }), res)
    assert.equal(res.statusCode, 401)
    assert.equal(res.headers['Cache-Control'], 'no-store, private')
    assert.equal(res.headers['Vary'], 'Authorization')
    assert.equal(res.headers['X-Content-Type-Options'], 'nosniff')
  } finally {
    for (const name of names) {
      if (previous[name] === undefined) delete process.env[name]
      else process.env[name] = previous[name]
    }
  }
})

// The real API entrypoint and Supabase client are exercised with a strict
// in-process transport fixture. No network request can escape this test.
test('real finalize entrypoint reads owner recovery proof through isolated mocked HTTP', async () => {
  const names = ['VIDEO_CLOUD_TEST_ENABLED','VIDEO_CLOUD_TEST_PROJECT_REF','VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID','VERCEL_ENV','VERCEL_PROJECT_ID','VITE_SUPABASE_URL','SUPABASE_URL','VITE_SUPABASE_ANON_KEY','VIDEO_PRODUCTION_FENCED_READY','VIDEO_ATTESTED_RPC_RELEASE_APPROVED','SUPABASE_SERVICE_ROLE_KEY','SUPABASE_SECRET_KEY','SUPABASE_DB_URL','DATABASE_URL','VIDEO_QA_ENV']
  const previous = Object.fromEntries(names.map(name => [name, process.env[name]]))
  const originalFetch = globalThis.fetch
  const uid = '11111111-1111-4111-8111-111111111111'
  const path = uid + '/22222222-2222-4222-8222-222222222222.mp4'
  const calls = []
  try {
    Object.assign(process.env, {VIDEO_CLOUD_TEST_ENABLED:'true',VIDEO_CLOUD_TEST_PROJECT_REF:'hbhyuotzginwysrineyo',VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID:'prj_isolated_fixture_only',VERCEL_PROJECT_ID:'prj_isolated_fixture_only',VERCEL_ENV:'preview',VITE_SUPABASE_URL:'https://hbhyuotzginwysrineyo.supabase.co',SUPABASE_URL:'https://hbhyuotzginwysrineyo.supabase.co',VITE_SUPABASE_ANON_KEY:'fixture-anon'})
    for (const name of ['VIDEO_PRODUCTION_FENCED_READY','VIDEO_ATTESTED_RPC_RELEASE_APPROVED','SUPABASE_SERVICE_ROLE_KEY','SUPABASE_SECRET_KEY','SUPABASE_DB_URL','DATABASE_URL','VIDEO_QA_ENV']) delete process.env[name]
    globalThis.fetch = async (input, init = {}) => {
      const url = String(input instanceof Request ? input.url : input)
      const base = 'https://hbhyuotzginwysrineyo.supabase.co'
      assert.ok(url.startsWith(base + '/'), 'unexpected network origin')
      const endpoint = url.slice(base.length).split('?')[0]
      calls.push(endpoint)
      const data = endpoint === '/auth/v1/user' ? {id:uid,aud:'authenticated',app_metadata:{provider:'email',providers:['email']},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}
        : endpoint === '/rest/v1/rpc/video_cloud_allowed' ? true
        : endpoint === '/rest/v1/rpc/video_cloud_recovery_inspect_v1' ? {path,state:'published',allow_resume:false,expired:false,storage_present:true,post_id:'33333333-3333-4333-8333-333333333333',sha256:'a'.repeat(64),size:1024}
        : null
      assert.notEqual(data,null,'unexpected endpoint: '+endpoint)
      return new Response(JSON.stringify(data),{status:200,headers:{'content-type':'application/json'}})
    }
    const res = response()
    await createVideoFinalizeHandler()(request({headers:{authorization:'Bearer fixture.token'},body:{action:'recovery_inspect',object_path:path}}),res)
    assert.equal(res.statusCode,200)
    assert.equal(res.body.state,'published')
    assert.equal(res.body.allow_resume,false)
    assert.equal(res.body.storage_present,true)
    assert.equal(res.body.size,1024)
    assert.equal(calls.filter(x=>x==='/auth/v1/user').length,2)
    assert.equal(calls.filter(x=>x==='/rest/v1/rpc/video_cloud_allowed').length,2)
    assert.equal(calls.filter(x=>x==='/rest/v1/rpc/video_cloud_recovery_inspect_v1').length,1)
  } finally {
    globalThis.fetch = originalFetch
    for (const name of names) {
      if (previous[name] === undefined) delete process.env[name]
      else process.env[name] = previous[name]
    }
  }
})

// All denial cases exercise the actual finalize entrypoint with an in-process
// fetch fixture; no external HTTP, Storage or database access is possible.
test('real finalize recovery denies foreign identity, auth failure, malformed RPC and identity switch', async () => {
  const names = ['VIDEO_CLOUD_TEST_ENABLED','VIDEO_CLOUD_TEST_PROJECT_REF','VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID','VERCEL_ENV','VERCEL_PROJECT_ID','VITE_SUPABASE_URL','SUPABASE_URL','VITE_SUPABASE_ANON_KEY','VIDEO_PRODUCTION_FENCED_READY','VIDEO_ATTESTED_RPC_RELEASE_APPROVED','SUPABASE_SERVICE_ROLE_KEY','SUPABASE_SECRET_KEY','SUPABASE_DB_URL','DATABASE_URL','VIDEO_QA_ENV']
  const previous = Object.fromEntries(names.map(name => [name, process.env[name]]))
  const originalFetch = globalThis.fetch
  const owner = '11111111-1111-4111-8111-111111111111'
  const foreign = '44444444-4444-4444-8444-444444444444'
  const path = owner + '/22222222-2222-4222-8222-222222222222.mp4'
  try {
    Object.assign(process.env, {VIDEO_CLOUD_TEST_ENABLED:'true',VIDEO_CLOUD_TEST_PROJECT_REF:'hbhyuotzginwysrineyo',VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID:'prj_isolated_fixture_only',VERCEL_PROJECT_ID:'prj_isolated_fixture_only',VERCEL_ENV:'preview',VITE_SUPABASE_URL:'https://hbhyuotzginwysrineyo.supabase.co',SUPABASE_URL:'https://hbhyuotzginwysrineyo.supabase.co',VITE_SUPABASE_ANON_KEY:'fixture-anon'})
    for (const name of ['VIDEO_PRODUCTION_FENCED_READY','VIDEO_ATTESTED_RPC_RELEASE_APPROVED','SUPABASE_SERVICE_ROLE_KEY','SUPABASE_SECRET_KEY','SUPABASE_DB_URL','DATABASE_URL','VIDEO_QA_ENV']) delete process.env[name]
    const cases = [
      {name:'foreign JWT',mode:'foreign',status:403,rpc:0},
      {name:'failed authentication',mode:'auth_error',status:503,rpc:0},
      {name:'inconsistent RPC proof',mode:'rpc_mismatch',status:409,rpc:1},
      {name:'identity changes after inspection',mode:'identity_switch',status:401,rpc:1},
    ]
    for (const scenario of cases) {
      let authCalls = 0, rpcCalls = 0
      globalThis.fetch = async input => {
        const url = String(input instanceof Request ? input.url : input)
        const base = 'https://hbhyuotzginwysrineyo.supabase.co'
        assert.ok(url.startsWith(base + '/'), 'unexpected outbound HTTP origin')
        const endpoint = url.slice(base.length).split('?')[0]
        let value
        if (endpoint === '/auth/v1/user') {
          authCalls++
          if (scenario.mode === 'auth_error') return new Response(JSON.stringify({message:'invalid JWT'}),{status:401,headers:{'content-type':'application/json'}})
          const id = scenario.mode === 'foreign' || (scenario.mode === 'identity_switch' && authCalls > 1) ? foreign : owner
          value = {id,aud:'authenticated',app_metadata:{provider:'email',providers:['email']},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}
        } else if (endpoint === '/rest/v1/rpc/video_cloud_allowed') value = true
        else if (endpoint === '/rest/v1/rpc/video_cloud_recovery_inspect_v1') {
          rpcCalls++
          value = {path:scenario.mode === 'rpc_mismatch' ? foreign+'/22222222-2222-4222-8222-222222222222.mp4' : path,state:'published',allow_resume:false,expired:false,storage_present:true,post_id:'33333333-3333-4333-8333-333333333333',sha256:'a'.repeat(64),size:1024}
        } else assert.fail('unexpected HTTP endpoint: '+endpoint)
        return new Response(JSON.stringify(value),{status:200,headers:{'content-type':'application/json'}})
      }
      const res = response()
      await createVideoFinalizeHandler()(request({headers:{authorization:'Bearer fixture.token'},body:{action:'recovery_inspect',object_path:path}}),res)
      assert.equal(res.statusCode,scenario.status,scenario.name)
      assert.equal(rpcCalls,scenario.rpc,scenario.name+': recovery RPC calls')
      assert.notEqual(res.body?.state,'published',scenario.name+': no published proof leaked')
    }
  } finally {
    globalThis.fetch = originalFetch
    for (const name of names) {
      if (previous[name] === undefined) delete process.env[name]
      else process.env[name] = previous[name]
    }
  }
})
