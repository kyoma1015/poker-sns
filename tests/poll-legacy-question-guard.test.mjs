import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const sql = readFileSync(new URL('../sql/poll_only/block_legacy_question_inserts_candidate.sql', import.meta.url), 'utf8')
test('legacy question guard is non-destructive and applies to all RPC insert paths', () => {
 assert.match(sql, /before insert or update of kind on public\.post_interactive/i)
 assert.match(sql, /new\.kind is distinct from 'poll'/i)
 assert.match(sql, /raise exception 'Only polls are supported'/i)
 assert.doesNotMatch(sql, /\b(delete from|truncate|drop table|update public\.post_interactive set)\b/i)
 assert.match(sql, /commit;\s*$/)
})
