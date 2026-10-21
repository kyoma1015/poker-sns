import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const core = readFileSync(new URL('../sql/poll_only/core_without_notifications_candidate.sql', import.meta.url), 'utf8')
const runner = readFileSync(new URL('./polls/run_isolated.sh', import.meta.url), 'utf8')

test('core rollout retains create, vote and result RPCs', () => {
  for (const rpc of ['create_interactive_post_v4', 'submit_interactive_response_v2', 'get_interactive_results_v4']) {
    assert.match(core, new RegExp('create or replace function public\\.' + rpc + '\\('))
  }
  assert.match(core, /notify pgrst, 'reload schema'/)
  assert.match(core, /commit;\\s*$/)
})

test('core rollout cannot install or alter close notification execution', () => {
  assert.doesNotMatch(core, /create or replace function poll_private\\.close_due_polls\\(/i)
  assert.doesNotMatch(core, /create or replace function poll_private\\.guard_closed_notification\\(/i)
  assert.doesNotMatch(core, /create trigger poll_closed_guard_v1/i)
  assert.doesNotMatch(core, /cron\\.(schedule|unschedule)/i)
  assert.doesNotMatch(core, /drop trigger/i)
})

test('isolated QA applies core twice and verifies notification isolation', () => {
  assert.match(runner, /for core_pass in 1 2/)
  assert.match(runner, /core_without_notifications_candidate\\.sql/)
  assert.match(runner, /Core unexpectedly installed notification worker/)
  assert.match(runner, /Core unexpectedly installed notification cron/)
})
