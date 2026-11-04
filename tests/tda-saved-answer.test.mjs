import test from 'node:test'
import assert from 'node:assert/strict'
import * as data from '../src/tdaQuizData.ts'
const question = { question_id:'q1', question_text:'synthetic', difficulty:null, category:null,
 options:[{id:'a',option_order:0,option_text:'A'},{id:'b',option_order:1,option_text:'B'}] }
const row = () => ({ is_correct:false, correct_option_id:'b', explanation:'saved', total_answers:10, correct_answers:4, correct_rate:40 })
const parse = (value, selected='a', detail=null) => data.parseQuizAnswer(question,selected,value,detail)
test('false remains false, valid statistics and saved explanation are preserved',()=>{
 const result=parse(row()); assert.equal(result.is_correct,false); assert.equal(result.correct_rate,40); assert.equal(result.explanation,'saved')
})
for(const [name,changes] of [
 ['string false',{is_correct:'false'}],['numeric correctness',{is_correct:0}],
 ['foreign correct option',{correct_option_id:'foreign'}],['contradictory correctness',{is_correct:true}],
 ['negative count',{total_answers:-1}],['fractional count',{total_answers:10.5}],
 ['correct count exceeds total',{correct_answers:11}],['nonfinite rate',{correct_rate:NaN}],
 ['out of range rate',{correct_rate:101}],['array result',null]
]) test('reject malformed saved answer: '+name,()=>assert.throws(()=>parse(changes===null?[]:{...row(),...changes})))
test('selected option must belong to this question',()=>assert.throws(()=>parse(row(),'foreign')))
test('null low-sample rate is retained, malformed optional explanation cannot replace saved result',()=>{
 const result=parse({...row(),total_answers:2,correct_answers:1,correct_rate:null},'a',{explanation:{bad:true},rules:[{rule_number:'unsafe',title_ja:{}}]})
 assert.equal(result.correct_rate,null); assert.equal(result.explanation,'saved'); assert.deepEqual(result.rules,[])
})
test('valid detail references are used without changing authoritative correctness',()=>{
 const result=parse(row(),'a',{is_correct:true, explanation:'detail',rules:[{rule_number:1,title_ja:'synthetic'}]})
 assert.equal(result.is_correct,false);assert.equal(result.explanation,'detail');assert.deepEqual(result.rules,[{rule_number:1,title_ja:'synthetic'}])
})
