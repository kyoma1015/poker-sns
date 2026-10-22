import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// The preflight is intentionally safe for manually approved live read-only SQL
// audits. Never let DDL, DML, executing functions or user rows enter this file.
const body = readFileSync('sql/poll_only/preflight_readonly.sql', 'utf8')
 .replace(/--[^\n]*/g, '')
 .trim();
const statements = body.split(';').map(x=>x.trim()).filter(Boolean);
assert.ok(statements.length >= 10, 'All release gates must remain populated');
for (const sql of statements) {
  assert.match(sql, /^select\b/i);
  assert.doesNotMatch(sql, /\b(insert|update|delete|alter|create|drop|truncate|grant|revoke|do|call|copy|execute|refresh|vacuum)\b/i);
  assert.doesNotMatch(sql, /\b(select\s+\*|password|encrypted_password|email|phone|raw_user_meta_data|access_token|refresh_token)\b/i);
}
console.log('PASS release preflight is SELECT-only, aggregates/catalog only, no credentials or PII columns');
