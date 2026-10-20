import test from 'node:test'
import assert from 'node:assert/strict'
import { Headers, MockAgent, fetch, request } from 'undici'
import OpenAI from 'openai'

test('patched HTTP transport supports Vercel Headers and request with no external network', async () => {
  const agent = new MockAgent()
  agent.disableNetConnect()
  agent.get('https://transport.invalid').intercept({ path: '/ping', method: 'GET' }).reply(200, 'ok')
  try {
    const headers = new Headers({ 'x-qa': 'value' })
    assert.equal(headers.get('x-qa'), 'value')
    const response = await request('https://transport.invalid/ping', { dispatcher: agent, headers })
    assert.equal(response.statusCode, 200)
    assert.equal(await response.body.text(), 'ok')
    agent.assertNoPendingInterceptors()
  } finally { await agent.close() }
})
test('patched fetch decodes JSON under the locked API', async () => {
  const agent = new MockAgent()
  agent.disableNetConnect()
  agent.get('https://transport.invalid').intercept({ path: '/json', method: 'GET' }).reply(200, { ok: true }, { headers: { 'content-type': 'application/json' } })
  try {
    assert.deepEqual(await (await fetch('https://transport.invalid/json', { dispatcher: agent })).json(), { ok: true })
    agent.assertNoPendingInterceptors()
  } finally { await agent.close() }
})
test('OpenAI SDK response API still consumes a supplied mocked fetch without paid calls', async () => {
  let captured
  const client = new OpenAI({ apiKey: 'test-only-not-a-real-key', fetch: async (url, init) => {
    captured = { url: String(url), method: init.method, body: JSON.parse(init.body) }
    return new Response(JSON.stringify({ id: 'qa-response', object: 'response', output: [] }), { headers: { 'content-type': 'application/json' } })
  } })
  const response = await client.responses.create({ model: 'test-model', input: 'fixture' })
  assert.equal(response.id, 'qa-response')
  assert.equal(captured.method, 'POST')
  assert.equal(captured.body.input, 'fixture')
})
