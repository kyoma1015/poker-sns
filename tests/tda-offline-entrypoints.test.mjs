import test from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,writeFileSync,rmSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
import {spawnSync} from 'node:child_process'
import {createHash} from 'node:crypto'
const hash=bytes=>createHash('sha256').update(bytes).digest('hex')
const q=JSON.stringify([{question_id:'q',question_text:'PRIVATE_SENTINEL',difficulty:null,category:null,options:['A','B','C','D'].map((id,i)=>({id,option_text:id,option_order:i+1}))}])
const keys=Buffer.from(JSON.stringify([{question_id:'q',correct_option_id:'A',explanation:'Synthetic',rule_numbers:[1]}]))
const badUtf8=Buffer.from(q.replace('PRIVATE_SENTINEL','X'));badUtf8[badUtf8.indexOf(Buffer.from('X'))]=0xff
for(const entry of ['legacy','snapshot'])for(const [name,bytes,expected]of[
 ['normal bytes',Buffer.from(q),0],
 ['duplicate member',Buffer.from(q.replace('"question_id":"q"','"question_id":"conflict","question_id":"q"')),1],
 ['invalid UTF8 inside JSON string',badUtf8,1],
 ['empty file',Buffer.alloc(0),1],
])test(`real ${entry} entrypoint ${name}`,()=>{
 const directory=mkdtempSync(join(tmpdir(),'poker-tda-cli-'))
 try{
  const question=join(directory,'questions.json'),key=join(directory,'keys.json'),manifest=join(directory,'manifest.json')
  writeFileSync(question,bytes);writeFileSync(key,keys);writeFileSync(manifest,JSON.stringify({version:1,question_sha256:hash(bytes),answer_key_sha256:hash(keys),expected_question_count:1,expected_option_count:4}))
  const args=entry==='legacy'?['scripts/audit-tda-questions.mjs',question,'1']:['scripts/tda-snapshot-audit.mjs',question,key,manifest]
  const child=spawnSync(process.execPath,args,{encoding:'utf8',timeout:10000,maxBuffer:1024*1024})
  assert.equal(child.error,undefined);assert.equal(child.signal,null);assert.equal(child.status,expected)
  const report=JSON.parse(expected===0?child.stdout:child.stderr)
  assert.equal(report.official_rule_accuracy,'UNVERIFIED');assert.equal(report.publication_approved,false)
  assert.equal(expected===0?child.stderr:child.stdout,'')
  assert.doesNotMatch(child.stdout+child.stderr,/PRIVATE_SENTINEL|conflict|SyntaxError|TypeError/)
  assert.equal((child.stdout+child.stderr).includes(directory),false)
  if(expected)assert.equal(report.reason,entry==='legacy'?'INVALID_JSON':'INVALID_SOURCE_JSON')
 }finally{rmSync(directory,{recursive:true,force:true})}
})
