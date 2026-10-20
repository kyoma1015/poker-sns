import assert from 'node:assert/strict'
import { readFileSync,readdirSync } from 'node:fs'
import { auditPlayerType } from '../scripts/audit-player-type.mjs'
const fixture=JSON.parse(readFileSync(new URL('./fixtures/player-type-v2.json',import.meta.url)))
const assets=readdirSync(new URL('../public/animals/',import.meta.url)).filter(x=>x.endsWith('.png')).map(x=>x.slice(0,-4))
const before=JSON.stringify(fixture)
assert.equal(auditPlayerType(fixture,assets).status,'CONDITIONAL PASS')
for(const answers of [[],fixture.personas[0].answers.slice(0,49),[...fixture.personas[0].answers,'A'],fixture.personas[0].answers.map((x,i)=>i===0?'Z':x)]) {
 const broken=structuredClone(fixture);broken.personas[0].answers=answers
 assert.equal(auditPlayerType(broken,assets).status,'FAIL','invalid persona answer count/letter must fail')
}
assert.equal(JSON.stringify(fixture),before,'audit must not mutate source')
console.log('PASS D immutable persona integrity acceptance')
