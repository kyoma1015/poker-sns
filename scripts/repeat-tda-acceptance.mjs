// Finite same-input stability sample. No retries, deadline changes or DB access.
import assert from 'node:assert/strict'
import {spawnSync,execFileSync} from 'node:child_process'
import {readFileSync,writeFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
const suites=[
 {path:'tests/tda-quiz-data.test.mjs',methods:28,browser_cases:4},
 {path:'tests/tda-next-navigation.test.mjs',methods:1,browser_cases:3},
]
const manifest=JSON.parse(readFileSync('docs/qa/selected-abd-20261026/source-manifest.json','utf8'))
const hash=bytes=>createHash('sha1').update(Buffer.from('blob '+bytes.length)).update(Buffer.from([0])).update(bytes).digest('hex')
const frozen=suites.map(s=>{
 const recorded=(manifest.additions||[]).find(r=>r.path===s.path)||(manifest.overrides||[]).find(r=>r.path===s.path)||manifest.sources.find(r=>r.target_path===s.path)
 assert(recorded,'reviewed acceptance required: '+s.path)
 const expected=recorded.sha||recorded.source_blob
 assert.equal(hash(readFileSync(s.path)),expected,'acceptance must retain reviewed bytes')
 return {...s,blob:expected}
})
const results=[],started_at=new Date().toISOString()
let failed=false
outer:for(let iteration=1;iteration<=3;iteration++){
 for(const suite of frozen){
  const started=performance.now()
  const r=spawnSync(process.execPath,[suite.path],{encoding:'utf8',timeout:60000,maxBuffer:4*1024*1024})
  const output=(r.stdout||'')+(r.stderr||'')
  // Emit underlying test logs, never hide a failed trial behind another trial.
  process.stdout.write(output)
  const counts=[...output.matchAll(/ℹ tests ([0-9]+)/g)].map(m=>Number(m[1]))
  const passCounts=[...output.matchAll(/ℹ pass ([0-9]+)/g)].map(m=>Number(m[1]))
  const failCounts=[...output.matchAll(/ℹ fail ([0-9]+)/g)].map(m=>Number(m[1]))
  const ok=!r.error&&r.status===0&&counts.at(-1)===suite.methods&&passCounts.at(-1)===suite.methods&&failCounts.at(-1)===0
  results.push({iteration,suite:suite.path,blob:suite.blob,elapsed_ms:Math.round(performance.now()-started),methods:suite.methods,browser_cases:suite.browser_cases,pass:ok,error:r.error?.code||null,exit_code:r.status,signal:r.signal})
  if(!ok){failed=true;break outer}
 }
}
const report={version:1,head:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),started_at,completed_at:new Date().toISOString(),planned_iterations:3,completed_trials:results.length,distinct_browser_cases:7,planned_browser_case_executions:21,results,verdict:failed?'FAIL':'PASS',limitations:'Synthetic transport only; three consecutive samples cannot prove absence of flakiness or official TDA correctness. Original 25s filter and 40s next deadlines unchanged.'}
if(process.env.TDA_STABILITY_REPORT)writeFileSync(process.env.TDA_STABILITY_REPORT,JSON.stringify(report,null,2)+'\n')
console.log(JSON.stringify(report))
if(failed)process.exitCode=1
