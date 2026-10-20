import test from 'node:test'
import assert from 'node:assert/strict'
import { pollVoteRequest } from '../src/interactiveRequests.ts'

const now = Date.parse('2026-10-20T00:00:00Z')
const poll = { post_id: 'poll-id', kind: 'poll', options: ['A', 'B'], closes_at: '2026-10-20T01:00:00Z', is_anonymous: false }
test('named poll request matches the disclosed named mode', () => {
  assert.deepEqual(pollVoteRequest(poll, 1, now), {
    p_post_id: 'poll-id', p_option_index: 1, p_answer: null, p_is_anonymous: false,
  })
})
test('anonymous poll remains anonymous', () => {
  assert.equal(pollVoteRequest({ ...poll, is_anonymous: true }, 0, now).p_is_anonymous, true)
})
for (const choice of [null, -1, 2, 0.5, NaN]) {
  test(`invalid option ${choice} cannot produce a request`, () => {
    assert.throws(() => pollVoteRequest(poll, choice, now))
  })
}
test('a previously rendered open card cannot vote at or after the deadline', () => {
  const deadline = Date.parse(poll.closes_at)
  assert.equal(pollVoteRequest(poll, 0, deadline - 1).p_option_index, 0)
  assert.throws(() => pollVoteRequest(poll, 0, deadline))
  assert.throws(() => pollVoteRequest(poll, 0, deadline + 1))
})
test('missing or invalid deadline fails closed', () => {
  for (const closes_at of [null, '', 'invalid']) {
    assert.throws(() => pollVoteRequest({ ...poll, closes_at }, 0, now))
  }
})
test('question boxes cannot use the poll write contract', () => {
  assert.throws(() => pollVoteRequest({ ...poll, kind: 'question' }, 0, now))
})
