import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createPollRequest, pollVoteRequest, pollDisplayResult } from '../src/interactiveRequests.ts'

for (const mode of ['question', 'normal', '', 'QUESTION']) {
  test(`stale or forged ${mode} mode is rejected before RPC`, () => {
    assert.throws(() => createPollRequest(mode, 'content', ['A', 'B'], 24, false))
  })
}
for (const count of [2, 3, 4]) {
  test(`${count} poll choices and privacy mode produce poll-only contract`, () => {
    const options = Array.from({ length: count }, (_, i) => ` ${i} `)
    const result = createPollRequest('poll', ' content ', options, 24, true)
    assert.deepEqual(result, { p_content: 'content', p_kind: 'poll', p_options: options.map(s => s.trim()), p_hours: 24, p_is_anonymous: true, p_question_policy: null })
  })
}
for (const [options, hours] of [[['A'], 24], [['A','B','C','D','E'], 24], [['A',' a '], 24], [['','B'], 24], [['x'.repeat(81),'B'], 24], [['A','B'], 0], [['A','B'], NaN]]) {
  test(`invalid poll parameters ${JSON.stringify([options,hours])} fail closed`, () => {
    assert.throws(() => createPollRequest('poll', 'content', options, hours, false))
  })
}
test('empty and overlong content fail closed', () => {
  for (const content of [' ', 'x'.repeat(501)]) assert.throws(() => createPollRequest('poll', content, ['A','B'], 24, false))
})
test('anonymous presentation drops identities even in unexpected server payload without mutating it', () => {
  const payload = { voters: [{ poker_id: 'private', option_index: 0 }], answers: [{ poker_id: 'private' }], total_votes: 1, vote_counts: { 0: 1 } }
  const result = pollDisplayResult(true, payload)
  assert.deepEqual(result.voters, [])
  assert.deepEqual(result.answers, [])
  assert.equal(result.total_votes, 1)
  assert.equal(payload.voters.length, 1)
  assert.equal(pollDisplayResult(false, payload), payload)
})
test('both composers use guarded creation; public card cannot mount historical question thread', () => {
  const timeline = readFileSync(new URL('../src/Timeline.tsx', import.meta.url), 'utf8')
  const card = readFileSync(new URL('../src/TimelineInteractive.tsx', import.meta.url), 'utf8')
  const detail = readFileSync(new URL('../src/PostDetail.tsx', import.meta.url), 'utf8')
  assert.match(timeline, /useState<'normal'\|'poll'>/)
  assert.doesNotMatch(timeline, /questionPolicy|choosePostMode\('question'\)|質問箱/)
  for (const source of [timeline, card]) {
    assert.match(source, /createPollRequest\(/)
    assert.match(source, /rpc\('create_interactive_post_v4', request\)/)
  }
  assert.match(card, /if \(item.kind !== 'poll'\) return null/)
  assert.doesNotMatch(card, /<QuestionThread/)
  assert.match(card, /export function QuestionThread/)
  assert.match(timeline, /visibleInteractiveIds.includes\(row.id\)/)
  assert.match(detail, /interactiveRow\?\.kind === 'question'/)
  for (const source of [timeline, detail, card]) assert.match(source, /pollDisplayResult\(/)
})

for (const malformed of [null, {}, { kind: 'poll', options: null },
  { kind: 'poll', options: ['A', 'B'], closes_at: '2099-01-01T00:00:00Z', is_anonymous: 'false' }]) {
  test('malformed legacy vote payload fails closed before RPC', () => {
    assert.throws(() => pollVoteRequest(malformed, 0))
  })
}
for (const malformed of [null, {}, [null, 'B'], [42, 'B']]) {
  test('malformed poll creation options fail closed before RPC', () => {
    assert.throws(() => createPollRequest('poll', 'content', malformed, 24, false))
  })
}

for (const overrides of [
  { post_id: '' }, { post_id: null }, { closes_at: null },
  { closes_at: '' }, { closes_at: 'not-a-date' },
  { options: ['A'] }, { options: ['A','B','C','D','E'] },
]) {
  test('vote refuses incomplete or invalid stored poll metadata', () => {
    const poll = { post_id: 'poll-1', kind: 'poll', options: ['A', 'B'],
      closes_at: '2099-01-01T00:00:00Z', is_anonymous: false, ...overrides }
    assert.throws(() => pollVoteRequest(poll, 0))
  })
}
test('valid vote retains anonymous flag and poll-only RPC arguments', () => {
  const poll = { post_id: 'poll-1', kind: 'poll', options: ['A', 'B'],
    closes_at: '2099-01-01T00:00:00Z', is_anonymous: true }
  assert.deepEqual(pollVoteRequest(poll, 1, Date.parse('2026-10-24T00:00:00Z')),
    { p_post_id: 'poll-1', p_option_index: 1, p_answer: null, p_is_anonymous: true })
})

test('poll card fails closed when deadline is missing or invalid', () => {
  const card = readFileSync(new URL('../src/TimelineInteractive.tsx', import.meta.url), 'utf8')
  assert.match(card, /!Number\.isFinite\(deadline\) \|\| deadline <= Date\.now\(\)/)
  assert.match(card, /終了または期限を確認できません/)
  assert.doesNotMatch(card, /new Date\(item\.closes_at!\)/)
})

test('poll composer and vote card lock synchronously against duplicate submissions', () => {
  const card = readFileSync(new URL('../src/TimelineInteractive.tsx', import.meta.url), 'utf8')
  assert.match(card, /import \{ useEffect, useRef, useState \} from 'react'/)
  assert.match(card, /if \(submitting\.current\) return/)
  assert.match(card, /if\(submitting\.current\|\|voteAccepted\.current\|\|mine\|\|closed\|\|choice===null\) return/)
  assert.match(card, /finally \{ submitting\.current = false; setBusy\(false\) \}/)
  assert.match(card, /finally\{submitting\.current=false;setBusy\(false\)\}/)
})

test('accepted vote cannot be resubmitted when refresh fails', () => {
  const card = readFileSync(new URL('../src/TimelineInteractive.tsx', import.meta.url), 'utf8')
  assert.match(card, /const voteAccepted = useRef\(false\)/)
  assert.match(card, /if\(submitting\.current\|\|voteAccepted\.current\|\|mine\|\|closed\|\|choice===null\) return/)
  assert.match(card, /if\(failure\) throw failure\s+voteAccepted\.current=true\s+try \{\s+await onUpdated\(\)/)
  assert.match(card, /投票は受け付けられましたが、結果を更新できませんでした/ )
  assert.match(card, /disabled=\{choice===null\|\|busy\|\|voteAccepted\.current\}/)
})
