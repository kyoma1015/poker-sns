import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { auditPlayerType } from '../scripts/audit-player-type.mjs'
const fixture=JSON.parse(readFileSync(new URL('./fixtures/player-type-v2.json',import.meta.url)))
const assets=readdirSync(new URL('../public/animals/',import.meta.url)).filter(x=>x.endsWith('.png')).map(x=>x.slice(0,-4))
const report=f=>auditPlayerType(f,assets)

test('all historical persona score references are explicitly verified without classifying animals',()=>{
 const r=report(fixture)
 assert.deepEqual(r.personaReferenceComparison,{status:'PASS',personas:30,dimensions:32,comparedValues:960,sourceCommit:fixture.source_commit,classification:'NOT VERIFIED'})
})
test('one altered reference score is rejected instead of silently passing the audit',()=>{
 const f=structuredClone(fixture); f.personas[0].raw.initiative++
 const r=report(f); assert.equal(r.status,'FAIL'); assert.equal(r.scoreDistribution,null)
 assert.ok(r.errors.some(e=>e.code==='PERSONA_REFERENCE_MISMATCH' && e.persona===0 && e.key==='initiative'))
})
for(const [name,value] of [['missing',undefined],['null',null],['array',[]],['string','bad']])test(`malformed ${name} reference blocks evidence`,()=>{
 const f=structuredClone(fixture); f.personas[0].raw=value
 const r=report(f); assert.equal(r.status,'FAIL'); assert.equal(r.scoreDistribution,null)
 assert.ok(r.errors.some(e=>e.code==='INVALID_PERSONA_REFERENCE' && e.persona===0))
})
for(const [name,change] of [['missing dimension',raw=>delete raw.initiative],['extra dimension',raw=>raw.invented_trait=0],['nonfinite',raw=>raw.initiative=Infinity],['numeric string',raw=>raw.initiative='1'],['boolean',raw=>raw.initiative=true]])test(`invalid ${name} cannot masquerade as reference verification`,()=>{
 const f=structuredClone(fixture); change(f.personas[0].raw)
 const r=report(f); assert.equal(r.status,'FAIL'); assert.equal(r.scoreDistribution,null)
 assert.ok(r.errors.some(e=>e.code==='INVALID_PERSONA_REFERENCE' && e.persona===0))
})
test('inherited score value cannot replace an own reference dimension',()=>{
 const f=structuredClone(fixture); const value=f.personas[0].raw.initiative;delete f.personas[0].raw.initiative;Object.setPrototypeOf(f.personas[0].raw,{initiative:value})
 const r=report(f);assert.equal(r.status,'FAIL'); assert.ok(r.errors.some(e=>e.code==='INVALID_PERSONA_REFERENCE'))
})
test('valid reference audit does not mutate fixture answers or scores',()=>{
 const before=JSON.stringify(fixture);assert.equal(report(fixture).status,'CONDITIONAL PASS');assert.equal(JSON.stringify(fixture),before)
})
