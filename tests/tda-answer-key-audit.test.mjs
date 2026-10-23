import test from 'node:test'
import assert from 'node:assert/strict'
let audit
try { ({ auditQuizAnswerKey: audit } = await import('../src/tdaQuizAnswerAudit.ts')) }
catch (error) { if (error.code !== 'ERR_MODULE_NOT_FOUND') throw error }
const question = (id='q1') => ({question_id:id,question_text:`判断 ${id}`,difficulty:null,category:'TDA',options:[
  {id:`${id}-b`,option_order:2,option_text:'B'}, {id:`${id}-a`,option_order:1,option_text:'A'},
  {id:`${id}-d`,option_order:4,option_text:'D'}, {id:`${id}-c`,option_order:3,option_text:'C'}]})
const key = (id='q1') => ({question_id:id,correct_option_id:`${id}-b`,explanation:'Synthetic explanation',rule_numbers:[1,2]})
function run(q=[question()], k=[key()]) { assert.equal(typeof audit,'function','offline answer-key audit is required'); return audit(q,k) }
test('valid offline export reports counts and 1-based displayed answer position without mutating input',()=>{
 const q=[question()],k=[key()],before=JSON.stringify([q,k]); const r=run(q,k)
 assert.equal(r.verdict,'STRUCTURE_PASS');assert.equal(r.question_count,1);assert.equal(r.option_count,4)
 assert.deepEqual(r.answer_position_counts,{'2':1});assert.deepEqual(r.issues,[]);assert.equal(JSON.stringify([q,k]),before)
 assert.equal(r.official_rule_accuracy,'UNVERIFIED');assert.equal(r.publication_approved,false)
})
test('missing answer row remains review required',()=>{assert.deepEqual(run([question()],[]).issues,[{code:'MISSING_ANSWER_KEY',question_id:'q1'}])})
test('duplicate answer rows do not select one answer silently',()=>{const r=run([question()],[key(),{...key(),correct_option_id:'q1-a'}]);assert.equal(r.verdict,'REVIEW_REQUIRED');assert.ok(r.issues.some(x=>x.code==='DUPLICATE_ANSWER_KEY'));assert.deepEqual(r.answer_position_counts,{})})
test('orphan answer row is identified',()=>{assert.ok(run([question()],[key(),key('orphan')]).issues.some(x=>x.code==='ORPHAN_ANSWER_KEY'))})
test('answer outside question options is rejected',()=>{assert.ok(run([question()],[{...key(),correct_option_id:'unknown'}]).issues.some(x=>x.code==='INVALID_CORRECT_OPTION'))})
for(const value of ['',null,42]) test(`missing or invalid explanation (${value}) needs review`,()=>{assert.ok(run([question()],[{...key(),explanation:value}]).issues.some(x=>x.code==='INVALID_EXPLANATION'))})
for(const value of [[],[0],[true],[1.5],[1,1],null]) test(`invalid rule references ${JSON.stringify(value)} need review`,()=>{assert.ok(run([question()],[{...key(),rule_numbers:value}]).issues.some(x=>x.code==='INVALID_RULE_REFERENCES'))})
test('non-four-choice question is reported rather than counted as 1400',()=>{const q=question();q.options.pop();assert.ok(run([q]).issues.some(x=>x.code==='OPTION_COUNT_NOT_FOUR'))})
test('empty corpus never passes',()=>{assert.equal(run([],[]).verdict,'REVIEW_REQUIRED')})
test('malformed and sparse key rows fail closed without echoing payload',()=>{for(const value of [null,{},[null],Array(1),[{private:'SENSITIVE_SENTINEL'}]]){assert.throws(()=>run([question()],value),error=>!String(error).includes('SENSITIVE_SENTINEL'))}})
test('malformed and sparse questions retain established parser rejection',()=>{assert.throws(()=>run(Array(1),[]))})
test('balanced synthetic answers expose all four positions without a quality approval',()=>{const q=['q1','q2','q3','q4'].map(question);const k=q.map((x,i)=>({...key(x.question_id),correct_option_id:`${x.question_id}-${'abcd'[i]}`}));const r=run(q,k);assert.deepEqual(r.answer_position_counts,{'1':1,'2':1,'3':1,'4':1});assert.equal(r.publication_approved,false)})
