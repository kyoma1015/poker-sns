import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const forward = readFileSync(new URL('../sql/poll_only/forward_candidate.sql', import.meta.url), 'utf8')
const schedule = readFileSync(new URL('../sql/poll_only/schedule_candidate.sql', import.meta.url), 'utf8')

test('production five-argument v3 creation RPC is replaced without introducing six-argument overload', () => {
  const declaration = forward.match(/create or replace function public\.create_interactive_post_v3\(([^)]*)\)/i)
  assert.ok(declaration, 'v3 replacement declaration is required')
  assert.equal((declaration[1].match(/\bp_[a-z_]+\s/g) || []).length, 5)
  assert.doesNotMatch(declaration[1], /p_question_policy/)
  assert.match(forward, /create_interactive_post_v3:text, text, text\[\], integer, boolean/)
})

test('historical result RPC signatures are handled and legacy client permissions stay revoked', () => {
  for (const name of ['get_interactive_results_v2', 'get_interactive_results_v3']) {
    assert.match(forward, new RegExp('create or replace function public\\.' + name + '\\(p_post_ids uuid\\[\\]\\)'))
    assert.match(forward, new RegExp(name + '.*get_interactive_results_v4', 's'))
  }
  assert.match(forward, /revoke all on function public\.get_interactive_results_v2\(uuid\[\]\),public\.get_interactive_results_v3\(uuid\[\]\) from public,anon,authenticated/)
})

test('new scheduler refuses existing production interactive cron', () => {
  assert.match(schedule, /jobname<>\s*'pokerid-poll-close-v1'/)
  assert.match(schedule, /command ~\* '\(poll\|interactive\)'/)
  assert.match(schedule, /raise exception 'Existing interactive cron requires review/)
})
