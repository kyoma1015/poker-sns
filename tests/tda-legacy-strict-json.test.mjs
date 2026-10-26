import test from 'node:test'
import assert from 'node:assert/strict'
import {runQuizAuditCli} from '../scripts/tda-audit-cli.mjs'
const question={question_id:'q',question_text:'PRIVATE_SENTINEL',difficulty:null,category:null,options:[{id:'a',option_order:1,option_text:'A'},{id:'b',option_order:2,option_text:'B'}]}
const raw=JSON.stringify([question])
function execute(input){const output=[];const code=runQuizAuditCli(['synthetic.json','1'],{readFile:()=>input,stdout:x=>output.push(x),stderr:x=>output.push(x)});return{code,report:JSON.parse(output[0])}}
for(const [name,input]of[
 ['duplicate question text',raw.replace('"question_text":','"question_text":"Conflicting","question_text":')],
 ['escaped duplicate question id',raw.replace('"question_id":"q"','"question_\\u0069d":"orphan","question_id":"q"')],
 ['duplicate option id',raw.replace('"id":"a"','"id":"WRONG","id":"a"')],
 ['nonfinite ignored metadata',raw.replace('"difficulty":null','"difficulty":null,"metadata":1e999')],
 ['excess depth metadata',raw.replace('"difficulty":null','"difficulty":null,"metadata":'+'['.repeat(130)+'0'+']'.repeat(130))],
 ['invalid UTF8 inside string',Buffer.concat([Buffer.from(raw.split('PRIVATE_SENTINEL')[0]),Buffer.from([0xff]),Buffer.from(raw.split('PRIVATE_SENTINEL')[1])])],
])test(`legacy CLI fails closed for ${name}`,()=>{const result=execute(input);assert.equal(result.code,1);assert.deepEqual(result.report,{verdict:'FAIL',reason:'INVALID_JSON',official_rule_accuracy:'UNVERIFIED',publication_approved:false});assert.doesNotMatch(JSON.stringify(result.report),/PRIVATE_SENTINEL|Conflicting|Unexpected/)})
for(const input of[raw,Buffer.from(raw)])test(`legacy CLI accepts valid ${typeof input} transport without publication approval`,()=>{const r=execute(input);assert.equal(r.code,0);assert.equal(r.report.official_rule_accuracy,'UNVERIFIED');assert.equal(r.report.publication_approved,false)})
