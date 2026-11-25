import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {fileURLToPath} from 'node:url'
import {dirname,resolve} from 'node:path'
const sql=readFileSync(resolve(dirname(fileURLToPath(import.meta.url)),'candidate_live_reservation_quota.sql'),'utf8')
assert.match(sql,/CREATE OR REPLACE FUNCTION public\.video_cloud_reserve\(/i)
assert.match(sql,/where owner_id=auth\.uid\(\) and expires_at>clock_timestamp\(\)\)\s*>=10/i)
assert.match(sql,/if r\.owner_id<>auth\.uid\(\) or r\.sha256 is distinct from p_sha256/i)
assert.match(sql,/if r\.expires_at<=clock_timestamp\(\)|r\.expires_at<=clock_timestamp\(\)/i)
assert.doesNotMatch(sql,/\b(?:delete|truncate|drop|alter)\s+(?:from\s+)?(?:video_cloud\.reservations|storage\.objects|public\.posts)\b/i)
console.log('candidate live-reservation quota: static safety checks PASS')
