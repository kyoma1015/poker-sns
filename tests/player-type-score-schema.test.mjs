import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { auditPlayerType } from '../scripts/audit-player-type.mjs'
const fixture=JSON.parse(readFileSync(new URL('./fixtures/player-type-v2.json',import.meta.url)))
const assets=readdirSync(new URL('../public/animals/',import.meta.url)).filter(x=>x.endsWith('.png')).map(x=>x.slice(0,-4))
const audit=f=>auditPlayerType(f,assets)
const reject=f=>{
 const result=audit(f)
 assert.equal(result.status,'FAIL')
 assert.ok(result.errors.some(error=>error.code==='INVALID_SCORE_ROW_SCHEMA'))
 assert.equal(result.scoreDistribution,null)
 assert.equal(result.strategyReviewEvidence,null)
}
test('historical score schema remains valid and all960 references remain unchanged',()=>{
 const before=JSON.stringify(fixture),r=audit(fixture)
 assert.equal(r.status,'CONDITIONAL PASS');assert.equal(r.personaReferenceComparison.comparedValues,960)
 assert.equal(JSON.stringify(fixture),before)
})
test('inherited score dimension cannot masquerade as an own exported value',()=>{
 const f=structuredClone(fixture),row=f.scores[0],value=row.initiative
 delete row.initiative;Object.setPrototypeOf(row,{initiative:value});reject(f)
})
test('inherited option identifier cannot supply a score-row join key',()=>{
 const f=structuredClone(fixture),row=f.scores[0],id=row.option_id
 delete row.option_id;Object.setPrototypeOf(row,{option_id:id});reject(f)
})
test('unknown extra score dimension cannot be silently ignored',()=>{
 const f=structuredClone(fixture);f.scores[0].unreviewed_axis=123;reject(f)
})
test('array decorated as a complete score object is rejected',()=>{
 const f=structuredClone(fixture);f.scores[0]=Object.assign([],f.scores[0]);reject(f)
})
test('null score row produces auditFAIL rather than crashing',()=>{
 const f=structuredClone(fixture);f.scores[0]=null;reject(f)
})
test('non-number score payload remains invalid without emitting evidence',()=>{
 const f=structuredClone(fixture);f.scores[0].initiative='1';reject(f)
})
