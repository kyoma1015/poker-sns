import test from 'node:test'
import assert from 'node:assert/strict'
import { topPersonalTraits, personalAdvice } from '../src/playerTypePresentation.ts'
const detail=trait_scores=>({trait_scores,discriminator_scores:{}})
const generic=personalAdvice(detail({}))
for (const [name,value] of [['string','19'],['boolean',true],['array',[19]],['coercible object',{valueOf:()=>19}]]) {
 test(`${name} score cannot produce a top tendency or strategic advice`,()=>{
  assert.deepEqual(topPersonalTraits(detail({initiative:value})),[])
  assert.equal(personalAdvice(detail({initiative:value,confidence:'11',attack_momentum:'15'})),generic)
 })
}
test('throwing numeric coercion is never evaluated',()=>{
 let calls=0;const value={valueOf(){calls++;throw Error('must not evaluate')}}
 assert.deepEqual(topPersonalTraits(detail({initiative:value})),[])
 assert.equal(personalAdvice(detail({initiative:value})),generic);assert.equal(calls,0)
})
test('malformed detail and score records fall back without exceptions',()=>{
 for(const value of [null,undefined,[],false,'scores']) {
  assert.deepEqual(topPersonalTraits(value),[]);assert.equal(personalAdvice(value),generic)
  assert.deepEqual(topPersonalTraits(detail(value)),[]);assert.equal(personalAdvice(detail(value)),generic)
 }
})
test('score accessors are not evaluated during result presentation',()=>{
 let calls=0;const scores={};Object.defineProperty(scores,'initiative',{enumerable:true,get(){calls++;throw Error('no')}})
 assert.deepEqual(topPersonalTraits(detail(scores)),[]);assert.equal(personalAdvice(detail(scores)),generic);assert.equal(calls,0)
})
test('finite negative and positive numeric presentation is preserved',()=>{
 assert.deepEqual(topPersonalTraits(detail({initiative:19,patience:-1})).map(x=>x.key),['initiative'])
 assert.match(personalAdvice(detail({initiative:19,confidence:11,attack_momentum:15})),/自分から動き、攻めを続ける/)
})
