import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const forward = readFileSync(new URL('../sql/poll_only/forward_candidate.sql', import.meta.url), 'utf8')
const schedule = readFileSync(new URL('../sql/poll_only/schedule_candidate.sql', import.meta.url), 'utf8')
const rollback = readFileSync(new URL('../sql/poll_only/disable_candidate.sql', import.meta.url), 'utf8')
const isolatedRunner = readFileSync(new URL('./polls/run_isolated.sh', import.meta.url), 'utf8')
const fixture = readFileSync(new URL('./polls/legacy_schema_fixture.sql', import.meta.url), 'utf8')

test('production five-argument v3 creation RPC is replaced without introducing six-argument overload', () => {
  const declaration = forward.match(/create or replace function public\.create_interactive_post_v3\(([^)]*)\)/i)
  assert.ok(declaration, 'v3 replacement declaration is required')
  assert.equal((declaration[1].match(/\bp_[a-z_]+\s/g) || []).length, 5)
  assert.doesNotMatch(declaration[1], /p_question_policy/)
  assert.match(forward, /create_interactive_post_v3\([\s\S]*?as \$v3_wrapper\$select public\.create_interactive_post_v4\([\s\S]*?\)\$v3_wrapper\$;/i)
  assert.match(forward, /create_interactive_post_v3:text, text, text\[\], integer, boolean/)
})

test('historical result RPC signatures are handled and legacy client permissions stay revoked', () => {
  for (const name of ['get_interactive_results_v2', 'get_interactive_results_v3']) {
    assert.match(forward, new RegExp('create or replace function public\\.' + name + '\\(p_post_ids uuid\\[\\]\\)'))
    assert.match(forward, new RegExp(name + '.*get_interactive_results_v4', 's'))
  }
  assert.match(forward, /revoke all on function public\.get_interactive_results_v2\(uuid\[\]\),public\.get_interactive_results_v3\(uuid\[\]\) from public,anon,authenticated/)
})

test('SQL wrappers contain no invalid bare dollar delimiters', () => {
  assert.doesNotMatch(forward, /as \$(?!\$|[A-Za-z_][A-Za-z0-9_]*\$)/)
  assert.match(forward, /as \$legacy_results\$/)
})

test('new scheduler refuses existing production interactive cron', () => {
  assert.match(schedule, /jobname<>\s*'pokerid-poll-close-v1'/)
  assert.match(schedule, /command ~\* '\(poll\|interactive\)'/)
  assert.match(schedule, /raise exception 'Existing interactive cron requires review/)
})

test('feature-disable rollback revokes every historical results RPC and preserves data', () => {
  for (const name of ['get_interactive_results_v2', 'get_interactive_results_v3', 'get_interactive_results_v4']) {
    assert.ok(rollback.includes("'" + name + "'"), name + ' missing from rollback')
  }
  assert.doesNotMatch(rollback, /drop\s+(?:table|schema)\b/i)
  assert.match(isolatedRunner, /historical question/)
  assert.match(isolatedRunner, /Rollback removed notification guard/)
})

test('isolated runner checks legacy cron collision and preserves both jobs on rejection', () => {
  assert.match(isolatedRunner, /poker_id_poll_closed_notifications/)
  assert.match(isolatedRunner, /cron-collision-guard\.log/)
  assert.match(isolatedRunner, /Scheduler collision guard changed existing jobs/)
})

test('isolated legacy fixture reproduces production v2/v3 RPC shapes', () => {
  assert.match(fixture, /create or replace function public\.create_interactive_post_v3\(p_content text,p_kind text,p_options text\[\] default null,p_hours integer default 24,p_is_anonymous boolean default true\)/)
  assert.match(fixture, /create or replace function public\.get_interactive_results_v2\(p_post_ids uuid\[\]\)/)
  assert.match(fixture, /create or replace function public\.get_interactive_results_v3\(p_post_ids uuid\[\]\)/)
  assert.match(fixture, /has_responded boolean,voters jsonb/)
})
