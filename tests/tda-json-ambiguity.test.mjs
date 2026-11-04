import test from 'node:test'
import assert from 'node:assert/strict'
import {createHash} from 'node:crypto'
import {runQuizSnapshotAudit} from '../scripts/tda-snapshot-audit.mjs'
const hash=b=>createHash('sha256').update(b).digest('hex')
const encode=v=>Buffer.from(JSON.stringify(v))
const question={question_id:'q',question_text:'Synthetic PRIVATE_SENTINEL',difficulty:null,category:null,options:['A','B','C','D'].map((id,i)=>({id,option_text:id,option_order:i+1}))}
const key={question_id:'q',correct_option_id:'A',explanation:'Synthetic',rule_numbers:[1]}
function execute({q=encode([question]),k=encode([key]),manifest,extra}={}){
 const ledger={version:1,question_sha256:hash(q),answer_key_sha256:hash(k),expected_question_count:1,expected_option_count:4}
 const m=manifest?Buffer.from(manifest(JSON.stringify(ledger))):extra?Buffer.from(JSON.stringify(ledger).slice(0,-1)+','+extra+'}'):encode(ledger)
 const lines=[];const errors=[];const files={q,k,m};const code=runQuizSnapshotAudit(['q','k','m'],{readFile:path=>files[path],stdout:x=>lines.push(x),stderr:x=>errors.push(x)})
 return {code,report:JSON.parse(lines[0]||errors[0])}
}
function refused(result,reason){assert.equal(result.code,1);assert.equal(result.report.reason,reason);assert.equal(result.report.publication_approved,false);assert.doesNotMatch(JSON.stringify(result.report),/PRIVATE_SENTINEL|duplicate.*field|Unexpected/)}
for(const [name,transform]of[
 ['version',raw=>raw.replace('"version":1','"version":2,"version":1')],
 ['question hash',raw=>raw.replace('"question_sha256":','"question_sha256":"'+'0'.repeat(64)+'","question_sha256":')],
 ['expected count',raw=>raw.replace('"expected_question_count":1','"expected_question_count":350,"expected_question_count":1')],
 ['escaped alias',raw=>raw.replace('"version":1','"ver\\u0073ion":2,"version":1')]
])test(`manifest duplicate ${name} is ambiguous even when last value is valid`,()=>refused(execute({manifest:transform}),'INVALID_MANIFEST'))
for(const [name,field,raw]of[
 ['question text','q',JSON.stringify([question]).replace('"question_text":','"question_text":"Conflicting","question_text":')],
 ['question id','q',JSON.stringify([question]).replace('"question_id":"q"','"question_id":"orphan","question_id":"q"')],
 ['nested option id','q',JSON.stringify([question]).replace('"id":"A"','"id":"WRONG","id":"A"')],
 ['correct answer','k',JSON.stringify([key]).replace('"correct_option_id":"A"','"correct_option_id":"B","correct_option_id":"A"')],
 ['explanation','k',JSON.stringify([key]).replace('"explanation":"Synthetic"','"explanation":"","explanation":"Synthetic"')],
 ['references','k',JSON.stringify([key]).replace('"rule_numbers":[1]','"rule_numbers":[],"rule_numbers":[1]')]
])test(`hash-matched source duplicate ${name} is rejected`,()=>refused(execute({[field]:Buffer.from(raw)}),'INVALID_SOURCE_JSON'))
for(const value of['1e999','-1e999'])test(`nonfinite exponent ${value} in manifest is rejected`,()=>refused(execute({extra:'"metadata":'+value}),'INVALID_MANIFEST'))
test('nonfinite exponent in hash-matched source is rejected',()=>refused(execute({q:Buffer.from(JSON.stringify([question]).replace('"difficulty":null','"difficulty":null,"metadata":1e999'))}),'INVALID_SOURCE_JSON'))
test('depth outside the explicit bounded JSON contract is rejected',()=>refused(execute({extra:'"metadata":'+'['.repeat(130)+'0'+']'.repeat(130)}),'INVALID_MANIFEST'))
test('same member names in distinct nested objects are valid',()=>{const r=execute({extra:'"metadata":{"first":{"id":"a"},"second":{"id":"b"}}'});assert.equal(r.code,0);assert.equal(r.report.official_rule_accuracy,'UNVERIFIED')})
test('escaped quotes braces and numeric-looking strings remain ordinary text',()=>{const q=encode([{...question,question_text:'Literal \\" } , " 1e999 PRIVATE_SENTINEL'}]);const r=execute({q});assert.equal(r.code,0);assert.equal(r.report.publication_approved,false)})
