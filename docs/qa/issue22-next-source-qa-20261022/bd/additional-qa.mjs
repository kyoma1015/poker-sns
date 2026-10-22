import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { parseQuizQuestions, normalizeQuizFilters, quizAuditReport, safeQuizRpc } from '/workspace/work/issue22-filter-values-worktrees/issue22-b-filter-values-v1/src/tdaQuizData.ts'
import { auditPlayerType } from '/workspace/work/issue22-d-main-worktrees/candidate/scripts/audit-player-type.mjs'
const droot='/workspace/work/issue22-d-main-worktrees/candidate'
const fixture=JSON.parse(readFileSync(droot+'/tests/fixtures/player-type-v2.json','utf8'))
const assets=readdirSync(droot+'/public/animals').filter(x=>x.endsWith('.png')).map(x=>x.slice(0,-4))
function freeze(x){if(x&&typeof x==='object'){for(const v of Object.values(x))freeze(v);Object.freeze(x)}return x}
const question=()=>({question_id:'q1',question_text:'正しい判断',difficulty:null,category:null,options:[{id:'a',option_order:2,option_text:'A'},{id:'b',option_order:1,option_text:'B'}]})
test('B frozen unsorted input stays immutable while parser returns sorted copies',()=>{
 const input=freeze([question()]);const before=JSON.stringify(input);const result=parseQuizQuestions(input)
 assert.deepEqual(result[0].options.map(x=>x.id),['b','a']);assert.equal(JSON.stringify(input),before);assert.notEqual(result[0].options,input[0].options)
})
test('B frozen mixed sparse optional filters produce dense string-only copies',()=>{
 const sparse=Object.assign(Array(8),{0:'A',2:null,3:false,4:'',5:NaN,6:'A',7:{bad:1}})
 const input=freeze({difficulties:sparse,categories:['TDA',undefined,7]});const before=JSON.stringify(input);const result=normalizeQuizFilters(input)
 assert.deepEqual(result,{difficulties:['A','','A'],categories:['TDA']});assert.notEqual(result.difficulties,sparse);assert.equal(JSON.stringify(input),before)
})
test('B normalized duplicate candidates never grant official accuracy/publication',()=>{
 const a=question();a.question_text='Ａ　Ｂ';const b={...question(),question_id:'q2',question_text:'a b'};const input=freeze([a,b]);const result=quizAuditReport(input,2)
 assert.deepEqual(result.duplicateQuestionCandidates,[['q1','q2']]);assert.equal(result.verdict,'REVIEW_REQUIRED');assert.equal(result.publication_approved,false);assert.equal(result.official_rule_accuracy,'UNVERIFIED')
})
test('B transport rejection executes once and preserves later successful result identity',async()=>{
 let count=0;const result=await safeQuizRpc(()=>{count++;throw new Error('synthetic transport')});assert.equal(count,1);assert.equal(result.data,null);assert.equal(typeof result.error.message,'string')
 const response=freeze({data:[{is_correct:false}],error:null});assert.equal(await safeQuizRpc(()=>Promise.resolve(response)),response)
})
test('D deeply frozen historical fixture remains unchanged and semantically UNKNOWN',()=>{
 const input=freeze(structuredClone(fixture));const before=JSON.stringify(input);const result=auditPlayerType(input,freeze([...assets]))
 assert.equal(result.status,'CONDITIONAL PASS');assert.equal(result.questions,50);assert.equal(result.animalDisplayKeys,36);assert.match(result.classificationSemanticValidity,/^UNKNOWN:/);assert.equal(JSON.stringify(input),before)
})
test('D all 50 persona positions reject a foreign answer without mutation',()=>{
 for(let i=0;i<50;i++){const input=structuredClone(fixture);input.personas[0].answers[i]='Z';freeze(input);const before=JSON.stringify(input);const result=auditPlayerType(input,assets)
 assert.equal(result.status,'FAIL');assert.ok(result.errors.some(x=>x.code==='INVALID_PERSONA_CHOICE'&&x.persona===0&&x.question===i+1));assert.equal(JSON.stringify(input),before)}
})
test('D each nonfinite score remains a structural failure',()=>{
 for(const value of [NaN,Infinity,-Infinity]){const input=structuredClone(fixture);input.scores[0].initiative=value;freeze(input);const result=auditPlayerType(input,assets);assert.equal(result.status,'FAIL');assert.ok(result.errors.some(x=>x.code==='NONFINITE_SCORE'&&x.key==='initiative'))}
})
test('D every missing configured animal asset is rejected',()=>{
 for(const asset of assets){const result=auditPlayerType(fixture,assets.filter(x=>x!==asset));assert.equal(result.status,'FAIL');assert.ok(result.errors.some(x=>x.code==='ANIMAL_ASSET_MISMATCH'&&x.key===asset))}
})
