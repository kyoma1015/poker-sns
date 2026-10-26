import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { auditPlayerType } from '../scripts/audit-player-type.mjs'
import { parseQuestions } from '../src/playerTypeQuestions.ts'
import { traitPositiveMax } from '../src/playerTypePresentation.ts'
const fixture=JSON.parse(readFileSync(new URL('./fixtures/player-type-v2.json',import.meta.url)))
const assets=readdirSync(new URL('../public/animals/',import.meta.url)).filter(x=>x.endsWith('.png')).map(x=>x.slice(0,-4))
const audit=f=>auditPlayerType(f,assets)
const terms=['ブラフ','ポラライズ','レンジ','ハンド','強い相手','弱い相手','バランス','エクスプロイト']

test('strategy review pack exposes literal evidence and retains semantic BLOCKED',()=>{
 const pack=audit(fixture).strategyReviewEvidence; assert.ok(pack)
 assert.equal(pack.questions.length,50);assert.equal(pack.optionCount,222)
 assert.equal(pack.classifier,'NOT EXECUTED');assert.match(pack.semanticValidity,/^BLOCKED:/)
 assert.deepEqual(pack.queries.map(q=>q.term),terms)
})
test('all strategy term matches are traceable to exact question and option text',()=>{
 const pack=audit(fixture).strategyReviewEvidence;assert.ok(pack)
 const questions=parseQuestions(fixture.rows)
 for(const query of pack.queries){
  const expected=questions.flatMap(q=>{
   const questionMatch=q.text.includes(query.term),optionOrders=q.options.filter(o=>o.text.includes(query.term)).map(o=>o.order)
   return questionMatch||optionOrders.length?[{questionOrder:q.order,questionMatch,optionOrders}]:[]
  })
  assert.deepEqual(query.matches,expected)
 }
})
test('every contrast reconstructs original option weights without changing axes or their meaning',()=>{
 const pack=audit(fixture).strategyReviewEvidence;assert.ok(pack)
 const questions=parseQuestions(fixture.rows),scores=new Map(fixture.scores.map(s=>[s.option_id,s]))
 for(const q of questions){
  const measured=pack.questions.find(x=>x.order===q.order)
  assert.deepEqual(measured.optionIds,q.options.map(o=>o.id))
  assert.equal(measured.text,q.text)
  for(const key of Object.keys(traitPositiveMax)){
   const values=q.options.map(o=>scores.get(o.id)[key]),contrast=measured.contrasts.find(x=>x.key===key)
   if(new Set(values).size===1)assert.equal(contrast,undefined)
   else {assert.ok(contrast);assert.equal(contrast.baseline,values[0]);assert.deepEqual(contrast.differences,values.map(x=>x-values[0]))}
  }
 }
})
test('added literal terms never upgrade semantic validity or execute a classifier',()=>{
 const f=structuredClone(fixture);for(const row of f.rows)if(row.question_order===50){row.question_text+=' ポラライズ';if(row.option_order===1)row.option_text+=' レンジ'}
 const pack=audit(f).strategyReviewEvidence;assert.ok(pack)
 assert.ok(pack.queries.find(q=>q.term==='ポラライズ').matches.some(m=>m.questionOrder===50&&m.questionMatch))
 assert.ok(pack.queries.find(q=>q.term==='レンジ').matches.some(m=>m.questionOrder===50&&m.optionOrders.includes(1)))
 assert.match(pack.semanticValidity,/^BLOCKED:/);assert.equal(pack.classifier,'NOT EXECUTED')
})
test('invalid score/reference evidence suppresses strategy pack',()=>{
 const f=structuredClone(fixture);f.personas[0].raw.initiative++
 const r=audit(f);assert.equal(r.status,'FAIL');assert.equal(r.strategyReviewEvidence,null)
})
test('evidence generation preserves source fixture and all 960 historical reference values',()=>{
 const before=JSON.stringify(fixture),r=audit(fixture)
 assert.ok(r.strategyReviewEvidence);assert.equal(r.personaReferenceComparison.comparedValues,960)
 assert.equal(JSON.stringify(fixture),before)
})
