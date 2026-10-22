import test from 'node:test'
import assert from 'node:assert/strict'
import {topPersonalTraits,relativePositiveScore} from '../src/playerTypePresentation.ts'
import './player-type.test.mjs'
for(const key of ['constructor','toString','__proto__','hasOwnProperty','valueOf']){
 test(`prototype key ${key} is not a known trait`,()=>{
  const scores=JSON.parse(`{"${key}":1}`)
  assert.deepEqual(topPersonalTraits({trait_scores:scores,discriminator_scores:{}}),[])
  assert.equal(relativePositiveScore(key,1),0)
 })
}
test('known trait remains finite and wins over inherited key',()=>{
 const r=topPersonalTraits({trait_scores:JSON.parse('{"constructor":999,"initiative":1}'),discriminator_scores:{}})
 assert.deepEqual(r.map(x=>x.key),['initiative'])
 assert.ok(Number.isFinite(relativePositiveScore('initiative',1)))
})
