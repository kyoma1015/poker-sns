import assert from 'node:assert/strict'

const { PREVIEW_URL, PREVIEW_POST_ID, VERCEL_OIDC_TOKEN, TEST_OWNER_JWT, TEST_OTHER_JWT } = process.env
if (![PREVIEW_URL, PREVIEW_POST_ID, VERCEL_OIDC_TOKEN, TEST_OWNER_JWT, TEST_OTHER_JWT].every(Boolean)) {
  console.error('BLOCKED: required Preview URL, post ID, trusted OIDC and two test JWTs are unavailable')
  process.exit(2)
}
const origin = new URL(PREVIEW_URL)
assert.equal(origin.pathname, '/')
assert.equal(origin.search, '')
assert.equal(origin.hash, '')
assert.equal(origin.username, '')
assert.equal(origin.password, '')
assert.equal(origin.protocol, 'https:')
assert.match(origin.hostname, /\.vercel\.app$/)
assert.match(PREVIEW_POST_ID, /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/)
const endpoint = new URL('/internal/video/media/' + PREVIEW_POST_ID, origin)
async function check(label, jwt, expected) {
  const headers = { 'x-vercel-trusted-oidc-idp-token': VERCEL_OIDC_TOKEN }
  if (jwt) headers.Authorization = 'Bearer ' + jwt
  const response = await fetch(endpoint, { method: 'GET', headers, redirect: 'manual', signal: AbortSignal.timeout(30000) })
  const type = response.headers.get('content-type') || ''
  const vercelChallenge = response.headers.has('x-vercel-challenge-token') || response.headers.has('x-vercel-authentication-required')
  if (vercelChallenge || response.status >= 300 && response.status < 400 || type.includes('text/html')) {
    throw new Error(label + ': BLOCKED (deployment redirect or HTML, not app response)')
  }
  if (response.status === 401 && response.headers.get('content-type')?.includes('text/html')) throw new Error(label + ': BLOCKED (Vercel protection)')
  if (!expected.includes(response.status)) throw new Error(label + ': unexpected HTTP ' + response.status)
  if (label === 'owner' && !type.startsWith('video/')) throw new Error('owner: response is not video')
  await response.body?.cancel()
  console.log(label + ': PASS (HTTP ' + response.status + ')')
}
try {
  await check('anonymous', null, [401])
  await check('other-user', TEST_OTHER_JWT, [403, 404])
  await check('owner', TEST_OWNER_JWT, [200])
  console.log('PASS: read-only protected Preview media authorization')
} catch (error) {
  console.error('BLOCKED/FAIL: ' + error.message)
  process.exitCode = 1
}
