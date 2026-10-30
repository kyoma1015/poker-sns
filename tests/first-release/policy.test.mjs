import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { FIRST_RELEASE_ENABLED,firstReleaseRoute,firstReleaseVerdict,REQUIRED_RELEASE_GATES } from '../../src/firstReleasePolicy.ts'
const doc=JSON.parse(readFileSync('docs/progress/FIRST_RELEASE_V1.json','utf8'))
test('all mandatory safety gates exist, uniquely, without touching the32 ledger',()=>{
 assert.equal(doc.gates.length,12);assert.equal(new Set(doc.gates.map(g=>g.id)).size,12)
 assert.equal(doc.legacy_ledger.product_rows,32);assert.equal(doc.legacy_ledger.immutable,true)
 assert.equal(firstReleaseVerdict(doc).ready,false);assert.equal(FIRST_RELEASE_ENABLED,false)
})
test('candidate route allowlist fails closed for deferred, encoded and unknown URLs',()=>{
 for(const path of ['/tda','/player-type?result=x','/tools','/results','/profile/card','/player/a/card','/profile/results/new','/player/a/rate','/videos','/unknown','/%74da','//tda','/x%2f..%2ftda','/%00','/%ZZ'])assert.equal(firstReleaseRoute(path),null,path)
 for(const path of ['/','/login','/signup','/timeline','/post/a','/dm/a','/profile/edit','/player/a/followers','/search?q=x'])assert.notEqual(firstReleaseRoute(path),null,path)
})
test('absent, duplicate, unknown or incomplete evidence never authorizes release',()=>{
 for(const value of [null,{}, {gates:[]},{gates:[...doc.gates,doc.gates[0]]},{gates:doc.gates.map(g=>({...g,status:'PASS',evidence:[]}))},{gates:doc.gates.map(g=>({...g,id:'unknown',status:'PASS',evidence:['fixture']}))}])assert.equal(firstReleaseVerdict(value).ready,false)
 const fixture={gates:REQUIRED_RELEASE_GATES.map(id=>({id,status:'PASS',evidence:['synthetic policy-unit receipt; NOT actual safety proof']}))}
 assert.equal(firstReleaseVerdict(fixture).ready,true)
 assert.equal(FIRST_RELEASE_ENABLED,false,'synthetic receipt does not enable runtime')
})
test('canonical release build stops before build when safety gates are incomplete',()=>{
 const r=spawnSync(process.execPath,['scripts/build-first-release.mjs'],{encoding:'utf8',timeout:10000})
 assert.equal(r.status,2,r.stderr);assert.match(r.stdout,/"verdict": "NO-GO"/)
 assert.doesNotMatch(r.stdout,/building client|modules transformed/)
})
test('raw legacy ledger blob remains identical to pinned pre-mode source',()=>{
 const r=spawnSync(process.execPath,['scripts/first-release-gate.mjs'],{encoding:'utf8',timeout:10000})
 assert.equal(r.status,0,r.stderr)
 const report=JSON.parse(r.stdout);assert.equal(report.legacy_ledger_preserved,true);assert.equal(report.legacy_product_rows,32)
})
