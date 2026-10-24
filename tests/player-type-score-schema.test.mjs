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
for (const [name, value] of [['null',null],['object',{}],['string','scores'],['number',222],['boolean',true]]) {
 test(`invalid ${name} score container fails closed without throwing`,()=>{
  const f=structuredClone(fixture);f.scores=value;reject(f)
 })
}
test('sparse score array fails closed without emitting evidence',()=>{
 const f=structuredClone(fixture);delete f.scores[0];reject(f)
})
test('inherited array entry cannot supply an exported score row',()=>{
 const f=structuredClone(fixture),row=f.scores[0],proto=Object.create(Array.prototype)
 proto[0]=row;delete f.scores[0];Object.setPrototypeOf(f.scores,proto);reject(f)
})
test('polluted score-row prototype cannot hide unreviewed metadata',()=>{
 const f=structuredClone(fixture);Object.setPrototypeOf(f.scores[0],{unreviewed_axis:123});reject(f)
})
test('JSON own __proto__ payload is rejected without global prototype mutation',()=>{
 const f=structuredClone(fixture),before=Object.getPrototypeOf({})
 Object.defineProperty(f.scores[0],'__proto__',{value:{polluted:true},enumerable:true})
 reject(f);assert.equal(Object.getPrototypeOf({}),before);assert.equal({}.polluted,undefined)
})
test('hidden and symbol score fields cannot escape exact schema validation',()=>{
 for (const key of ['hidden',Symbol('hidden')]) {
  const f=structuredClone(fixture);Object.defineProperty(f.scores[0],key,{value:1});reject(f)
 }
})
test('score accessor is rejected without executing user code',()=>{
 const f=structuredClone(fixture);let calls=0
 Object.defineProperty(f.scores[0],'initiative',{get(){calls++;throw new Error('must not execute')},enumerable:true})
 reject(f);assert.equal(calls,0)
})
