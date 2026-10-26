import test from 'node:test'
import assert from 'node:assert/strict'
import {parseUnambiguousJSON as parse} from '../scripts/strict-json.mjs'
import {runQuizSnapshotAudit} from '../scripts/tda-snapshot-audit.mjs'
const bytes=s=>Buffer.from(s)
for(const [name,raw] of [
 ['prototype','{"__proto__":1,"__proto__":2}'],
 ['unicode surrogate alias','{"\\ud83d\\ude00":1,"😀":2}'],
 ['empty key','{"":1,"":2}'],
 ['backslash alias','{"a\\\\b":1,"a\\u005cb":2}'],
]) test(`strict decoder refuses duplicate ${name}`,()=>assert.throws(()=>parse(bytes(raw)),/AMBIGUOUS_JSON_OBJECT/))
for(const depth of [127,128])test(`depth ${depth} is accepted`,()=>assert.deepEqual(parse(bytes('['.repeat(depth)+'0'+']'.repeat(depth))),JSON.parse('['.repeat(depth)+'0'+']'.repeat(depth))))
test('depth 129 is refused at the boundary',()=>assert.throws(()=>parse(bytes('['.repeat(129)+'0'+']'.repeat(129))),/JSON_DEPTH_LIMIT/))
for(const raw of [Buffer.from([0xc0,0xaf]),Buffer.from([0xed,0xa0,0x80]),Buffer.from([0xe2,0x82]),Buffer.from([0xf4,0x90,0x80,0x80])])test(`invalid UTF8 ${raw.toString('hex')} is refused`,()=>assert.throws(()=>parse(raw)))
for(const raw of ['{"x":NaN}','{"x":Infinity}','{"x":1,}','[0,]','{"x":"\\q"}','{"x":1} trailing'])test(`invalid JSON grammar is refused: ${raw}`,()=>assert.throws(()=>parse(bytes(raw))))
test('all JSON finite scalar and escaped string forms retain their values',()=>{
 for(const raw of ['-0','5e-324','1.7976931348623157e308','true','false','null','"\\b\\f\\n\\r\\t\\/\\\\\\\""','"日本語 😀 \\ud800"'])assert.deepEqual(parse(bytes(raw)),JSON.parse(raw))
})
test('10000 fixed-seed valid finite JSON values match JSON.parse without mutation',()=>{
 let state=0x544441;const random=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/2**32}
 const strings=['','日本語 😀','\\"{}[],:','1e999','__proto__','\u0000\n\t','a\\b','é']
 const make=depth=>{const choice=Math.floor(random()*(depth===5?5:7));switch(choice){case 0:return null;case 1:return random()<.5;case 2:return (random()-.5)*1e200;case 3:return strings[Math.floor(random()*strings.length)];case 4:return Math.floor(random()*200)-100;case 5:return Array.from({length:Math.floor(random()*5)},()=>make(depth+1));default:{const out=Object.create(null);for(let n=0;n<Math.floor(random()*5);n++)out['key'+n+strings[Math.floor(random()*strings.length)]]=make(depth+1);return out}}}
 for(let n=0;n<10000;n++){const raw=bytes(JSON.stringify(make(0)));const copy=Buffer.from(raw);assert.deepEqual(parse(raw),JSON.parse(raw.toString()),`case ${n}`);assert.deepEqual(raw,copy)}
})
test('all malformed manifest classes retain generic reasons and nonpublication gates',()=>{
 const malformed=['{"secret":"PRIVATE_SENTINEL","secret":2}','{"value":1e999}','['.repeat(129)+'0'+']'.repeat(129),'{"secret":"PRIVATE_SENTINEL"',Buffer.from([0xff])]
 for(const raw of malformed){const output=[];const code=runQuizSnapshotAudit(['q','k','m'],{readFile:()=>typeof raw==='string'?bytes(raw):raw,stdout:s=>output.push(s),stderr:s=>output.push(s)});assert.equal(code,1);assert.equal(output.length,1);const report=JSON.parse(output[0]);assert.deepEqual(report,{verdict:'FAIL',reason:'INVALID_MANIFEST',official_rule_accuracy:'UNVERIFIED',publication_approved:false});assert.doesNotMatch(output[0],/PRIVATE_SENTINEL|JSON_DEPTH_LIMIT|AMBIGUOUS_JSON_OBJECT|NONFINITE_JSON_NUMBER/)}
})
